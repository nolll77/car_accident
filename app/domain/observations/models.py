import uuid
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field


class PredictionEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_version_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    features: Dict[str, Any]
    prediction: Any
    latency_ms: float

    # Traceability context
    trace_id: str | None = None
    tenant_id: str | None = None


class ModelDegradedEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_version_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    drift_score: float
    feature_name: str
    reason: str
