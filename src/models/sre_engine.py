"""
MLOps Phase 7: SRE Policy Engine
Orchestrateur autonome de Continuous Training.
Boucle fermée : Monitor -> Alerte -> Retrain -> Register.

Thresholds PSI (standard industriel) :
  PSI < 0.1  → No drift (stable)
  PSI 0.1-0.2 → Moderate drift (warning)
  PSI > 0.2  → Significant drift (trigger retraining)
"""

import logging
import subprocess
import sys
import os
from src.models.drift_monitor import DriftMonitor

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SRE_Engine")

# Seuil PSI au-dessus duquel on considère qu'il y a une dérive significative
PSI_THRESHOLD = 0.2

# Features critiques à surveiller pour déclencher le retraining
CRITICAL_FEATURES = ["an_nais", "is_motorise", "catu", "sexe", "trajet"]


class ContinuousTrainingEngine:
    def __init__(self, psi_threshold: float = PSI_THRESHOLD):
        self.monitor = DriftMonitor()
        self.psi_threshold = psi_threshold

    def run_sre_loop(self):
        """
        Exécute la boucle SRE complète.
        Destiné à être appelé par un CronJob Prefect en production.
        """
        logger.info("Début de la boucle de vérification SRE...")

        # 1. Observation — retourne un dict {feature: psi_score}
        psi_results = self.monitor.detect_drift(features_to_monitor=CRITICAL_FEATURES)

        if not psi_results:
            logger.warning(
                "SRE POLICY : Aucune donnée de référence ou de production disponible. Aucune action."
            )
            return

        # 2. Évaluation du seuil — CORRECTION P0 : on itère sur les valeurs, on ne caste pas le dict
        logger.info("📊 Scores PSI par feature :")
        drifted_features = []
        for feature, psi_value in psi_results.items():
            if psi_value is None:
                logger.warning(f"  - {feature}: PSI=N/A (données insuffisantes)")
                continue
            status = (
                "🔴 DRIFT"
                if psi_value > self.psi_threshold
                else ("🟡 WARNING" if psi_value > 0.1 else "🟢 STABLE")
            )
            logger.info(f"  - {feature}: PSI={psi_value:.4f} {status}")
            if psi_value > self.psi_threshold:
                drifted_features.append((feature, psi_value))

        # 3. Réaction Autonome (Policy) — déclenché seulement si au moins 1 feature critique a dérivé
        if drifted_features:
            logger.warning(
                f"SRE POLICY ACTIVÉE : {len(drifted_features)} feature(s) ont dérivé au-delà du seuil PSI={self.psi_threshold} : "
                f"{[f for f, _ in drifted_features]}"
            )
            try:
                # 4. Ré-entraînement via le script principal (train_famille.py)
                # CORRECTION P0 : import fantôme supprimé, on appelle le vrai script
                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                train_script = os.path.join(
                    project_root, "src", "models", "train_famille.py"
                )

                logger.info(f"Lancement du ré-entraînement : {train_script}")
                result = subprocess.run(
                    [sys.executable, train_script],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    logger.error(
                        f"❌ SRE POLICY ÉCHEC : Le ré-entraînement a échoué.\nSTDERR: {result.stderr}"
                    )
                else:
                    logger.info(
                        "✅ SRE POLICY RÉUSSIE : Nouveaux modèles entraînés et versionnés dans MLflow."
                    )
                    logger.info("Nettoyage du shadow_log de production...")
                    shadow_log = os.path.join(
                        project_root, "data", "production_logs", "shadow_log.csv"
                    )
                    if os.path.exists(shadow_log):
                        os.remove(shadow_log)
                        logger.info(f"Shadow log supprimé : {shadow_log}")

            except Exception as e:
                logger.error(f"❌ SRE POLICY ÉCHEC : Exception inattendue. {e}")
        else:
            logger.info(
                f"SRE POLICY : Modèle stable. Aucun feature critique n'a dépassé PSI={self.psi_threshold}. "
                "Aucune action requise."
            )


if __name__ == "__main__":
    engine = ContinuousTrainingEngine()
    engine.run_sre_loop()
