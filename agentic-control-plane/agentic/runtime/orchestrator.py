"""
Orchestrator : câble Signal -> Specialist -> Diagnosis -> ActionProposal ->
PolicyEngine -> (Executor | Human Gate | Deny), avec State Machine et
Evidence Store systématiques. Zéro import de provider concret.
"""

from __future__ import annotations
from typing import Optional

from agentic.adapters.protocol import ObservabilityAdapter
from agentic.core.contracts import (
    ActionProposal,
    ActionType,
    Decision,
    Episode,
    ExecutionResult,
)
from agentic.core.evidence import EvidenceStore
from agentic.core.idempotency import compute_dedup_key
from agentic.core.policy import PolicyEngine
from agentic.core.state import StateMachine
from agentic.runtime import executor as executor_module


class Orchestrator:
    def __init__(
        self,
        observability: ObservabilityAdapter,
        policy_engine: PolicyEngine,
        evidence_store: EvidenceStore,
        environment: str = "staging",
    ):
        self.observability = observability
        self.policy_engine = policy_engine
        self.evidence_store = evidence_store
        self.environment = environment

    def _get_specialist(self, risk_id: str):
        if "MODEL" in risk_id.upper():
            from agentic.runtime.model_specialist import ModelSpecialist

            return ModelSpecialist()
        elif "INFRA" in risk_id.upper():
            from agentic.runtime.infra_specialist import InfraSpecialist

            return InfraSpecialist()
        else:
            from agentic.runtime.specialist import DataSpecialist

            return DataSpecialist()

    def run(
        self,
        risk_id: str,
        signal_id: str = "data_drift",
        forced_action: Optional[ActionType] = None,
        detection_window: str = "2026-09-30",
    ) -> Episode:
        sm = StateMachine(initial="DETECTED")
        signal = self.observability.get_signal(signal_id)

        dedup_key = compute_dedup_key(
            risk_id=risk_id,
            signal_source=signal.source,
            environment=self.environment,
            detection_window=detection_window,
        )
        existing = self.evidence_store.find_existing_episode(dedup_key)
        if existing is not None:
            print(
                f"[IDEMPOTENCE] Épisode déjà traité : {existing} (dedup_key={dedup_key[:12]}...)"
            )

        episode_id = self.evidence_store.next_episode_id()
        specialist = self._get_specialist(risk_id)

        # INVESTIGATING
        sm.transition("INVESTIGATING")
        print(f"[{sm.current}] specialist = {specialist.name}")

        # DIAGNOSED
        diagnosis = specialist.diagnose(risk_id, signal)
        sm.transition("DIAGNOSED")
        print(f"[{sm.current}] {diagnosis.findings[0].description}")

        # PLANNED
        if forced_action is not None:
            action_type = forced_action
            action = ActionProposal(
                type=action_type,
                risk_id=risk_id,
                requested_by=specialist.name,
                reversible=action_type
                in (
                    ActionType.CREATE_ISSUE,
                    ActionType.INVESTIGATE,
                    ActionType.PROPOSE_RETRAIN,
                ),
                blast_radius=2 if action_type == ActionType.CREATE_ISSUE else 0,
            )
        else:
            from agentic.runtime.remediation_agent import RemediationAgent

            remediation_agent = RemediationAgent()
            action = remediation_agent.plan_action(diagnosis)

        sm.transition("PLANNED")
        print(f"[{sm.current}] action = {action.type.value}")

        # POLICY
        decision = self.policy_engine.evaluate(action)
        print(
            f"[POLICY] {decision.decision.value} "
            f"(règle: {decision.matched_rule}, raisons: {', '.join(decision.reason_codes)})"
        )

        execution: Optional[ExecutionResult] = None
        human_approval_required = False

        if decision.decision == Decision.ALLOW:
            sm.transition("EXECUTING")
            execution = executor_module.execute(action)
            sm.transition("RESOLVED")
            print(f"[{sm.current}] {execution.details} (ref: {execution.result_ref})")

        elif decision.decision == Decision.REQUIRE_APPROVAL:
            sm.transition("AWAITING_APPROVAL")
            human_approval_required = True
            print(
                f"[{sm.current}] BLOQUÉ — approbation humaine requise, aucune exécution"
            )

        else:  # DENY
            sm.transition("DENIED")
            print("[DENIED] Refusé par la politique — aucune exécution")

        episode = Episode(
            episode_id=episode_id,
            dedup_key=dedup_key,
            timestamp_utc=signal.observed_at,
            state_trace=sm.trace,
            risk_id=risk_id,
            signal=signal,
            diagnosis=diagnosis,
            action_proposal=action,
            policy_evaluation=decision,
            human_approval_required=human_approval_required,
            execution=execution,
        )

        path = self.evidence_store.save(episode)
        print(f"[EVIDENCE] {path}")
        return episode
