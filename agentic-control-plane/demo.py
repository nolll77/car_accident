"""
Usage :
    python demo.py DATA-042
    python demo.py DATA-042 --action deploy_prod
    python demo.py DATA-042 --action rollback_prod
    python demo.py test-adapter fake
"""

from __future__ import annotations
import sys
from pathlib import Path

from agentic.adapters.baac.observability import BAACObservabilityAdapter
from agentic.adapters.fake.observability import FakeObservabilityAdapter
from agentic.core.contracts import ActionType
from agentic.core.evidence import EvidenceStore
from agentic.core.policy import PolicyEngine
from agentic.runtime.orchestrator import Orchestrator

ROOT = Path(__file__).parent
POLICY_PATH = ROOT / "governance" / "autonomy_policy.yaml"
EVIDENCE_ROOT = ROOT / "evidence_store"

ACTION_MAP = {
    "deploy_prod": ActionType.DEPLOY_PROD,
    "rollback_prod": ActionType.ROLLBACK_PROD,
    "create_issue": ActionType.CREATE_ISSUE,
    "execute_retrain": ActionType.EXECUTE_RETRAIN,
}


def make_orchestrator(adapter) -> Orchestrator:
    return Orchestrator(
        observability=adapter,
        policy_engine=PolicyEngine(POLICY_PATH),
        evidence_store=EvidenceStore(EVIDENCE_ROOT),
    )


def run_demo(risk_id: str, forced_action_str: str | None) -> None:
    adapter = BAACObservabilityAdapter(simulated_drift_score=0.27)
    forced = ACTION_MAP.get(forced_action_str) if forced_action_str else None
    print(f"[DETECTED] risk = {risk_id}")
    make_orchestrator(adapter).run(risk_id=risk_id, forced_action=forced)


def run_adapter_test(adapter_name: str) -> None:
    adapters = {
        "baac": BAACObservabilityAdapter(simulated_drift_score=0.27),
        "fake": FakeObservabilityAdapter(simulated_value=0.31),
    }
    if adapter_name not in adapters:
        print(f"Adapter inconnu : {adapter_name}. Disponibles : {list(adapters)}")
        return
    print(f"--- Test de substitution d'adapter : {adapter_name} ---")
    make_orchestrator(adapters[adapter_name]).run(
        risk_id="DATA-042", detection_window=f"test-{adapter_name}"
    )
    print("Core modifications required: 0")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "test-adapter":
        run_adapter_test(sys.argv[2])
    elif len(sys.argv) >= 2:
        action = None
        if "--action" in sys.argv:
            action = sys.argv[sys.argv.index("--action") + 1]
        run_demo(sys.argv[1], action)
    else:
        print(
            "Usage: python demo.py DATA-042 [--action deploy_prod] | test-adapter fake"
        )
