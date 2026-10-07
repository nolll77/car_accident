"""
Les 7 contrats qui traversent le Core. Aucune classe ici ne doit jamais
importer un provider concret (evidently, mlflow, postgres, github, prefect...).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# 1. Risk
class Risk(BaseModel):
    id: str
    title: str
    domain: str
    severity: int  # 1-5, intrinsèque
    detectability: int  # 1-5
    blast_radius: int  # 1-5
    allowed_actions: tuple[str, ...]

    @property
    def priority_score(self) -> float:
        return (
            (self.severity * 0.4)
            + (self.detectability * 0.4)
            + (self.blast_radius * 0.2)
        )


# 2. Signal
class Signal(BaseModel):
    signal_id: str
    value: float
    threshold: float
    source: str
    observed_at: str = Field(default_factory=utcnow_iso)
    dimensions: tuple[str, ...] = Field(default_factory=tuple)

    @property
    def breached(self) -> bool:
        return self.value > self.threshold


# 3. Diagnosis
class Finding(BaseModel):
    description: str
    evidence_ref: str


class Diagnosis(BaseModel):
    risk_id: str
    agent: str
    confidence: float
    findings: tuple[Finding, ...]
    ground_truth_risk_id: Optional[str] = None

    @property
    def matches_ground_truth(self) -> Optional[bool]:
        if self.ground_truth_risk_id is None:
            return None
        return self.risk_id == self.ground_truth_risk_id


# 4. ActionProposal
class ActionType(str, Enum):
    INVESTIGATE = "investigate"
    CREATE_ISSUE = "create_issue"
    PROPOSE_RETRAIN = "propose_retrain"
    EXECUTE_RETRAIN = "execute_retrain"
    DEPLOY_STAGING = "deploy_staging"
    DEPLOY_PROD = "deploy_prod"
    ROLLBACK_PROD = "rollback_prod"
    DATABASE_WRITE = "database_write"


class ActionProposal(BaseModel):
    type: ActionType
    risk_id: str
    requested_by: str
    reversible: bool
    blast_radius: int
    parameters: dict[str, Any] = Field(default_factory=dict)


# 5. PolicyDecision
class Decision(str, Enum):
    ALLOW = "ALLOW"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"


class PolicyDecision(BaseModel):
    decision: Decision
    policy_version: str
    matched_rule: str
    reason_codes: tuple[str, ...]


# 6. ExecutionResult
class ExecutionResult(BaseModel):
    status: str
    executor: str
    result_ref: Optional[str] = None
    details: Optional[str] = None


# 7. Episode (Evidence)
class Episode(BaseModel):
    episode_id: str
    dedup_key: str
    timestamp_utc: str
    state_trace: list[str]
    risk_id: str
    signal: Signal
    diagnosis: Optional[Diagnosis] = None
    action_proposal: Optional[ActionProposal] = None
    policy_evaluation: Optional[PolicyDecision] = None
    human_approval_required: bool
    execution: Optional[ExecutionResult] = None

    def to_dict(self) -> dict:
        return self.model_dump(mode="json")
