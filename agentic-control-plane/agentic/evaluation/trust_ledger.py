import json
from pathlib import Path
from agentic.core.contracts import Signal
from agentic.runtime.specialist import DataSpecialist
from agentic.runtime.model_specialist import ModelSpecialist
from agentic.runtime.infra_specialist import InfraSpecialist
from tests.chaos.inject_data_042_drift import DriftInjector
from tests.chaos.inject_data_043_schema import SchemaCorruptionInjector
from tests.chaos.inject_model_012_collapse import ModelCollapseInjector
from tests.chaos.inject_infra_005_pg_saturation import PgSaturationInjector


def evaluate_shadow_mode():
    data_specialist = DataSpecialist()
    model_specialist = ModelSpecialist()
    infra_specialist = InfraSpecialist()
    from agentic.runtime.remediation_agent import RemediationAgent

    remediation_agent = RemediationAgent()

    injectors = [
        DriftInjector(),
        SchemaCorruptionInjector(),
        ModelCollapseInjector(),
        PgSaturationInjector(),
    ]
    results = []

    for injector in injectors:
        raw_signal = injector.get_signal_dict()
        signal = Signal(**raw_signal)

        if "model" in injector.expected_risk_id.lower():
            specialist = model_specialist
        elif "infra" in injector.expected_risk_id.lower():
            specialist = infra_specialist
        else:
            specialist = data_specialist

        # 1. Shadow Run - Diagnose
        diagnosis = specialist.diagnose(
            risk_id="UNKNOWN",
            signal=signal,
            context_info=f"Chaos test for {injector.name}",
        )

        # 2. Shadow Run - Remediate
        action_proposal = remediation_agent.plan_action(diagnosis)

        match = diagnosis.risk_id == injector.expected_risk_id
        results.append(
            {
                "injector": injector.name,
                "expected_risk_id": injector.expected_risk_id,
                "predicted_risk_id": diagnosis.risk_id,
                "predicted_action": action_proposal.type.value,
                "match": match,
                "findings": [
                    {"desc": f.description, "ref": f.evidence_ref}
                    for f in diagnosis.findings
                ],
            }
        )

    accuracy = sum(1 for r in results if r["match"]) / len(results)
    false_negatives = sum(1 for r in results if not r["match"])

    ledger = {
        "timestamp": Signal().observed_at,
        "metrics": {"accuracy": accuracy, "false_negatives_sev5": false_negatives},
        "episodes": results,
    }

    ledger_path = Path(__file__).parent.parent.parent / "trust_ledger.json"
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)

    print(f"Trust Ledger generated: {ledger_path}")
    print(f"Accuracy: {accuracy * 100}% | False Negatives: {false_negatives}")


if __name__ == "__main__":
    evaluate_shadow_mode()
