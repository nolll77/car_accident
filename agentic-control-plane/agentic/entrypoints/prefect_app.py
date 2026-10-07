"""
Entrypoint Prefect du Agentic Control Plane.

Ce module est l'unique couche où les décorateurs Prefect (@task, @flow) sont autorisés.
Il importe les composants du Core et du Runtime mais n'en modifie jamais la logique.

Usage local :
    python -m agentic.entrypoints.prefect_app

Déploiement :
    prefect deploy agentic/entrypoints/prefect_app.py:agentic_control_plane_flow
"""

from __future__ import annotations

import json
from pathlib import Path

from prefect import flow, task, get_run_logger

# --- Adaptateurs & Policy (imports différés pour Clean Architecture) ---
POLICY_PATH = (
    Path(__file__).parent.parent.parent / "governance" / "autonomy_policy.yaml"
)
EVIDENCE_DIR = Path(__file__).parent.parent.parent / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def _get_adapter(risk_id: str):
    """Fabrique le bon adaptateur réel selon le préfixe du risk_id."""
    prefix = risk_id.split("-")[0].upper()
    if prefix == "MODEL":
        from agentic.adapters.mlflow.observability import MLflowObservabilityAdapter

        return MLflowObservabilityAdapter(), "model_f1_drop"
    elif prefix == "INFRA":
        from agentic.adapters.infra.observability import InfraObservabilityAdapter

        return InfraObservabilityAdapter(), "shadow_log_staleness"
    else:
        from agentic.adapters.baac.observability import BAACObservabilityAdapter

        return BAACObservabilityAdapter(), "data_drift"


@task(name="get-signal", retries=2, retry_delay_seconds=10)
def fetch_and_route(risk_id: str, detection_window: str) -> dict:
    """
    Récupère le signal depuis l'adaptateur d'observabilité réel.
    - DATA-* → Evidently (prometheus_metrics.txt)
    - MODEL-* → MLflow (mlflow.db)
    - INFRA-* → Infra (shadow_log.csv)
    """
    adapter, signal_id = _get_adapter(risk_id)
    signal = adapter.get_signal(signal_id)
    logger = get_run_logger()
    logger.info(
        f"[Signal] {risk_id}: {signal.value:.4f} > seuil {signal.threshold} → breach={signal.breached}"
    )
    return signal.model_dump(mode="json")


@task(name="process-episode")
def process_episode(risk_id: str, signal_data: dict, detection_window: str) -> dict:
    """
    Orchestre le cycle complet :
    Specialist (Diagnose) → RemediationAgent (Plan) → PolicyEngine (Decide)
    """
    from agentic.core.contracts import Signal
    from agentic.core.evidence import EvidenceStore
    from agentic.core.policy import PolicyEngine
    from agentic.runtime.orchestrator import Orchestrator

    logger = get_run_logger()

    _signal = Signal(**signal_data)  # noqa: F841 — parsed for validation
    evidence_store = EvidenceStore(EVIDENCE_DIR)
    policy_engine = PolicyEngine(POLICY_PATH)
    observability, _ = _get_adapter(risk_id)  # L'adaptateur réel déjà routé

    orchestrator = Orchestrator(
        observability=observability,
        policy_engine=policy_engine,
        evidence_store=evidence_store,
    )

    episode = orchestrator.run(
        risk_id=risk_id,
        detection_window=detection_window,
    )

    episode_dict = episode.to_dict()
    logger.info(
        f"[Episode {episode.episode_id}] "
        f"Decision={episode.policy_evaluation.decision.value if episode.policy_evaluation else 'N/A'} | "
        f"Action={episode.action_proposal.type.value if episode.action_proposal else 'N/A'}"
    )

    # Persistance locale de l'épisode
    output_path = EVIDENCE_DIR / f"episode_{episode.episode_id}.json"
    output_path.write_text(json.dumps(episode_dict, indent=2), encoding="utf-8")
    logger.info(f"Épisode sauvegardé → {output_path}")

    return episode_dict


@flow(
    name="Agentic Control Plane",
    description="Pipeline agentique de détection et remédiation des risques MLOps.",
    version="1.0.0",
)
def agentic_control_plane_flow(
    risk_id: str = "DATA-042",
    detection_window: str = "2026-09-30",
):
    """
    Flow principal du Control Plane.

    En production, ce flow sera déclenché :
    - Via webhook (Prometheus AlertManager, Evidently) → déclenche `agentic_control_plane_flow(risk_id=...)`
    - Via déploiement planifié (Prefect `CronSchedule`) pour la surveillance continue.
    """
    logger = get_run_logger()
    logger.info(
        f"▶️  Démarrage du Control Plane — risk_id={risk_id} | window={detection_window}"
    )

    # Étape 1 : Récupérer le signal
    signal_data = fetch_and_route(risk_id, detection_window)

    # Étape 2 : Orchestrer le traitement (Diagnose → Plan → Decide)
    episode = process_episode(risk_id, signal_data, detection_window)

    logger.info("✅ Épisode traité avec succès.")
    return episode


if __name__ == "__main__":
    # Lancement local (hors serveur Prefect)
    result = agentic_control_plane_flow(
        risk_id="DATA-042",
        detection_window="2026-10-02",
    )
    print(json.dumps(result, indent=2))
