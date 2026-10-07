"""
Preuve de portabilité : le même flux tourne avec deux adapters aux
sémantiques différentes, sans aucune modification du Core.
"""

import shutil
from pathlib import Path

import pytest

from agentic.adapters.baac.observability import BAACObservabilityAdapter
from agentic.adapters.fake.observability import FakeObservabilityAdapter
from agentic.core.contracts import Decision
from agentic.core.evidence import EvidenceStore
from agentic.core.policy import PolicyEngine
from agentic.runtime.orchestrator import Orchestrator

POLICY_PATH = Path(__file__).parent.parent / "governance" / "autonomy_policy.yaml"


@pytest.fixture
def tmp_store(tmp_path):
    yield EvidenceStore(tmp_path / "evidence")
    shutil.rmtree(tmp_path, ignore_errors=True)


@pytest.mark.parametrize(
    "adapter,window",
    [
        (BAACObservabilityAdapter(fallback_score=0.27), "baac-window"),
        (FakeObservabilityAdapter(simulated_value=0.31), "fake-window"),
    ],
    ids=["baac_adapter", "fake_adapter_semantic_variation"],
)
def test_data_042_adapter_agnostic(adapter, window, tmp_store, monkeypatch):
    from agentic.runtime.specialist import DataSpecialist
    from agentic.runtime.remediation_agent import RemediationAgent
    from agentic.core.contracts import Diagnosis, Finding, ActionProposal, ActionType

    def mock_diagnose(self, risk_id, signal, context_info=""):
        return Diagnosis(
            risk_id=risk_id,
            agent="data_specialist_llm",
            confidence=0.9,
            findings=(
                Finding(
                    description="Mocked drift finding", evidence_ref="mock_evidence"
                ),
            ),
        )

    monkeypatch.setattr(DataSpecialist, "diagnose", mock_diagnose)

    def mock_plan_action(self, diagnosis):
        return ActionProposal(
            type=ActionType.CREATE_ISSUE,
            risk_id=diagnosis.risk_id,
            requested_by="remediation_agent_llm",
            reversible=True,
            blast_radius=2,
        )

    monkeypatch.setattr(RemediationAgent, "plan_action", mock_plan_action)

    orchestrator = Orchestrator(
        observability=adapter,
        policy_engine=PolicyEngine(POLICY_PATH),
        evidence_store=tmp_store,
    )
    episode = orchestrator.run(risk_id="DATA-042", detection_window=window)

    assert episode.policy_evaluation.decision == Decision.ALLOW
    assert episode.action_proposal.type.value == "create_issue"
    assert episode.signal.breached is True
