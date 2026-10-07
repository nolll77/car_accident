import uuid
from sqlalchemy import Column, String, JSON, DateTime, Integer, ForeignKey
from datetime import datetime
from .database import Base


# Fallback for SQLite compat if needed
def get_uuid():
    return str(uuid.uuid4())


class DatasetModel(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=get_uuid)
    namespace = Column(String, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    state = Column(String, default="REGISTERED")
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class DatasetVersionModel(Base):
    __tablename__ = "dataset_versions"

    id = Column(String, primary_key=True, default=get_uuid)
    dataset_id = Column(String, ForeignKey("datasets.id"))
    version_tag = Column(String, nullable=False)
    storage_uri = Column(String, nullable=False)
    schema_ref = Column(String, nullable=False)
    state = Column(String, default="PENDING")
    record_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingRunModel(Base):
    __tablename__ = "training_runs"

    id = Column(String, primary_key=True, default=get_uuid)
    dataset_version_id = Column(String, ForeignKey("dataset_versions.id"))
    model_name = Column(String, nullable=False)
    hyperparameters = Column(JSON, default=dict)
    status = Column(String, default="QUEUED")
    metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
