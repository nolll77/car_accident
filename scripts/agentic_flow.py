import uuid
from typing import Dict, Any
from prefect import flow, task, get_run_logger

# ==========================================
# Agentic Control Plane - Prefect Deployment
# ==========================================


@task(name="Extract Signal (Webhooks)")
def extract_signal(payload: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_run_logger()
    logger.info(f"Extracting signal from payload: {payload['source']}")
    return payload


@flow(
    name="Data Agent Flow",
    description="Agent spécialiste des dérives de données (DATA)",
)
def data_agent_flow(signal: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_run_logger()
    logger.info(f"🔍 Data Agent: Analyzing signal {signal['signal_id']}...")

    # Mocking Diagnosis Contract
    diagnosis = {
        "agent": "Data_Specialist",
        "confidence": 0.95,
        "findings": [
            f"Drift critique confirmé (PSI={signal.get('psi_score', 'N/A')}) sur '{signal.get('feature', 'unknown')}'"
        ],
        "proposed_action": "propose_retrain",
    }
    logger.info(f"✅ Data Agent Diagnosis: {diagnosis['findings'][0]}")
    return diagnosis


@flow(
    name="Infra Agent Flow",
    description="Agent spécialiste des bases de données et Docker (INFRA)",
)
def infra_agent_flow(signal: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_run_logger()
    logger.info(f"🔍 Infra Agent: Analyzing signal {signal['signal_id']}...")

    diagnosis = {
        "agent": "Infra_Specialist",
        "confidence": 0.99,
        "findings": ["PostgreSQL injoignable, bascule réplica nécessaire."],
        "proposed_action": "create_issue",
    }
    logger.info(f"✅ Infra Agent Diagnosis: {diagnosis['findings'][0]}")
    return diagnosis


@flow(
    name="Model Agent Flow",
    description="Agent spécialiste du Registry et du Serving (MODEL)",
)
def model_agent_flow(signal: Dict[str, Any]) -> Dict[str, Any]:
    logger = get_run_logger()
    logger.info(f"🔍 Model Agent: Analyzing signal {signal['signal_id']}...")

    diagnosis = {
        "agent": "Model_Specialist",
        "confidence": 0.92,
        "findings": ["Staleness détecté. Le modèle Champion est obsolète."],
        "proposed_action": "propose_retrain",
    }
    logger.info(f"✅ Model Agent Diagnosis: {diagnosis['findings'][0]}")
    return diagnosis


@flow(
    name="Remediation Agent Flow", description="Synthétise et applique le Policy Engine"
)
def remediation_agent_flow(diagnosis: Dict[str, Any], risk_id: str) -> str:
    logger = get_run_logger()
    logger.info(
        f"⚖️ Remediation Agent: Evaluates {diagnosis['proposed_action']} for {risk_id}"
    )

    # Mock Policy Engine (Shadow Mode)
    decision = "DENY"
    logger.info(f"🛡️ Policy Engine Decision: {decision} (Shadow Mode Active)")

    episode_id = f"EP-{str(uuid.uuid4())[:8]}"
    logger.info(f"💾 Evidence Store: Episode {episode_id} saved (Hash Chain).")

    return episode_id


@flow(
    name="Agentic Orchestrator",
    description="Point d'entrée principal (Webhook Trigger)",
)
def orchestrator_flow(risk_id: str, payload: Dict[str, Any]):
    logger = get_run_logger()
    logger.info(f"🚀 Orchestrator received trigger for {risk_id}")

    signal = extract_signal(payload)

    # Routing
    if "DATA" in risk_id:
        diagnosis = data_agent_flow(signal)
    elif "INFRA" in risk_id:
        diagnosis = infra_agent_flow(signal)
    else:
        diagnosis = model_agent_flow(signal)

    episode_id = remediation_agent_flow(diagnosis, risk_id)
    logger.info(f"🏁 Orchestration terminée. Preuve générée : {episode_id}")


if __name__ == "__main__":
    # Test local : Injection de Chaos depuis le main
    print("Injection de Chaos: DATA-042 (Data Drift)")
    orchestrator_flow(
        risk_id="DATA-042",
        payload={
            "signal_id": "sig-001",
            "source": "evidently.drift_monitor",
            "psi_score": 0.35,
            "feature": "age",
        },
    )
