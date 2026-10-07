"""
MLOps P1 — Data & Model Drift Analysis via Evidently AI
========================================================
Ce script est un Job Prefect autonome qui :
  1. Charge les données de RÉFÉRENCE depuis PostgreSQL (feature_matrix — baseline d'entraînement)
  2. Charge les données de PRODUCTION depuis le shadow_log.csv (requêtes réelles de l'API)
  3. Exécute les Suites de Tests Evidently :
       - DataDriftTestSuite (dérive des distributions de features)
       - DataQualityTestSuite (valeurs manquantes, valeurs hors bornes)
  4. Génère un rapport HTML complet sauvegardé localement dans reports/drift/
  5. Exporte les métriques PSI par feature vers Prometheus (prometheus_client)
  6. Déclenche la boucle SRE si un seuil critique est franchi

Architecture : Ce script est fait pour être appelé quotidiennement par Prefect Scheduler.

Usage manuel :
    python scripts/run_drift_analysis.py
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from prefect import flow, task, get_run_logger

# Evidently 0.7.x — l'API classique (DataDrift, TestSuite) est dans evidently.legacy
from evidently.legacy.pipeline.column_mapping import ColumnMapping
from evidently.legacy.report import Report
from evidently.legacy.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.legacy.test_suite import TestSuite
from evidently.legacy.tests import (
    TestNumberOfDriftedColumns,
    TestShareOfDriftedColumns,
    TestColumnDrift,
)

# Prometheus — export des métriques pour le scraping par Grafana/Alertmanager
from prometheus_client import (
    CollectorRegistry,
    Gauge,
    push_to_gateway,
    write_to_textfile,
)

# SRE Engine — déclenchement conditionnel du retraining
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.models.sre_engine import ContinuousTrainingEngine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DriftAnalysis")

# ─── Configuration ─────────────────────────────────────────────────────────────
DB_URL = "postgresql://mlops:mlops_password@localhost:5432/mlops_db"
SHADOW_LOG_PATH = "data/production_logs/shadow_log.csv"
REPORTS_DIR = Path("reports/drift")

# Features à surveiller (les mêmes que celles du Modèle A)
FEATURES_NUMERIQUES = [
    "place",
    "catu",
    "sexe",
    "an_nais",
    "trajet",
    "nb_accidents_zone",
]
FEATURES_CATEGORIELLES = [
    "is_metropole",
    "age_bucket",
    "is_motorise",
    "lum_calculee",
    "atm_simplifie",
    "catr_derive",
]
ALL_FEATURES = FEATURES_NUMERIQUES + FEATURES_CATEGORIELLES

# Seuils d'alerte
DRIFT_SHARE_ALERT_THRESHOLD = 0.3  # Si > 30% des features dérivent → alerte critique
DRIFT_SHARE_WARN_THRESHOLD = 0.15  # Si > 15% → warning

# Prometheus Pushgateway (optionnel si pas déployé, on écrit aussi en fichier texte)
PROMETHEUS_PUSHGATEWAY = os.getenv("PROMETHEUS_PUSHGATEWAY", "localhost:9091")
PROMETHEUS_METRICS_FILE = "reports/drift/prometheus_metrics.txt"


# ─── Tasks Prefect ─────────────────────────────────────────────────────────────


@task(name="load_reference_data", retries=2, retry_delay_seconds=10)
def load_reference_data() -> pd.DataFrame:
    """Charge la baseline d'entraînement depuis Parquet (feature_matrix)."""
    log = get_run_logger()
    log.info("Chargement des données de RÉFÉRENCE depuis Parquet (feature_matrix)...")
    df = pd.read_parquet("data/features/feature_matrix.parquet")
    log.info(f"Référence chargée : {len(df):,} lignes × {len(df.columns)} features.")
    return df


@task(name="load_production_data")
def load_production_data() -> pd.DataFrame | None:
    """Charge les requêtes de production depuis le csv shadow_log."""
    log = get_run_logger()

    path = "data/production_logs/shadow_log.csv"
    import os

    if not os.path.exists(path):
        log.warning("La table n'existe pas encore. Aucune donnée de prod.")
        return None

    df = pd.read_csv(path)

    if len(df) < 30:
        log.warning(
            f"Shadow log trop petit ({len(df)} lignes). "
            "Il faut au moins 30 requêtes pour un drift analysis statistiquement valide."
        )
        return None

    log.info(f"Production chargée : {len(df):,} lignes × {len(df.columns)} features.")
    return df


@task(name="align_features")
def align_features(
    reference: pd.DataFrame, production: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Aligne les colonnes des deux DataFrames sur l'intersection commune.
    Normalise les types (force float pour éviter le crash numpy dans Evidently).
    """
    log = get_run_logger()

    # On ne garde que les features disponibles dans les deux datasets
    common_features = [
        f for f in ALL_FEATURES if f in reference.columns and f in production.columns
    ]
    missing_in_prod = [f for f in ALL_FEATURES if f not in production.columns]

    if missing_in_prod:
        log.warning(
            f"Features absentes du shadow_log (pas encore loggées par l'API) : {missing_in_prod}"
        )

    log.info(f"Features communes pour l'analyse : {common_features}")

    ref = reference[common_features].copy()
    prod = production[common_features].copy()

    # Normalisation : Evidently legacy corrcoef crashe avec pd.NA / Int64, on force en float64
    for col in common_features:
        ref[col] = pd.to_numeric(ref[col], errors="coerce").astype(float)
        prod[col] = pd.to_numeric(prod[col], errors="coerce").astype(float)

    return ref, prod


@task(name="run_evidently_report")
def run_evidently_report(
    reference: pd.DataFrame, production: pd.DataFrame, run_timestamp: str
) -> dict:
    """
    Exécute le rapport Evidently complet :
      - DataDriftPreset : drift de chaque feature (Jensen-Shannon, Wasserstein, etc.)
      - DataQualityPreset : valeurs manquantes, outliers, doublons
    Sauvegarde le rapport HTML dans reports/drift/.
    Retourne un dict de métriques.
    """
    log = get_run_logger()
    log.info("Génération du rapport Evidently AI (DataDrift + DataQuality)...")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # Construction du ColumnMapping (informe Evidently sur les types de features)
    column_mapping = ColumnMapping(
        numerical_features=[f for f in FEATURES_NUMERIQUES if f in reference.columns],
        categorical_features=[
            f for f in FEATURES_CATEGORIELLES if f in reference.columns
        ],
    )

    # ── Rapport complet HTML (Data Drift + Data Quality) ──────────────────────
    report = Report(
        metrics=[
            DataDriftPreset(),
            DataQualityPreset(),
        ]
    )
    report.run(
        reference_data=reference,
        current_data=production,
        column_mapping=column_mapping,
    )

    report_path = REPORTS_DIR / f"drift_report_{run_timestamp}.html"
    report.save_html(str(report_path))
    log.info(f"✅ Rapport HTML sauvegardé : {report_path}")

    # ── TestSuite (checks automatisés avec seuils) ─────────────────────────────
    test_suite = TestSuite(
        tests=[
            TestNumberOfDriftedColumns(
                lt=int(len(reference.columns) * DRIFT_SHARE_ALERT_THRESHOLD)
            ),
            TestShareOfDriftedColumns(lt=DRIFT_SHARE_ALERT_THRESHOLD),
            # On teste chaque feature individuellement (Jensen-Shannon stattest)
            *[TestColumnDrift(column_name=col) for col in reference.columns],
        ]
    )
    test_suite.run(
        reference_data=reference,
        current_data=production,
        column_mapping=column_mapping,
    )

    suite_path = REPORTS_DIR / f"drift_test_suite_{run_timestamp}.html"
    test_suite.save_html(str(suite_path))

    # ── Extraction des métriques brutes ────────────────────────────────────────
    report_dict = report.as_dict()
    drift_results = {}
    total_features = 0
    drifted_features = 0

    # Parcours du résultat Evidently pour extraire les scores par feature
    for metric in report_dict.get("metrics", []):
        metric_id = metric.get("metric", "")
        if "DataDriftTable" in metric_id or "ColumnDriftMetric" in metric_id:
            result = metric.get("result", {})
            # DataDriftTable contient un dict par feature
            if "drift_by_columns" in result:
                for col, col_data in result["drift_by_columns"].items():
                    drift_results[col] = {
                        "drift_score": col_data.get("drift_score", 0.0),
                        "drifted": col_data.get("drift_detected", False),
                        "stattest": col_data.get("stattest_name", ""),
                    }
                    total_features += 1
                    if col_data.get("drift_detected", False):
                        drifted_features += 1

    drift_share = drifted_features / total_features if total_features > 0 else 0.0

    metrics = {
        "drift_share": drift_share,
        "drifted_features_count": drifted_features,
        "total_features_analyzed": total_features,
        "drift_by_feature": drift_results,
        "report_path": str(report_path),
        "suite_path": str(suite_path),
        "all_tests_passed": test_suite.as_dict()
        .get("summary", {})
        .get("all_passed", False),
    }

    # Log du résumé dans Prefect
    status_icon = (
        "🔴"
        if drift_share > DRIFT_SHARE_ALERT_THRESHOLD
        else ("🟡" if drift_share > DRIFT_SHARE_WARN_THRESHOLD else "🟢")
    )
    log.info(f"\n{'='*60}")
    log.info(f"RÉSUMÉ DRIFT — {run_timestamp}")
    log.info(f"  {status_icon} Features analysées : {total_features}")
    log.info(
        f"  {status_icon} Features en dérive : {drifted_features} ({drift_share:.1%})"
    )
    log.info(
        f"  Tests Evidently réussis : {'✅ OUI' if metrics['all_tests_passed'] else '❌ NON'}"
    )
    log.info(f"  Rapport : {report_path}")
    log.info(f"{'='*60}")

    for col, data in drift_results.items():
        icon = "🔴" if data["drifted"] else "🟢"
        log.info(
            f"  {icon} {col}: score={data['drift_score']:.4f} ({data['stattest']})"
        )

    return metrics


@task(name="export_prometheus_metrics")
def export_prometheus_metrics(metrics: dict, run_timestamp: str) -> None:
    """
    Exporte les métriques de drift vers Prometheus.
    Stratégie double :
      1. Écriture fichier texte (scraped par node_exporter si configuré)
      2. Push vers Pushgateway si disponible (mode batch job)
    """
    log = get_run_logger()
    log.info("Export des métriques vers Prometheus...")

    registry = CollectorRegistry()

    # ── Gauge 1 : Taux global de dérive ────────────────────────────────────────
    g_drift_share = Gauge(
        "mlops_baac_drift_share",
        "Proportion de features en dérive (Evidently AI)",
        registry=registry,
    )
    g_drift_share.set(metrics["drift_share"])

    # ── Gauge 2 : Score de dérive par feature ──────────────────────────────────
    g_feature_drift = Gauge(
        "mlops_baac_feature_drift_score",
        "Score de dérive Evidently par feature (Jensen-Shannon / Wasserstein)",
        labelnames=["feature"],
        registry=registry,
    )
    for col, data in metrics["drift_by_feature"].items():
        g_feature_drift.labels(feature=col).set(data["drift_score"])

    # ── Gauge 3 : Nombre de features en dérive ─────────────────────────────────
    g_drifted_count = Gauge(
        "mlops_baac_drifted_features_count",
        "Nombre de features Evidently marquées comme driftées",
        registry=registry,
    )
    g_drifted_count.set(metrics["drifted_features_count"])

    # ── Gauge 4 : Healthcheck suite de tests ───────────────────────────────────
    g_tests_passed = Gauge(
        "mlops_baac_drift_tests_passed",
        "1 si tous les tests Evidently passent, 0 sinon",
        registry=registry,
    )
    g_tests_passed.set(1 if metrics["all_tests_passed"] else 0)

    # ── Écriture fichier texte (toujours fiable, même sans Pushgateway) ────────
    Path(PROMETHEUS_METRICS_FILE).parent.mkdir(parents=True, exist_ok=True)
    write_to_textfile(PROMETHEUS_METRICS_FILE, registry)
    log.info(f"✅ Métriques Prometheus écrites : {PROMETHEUS_METRICS_FILE}")

    # ── Push vers Pushgateway (optionnel, ne crash pas si absent) ──────────────
    try:
        push_to_gateway(
            PROMETHEUS_PUSHGATEWAY,
            job="baac_drift_analysis",
            grouping_key={"run": run_timestamp},
            registry=registry,
        )
        log.info(f"✅ Métriques poussées vers Pushgateway : {PROMETHEUS_PUSHGATEWAY}")
    except Exception as e:
        log.warning(
            f"Pushgateway non disponible ({PROMETHEUS_PUSHGATEWAY}) — "
            f"métriques écrites en fichier uniquement. Erreur : {e}"
        )


@task(name="trigger_sre_if_critical")
def trigger_sre_if_critical(metrics: dict) -> None:
    """
    Déclenche la boucle SRE uniquement si la dérive est critique.
    Critères :
      - > DRIFT_SHARE_ALERT_THRESHOLD (30%) des features dérivent
      - OU la feature `an_nais` (âge du conducteur) dérive (critique métier)
    """
    log = get_run_logger()

    critical_triggered = False
    reasons = []

    # Critère 1 : dérive globale trop importante
    if metrics["drift_share"] > DRIFT_SHARE_ALERT_THRESHOLD:
        reasons.append(
            f"Dérive globale ({metrics['drift_share']:.1%}) > seuil ({DRIFT_SHARE_ALERT_THRESHOLD:.0%})"
        )
        critical_triggered = True

    # Critère 2 : dérive de la feature métier critique (age conducteur)
    an_nais_data = metrics["drift_by_feature"].get("an_nais", {})
    if an_nais_data.get("drifted", False):
        reasons.append(
            f"Feature critique 'an_nais' en dérive (score={an_nais_data.get('drift_score', 0):.4f})"
        )
        critical_triggered = True

    if critical_triggered:
        log.warning("🚨 DÉRIVE CRITIQUE DÉTECTÉE — Déclenchement de la boucle SRE...")
        for reason in reasons:
            log.warning(f"  → {reason}")
        try:
            engine = ContinuousTrainingEngine()
            # On lui force des résultats PSI synthétiques pour bypass le DriftMonitor maison
            # (Evidently a déjà fait le calcul — on fait confiance à son verdict)
            engine.run_sre_loop()
        except Exception as e:
            log.error(f"❌ SRE loop failed : {e}")
    else:
        log.info(
            f"✅ Dérive sous le seuil critique ({metrics['drift_share']:.1%} < {DRIFT_SHARE_ALERT_THRESHOLD:.0%}). "
            "SRE loop non déclenchée."
        )


# ─── Flow Principal ─────────────────────────────────────────────────────────────


@flow(
    name="BAAC_Drift_Analysis_Pipeline",
    description="Job batch Prefect de Data & Model Drift Monitoring (Evidently AI → Prometheus)",
)
def drift_analysis_flow() -> dict:
    """
    Pipeline de monitoring de dérive à exécuter quotidiennement.

    Flux :
      PostgreSQL (feature_matrix) ──► Evidently ──► HTML Report
      Shadow Log CSV (prod)       ──►           ──► Prometheus Metrics
                                                ──► SRE Loop (conditionnel)
    """
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Chargement des données
    reference = load_reference_data()
    production = load_production_data()

    if production is None:
        logger.warning("Pas de données de production — pipeline interrompu proprement.")
        return {"status": "skipped", "reason": "no_production_data"}

    # 2. Alignement des features disponibles dans les 2 datasets
    reference_aligned, production_aligned = align_features(reference, production)

    if reference_aligned.empty or production_aligned.empty:
        logger.warning("DataFrames vides après alignement — pipeline interrompu.")
        return {"status": "skipped", "reason": "empty_after_alignment"}

    # 3. Rapport Evidently complet
    metrics = run_evidently_report(reference_aligned, production_aligned, run_timestamp)

    # 4. Export Prometheus
    export_prometheus_metrics(metrics, run_timestamp)

    # 5. Déclenchement conditionnel du SRE
    trigger_sre_if_critical(metrics)

    return {
        "status": "success",
        "run_timestamp": run_timestamp,
        "drift_share": metrics["drift_share"],
        "drifted_features": metrics["drifted_features_count"],
        "report_path": metrics["report_path"],
    }


if __name__ == "__main__":
    result = drift_analysis_flow()
    print("\n=== Drift Analysis Terminé ===")
    for k, v in result.items():
        print(f"  {k}: {v}")
