from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime


@dataclass
class Dataset:
    id: UUID
    namespace: str
    name: str
    owner: str
    state: str = "REGISTERED"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        namespace: str,
        name: str,
        owner: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "Dataset":
        if not namespace:
            raise ValueError("namespace is required")
        if not name:
            raise ValueError("name is required")
        if not owner:
            raise ValueError("owner is required")

        return cls(
            id=uuid4(),
            namespace=namespace,
            name=name,
            owner=owner,
            metadata=metadata or {},
        )


@dataclass
class DatasetVersion:
    id: UUID
    dataset_id: UUID
    version_tag: str
    storage_uri: str
    schema_ref: str
    state: str = "PENDING"
    record_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def create(
        cls,
        dataset_id: UUID,
        version_tag: str,
        storage_uri: str,
        schema_ref: str,
    ) -> "DatasetVersion":
        return cls(
            id=uuid4(),
            dataset_id=dataset_id,
            version_tag=version_tag,
            storage_uri=storage_uri,
            schema_ref=schema_ref,
        )


@dataclass
class TrainingRun:
    id: UUID
    dataset_version_id: UUID
    model_name: str
    hyperparameters: Dict[str, Any]
    status: str = "QUEUED"
    metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ModelVersion:
    id: UUID
    training_run_id: UUID
    model_name: str
    version_tag: str
    artifact_uri: str
    status: str = "STAGING"
    metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Deployment:
    id: UUID
    model_version_id: UUID
    environment: str
    endpoint_url: str
    status: str = "INITIALIZING"
    created_at: datetime = field(default_factory=datetime.utcnow)
