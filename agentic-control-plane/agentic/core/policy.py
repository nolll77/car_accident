"""
PolicyEngine : fonction pure, aucune dépendance externe, aucun LLM.
(ActionProposal, autonomy_policy) -> PolicyDecision
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agentic.core.contracts import ActionProposal, Decision, PolicyDecision


class PolicyEngine:
    def __init__(self, policy_path: Path):
        with open(policy_path, "r", encoding="utf-8") as f:
            raw: dict[str, Any] = yaml.safe_load(f)
        self.policy_version: str = raw["policy_version"]
        self.rules: dict[str, Any] = raw["rules"]

    def evaluate(self, action: ActionProposal) -> PolicyDecision:
        rule = self.rules.get(action.type.value)

        if rule is None:
            return PolicyDecision(
                decision=Decision.DENY,
                policy_version=self.policy_version,
                matched_rule="__no_rule__",
                reason_codes=("NO_MATCHING_RULE",),
            )

        autonomy = rule.get("autonomy")
        conditions = rule.get("conditions", {})

        if "blast_radius_max" in conditions:
            if action.blast_radius > conditions["blast_radius_max"]:
                return PolicyDecision(
                    decision=Decision.DENY,
                    policy_version=self.policy_version,
                    matched_rule=action.type.value,
                    reason_codes=("BLAST_RADIUS_EXCEEDED",),
                )

        if autonomy == "autonomous":
            return PolicyDecision(
                decision=Decision.ALLOW,
                policy_version=self.policy_version,
                matched_rule=action.type.value,
                reason_codes=("ACTION_ALLOWED",),
            )

        if autonomy == "human_approval_required":
            return PolicyDecision(
                decision=Decision.REQUIRE_APPROVAL,
                policy_version=self.policy_version,
                matched_rule=action.type.value,
                reason_codes=("HUMAN_APPROVAL_REQUIRED",),
            )

        return PolicyDecision(
            decision=Decision.DENY,
            policy_version=self.policy_version,
            matched_rule=action.type.value,
            reason_codes=("UNKNOWN_AUTONOMY_LEVEL",),
        )
