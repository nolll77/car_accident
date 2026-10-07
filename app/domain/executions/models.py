from enum import Enum
import uuid
from sqlalchemy import Column, String, JSON, DateTime
from datetime import datetime
from app.infrastructure.database import Base


def get_uuid():
    return str(uuid.uuid4())


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionModel(Base):
    __tablename__ = "executions"

    id = Column(String, primary_key=True, default=get_uuid)
    status = Column(String, nullable=False, default=ExecutionStatus.QUEUED.value)
    type = Column(String, nullable=False)
    input_data = Column(JSON, nullable=False, default=dict)
    result_data = Column(JSON, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
