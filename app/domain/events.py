from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime


@dataclass
class DomainEvent:
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[UUID] = None
    causation_id: Optional[UUID] = None


@dataclass
class DatasetRegisteredEvent(DomainEvent):
    dataset_id: UUID
    namespace: str
    name: str


@dataclass
class DatasetVersionCreatedEvent(DomainEvent):
    dataset_version_id: UUID
    dataset_id: UUID
    version_tag: str


@dataclass
class TrainingRunStartedEvent(DomainEvent):
    training_run_id: UUID
    dataset_version_id: UUID


@dataclass
class TrainingRunCompletedEvent(DomainEvent):
    training_run_id: UUID
    metrics: Dict[str, float]


@dataclass
class ModelVersionRegisteredEvent(DomainEvent):
    model_version_id: UUID
    training_run_id: UUID
    artifact_uri: str


@dataclass
class DeploymentStatusChangedEvent(DomainEvent):
    deployment_id: UUID
    new_status: str
