from pathlib import Path
from agentic.core.contracts import ActionProposal, ActionType, Decision
from agentic.core.policy import PolicyEngine

POLICY_PATH = Path(__file__).parent.parent / "governance" / "autonomy_policy.yaml"


def test_allows_issue_creation():
    engine = PolicyEngine(POLICY_PATH)
    action = ActionProposal(
        type=ActionType.CREATE_ISSUE,
        risk_id="DATA-042",
        requested_by="test",
        reversible=True,
        blast_radius=2,
    )
    assert engine.evaluate(action).decision == Decision.ALLOW


def test_denies_over_blast_radius():
    engine = PolicyEngine(POLICY_PATH)
    action = ActionProposal(
        type=ActionType.CREATE_ISSUE,
        risk_id="DATA-042",
        requested_by="test",
        reversible=True,
        blast_radius=5,
    )
    result = engine.evaluate(action)
    assert result.decision == Decision.DENY
    assert "BLAST_RADIUS_EXCEEDED" in result.reason_codes


def test_requires_approval_for_deploy_prod():
    engine = PolicyEngine(POLICY_PATH)
    action = ActionProposal(
        type=ActionType.DEPLOY_PROD,
        risk_id="DATA-042",
        requested_by="test",
        reversible=False,
        blast_radius=5,
    )
    assert engine.evaluate(action).decision == Decision.REQUIRE_APPROVAL


def test_requires_approval_for_rollback():
    engine = PolicyEngine(POLICY_PATH)
    action = ActionProposal(
        type=ActionType.ROLLBACK_PROD,
        risk_id="DATA-042",
        requested_by="test",
        reversible=False,
        blast_radius=5,
    )
    assert engine.evaluate(action).decision == Decision.REQUIRE_APPROVAL
