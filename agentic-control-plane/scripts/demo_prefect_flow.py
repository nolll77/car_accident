"""
Démonstration du flow Prefect avec signaux RÉELS et LLMs simulés.

Lance le cycle complet :
  [Real] prometheus_metrics.txt → Signal(value=0.75, breach=True)
  [Mock] DataSpecialist         → Diagnosis(risk_id=DATA-042, confidence=0.92)
  [Mock] RemediationAgent       → ActionProposal(type=create_issue)
  [Real] PolicyEngine           → Decision.ALLOW

Usage :
    .venv/bin/python scripts/demo_prefect_flow.py
"""

import sys
from pathlib import Path

# Assurer que le package agentic est importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import patch

from agentic.core.contracts import ActionProposal, ActionType, Diagnosis, Finding


# ── Bouchons LLM ────────────────────────────────────────────────────────────


def _mock_diagnose(self, risk_id, signal, context_info=""):
    """Simule le diagnostic du DataSpecialist sans appel réseau."""
    return Diagnosis(
        risk_id="DATA-042",
        agent="data_specialist_llm [MOCK]",
        confidence=0.92,
        findings=(
            Finding(
                description=(
                    f"Dérive significative détectée : drift_share={signal.value:.0%}. "
                    f"Features les plus touchées : {', '.join(signal.dimensions[:3])}. "
                    "Suspect principal : changement de distribution démographique (an_nais)."
                ),
                evidence_ref="baac.evidently.prometheus :: mlops_baac_drift_share",
            ),
            Finding(
                description=(
                    "La feature nb_accidents_zone présente un score Jensen-Shannon de 0.647 "
                    "(seuil critique 0.20). Risque de biais géographique croissant."
                ),
                evidence_ref="baac.evidently.prometheus :: mlops_baac_feature_drift_score[nb_accidents_zone]",
            ),
        ),
    )


def _mock_plan_action(self, diagnosis):
    """Simule la décision du RemediationAgent sans appel réseau."""
    return ActionProposal(
        type=ActionType.CREATE_ISSUE,
        risk_id=diagnosis.risk_id,
        requested_by="remediation_agent_llm [MOCK]",
        reversible=True,
        blast_radius=2,
        parameters={
            "title": "[AUTO] Dérive DATA-042 détectée — drift_share=75%",
            "body": (
                "Le pipeline de monitoring Evidently a détecté une dérive majeure (75%) "
                "sur 9/12 features BAAC. Features prioritaires : nb_accidents_zone (0.647), "
                "trajet (0.599), place (0.419). Action recommandée : relancer l'harmonisation "
                "et ré-entraîner le modèle Famille A."
            ),
            "labels": ["data-drift", "auto-generated", "DATA-042"],
        },
    )


# ── Exécution du Flow ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("  DEMO PREFECT FLOW — Signaux réels + LLMs simulés")
    print("=" * 65)
    print()

    from agentic.runtime.specialist import DataSpecialist
    from agentic.runtime.remediation_agent import RemediationAgent
    from agentic.entrypoints.prefect_app import agentic_control_plane_flow

    with (
        patch.object(DataSpecialist, "diagnose", _mock_diagnose),
        patch.object(RemediationAgent, "plan_action", _mock_plan_action),
    ):
        result = agentic_control_plane_flow(
            risk_id="DATA-042",
            detection_window="2026-10-02",
        )

    print()
    print("=" * 65)
    print("  RÉSULTAT DE L'ÉPISODE")
    print("=" * 65)

    import json

    print(json.dumps(result, indent=2, ensure_ascii=False))
