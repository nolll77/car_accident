import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict

from app.serving.model_loader import get_serving_engine, ModelServingEngine
from app.domain.observations.models import PredictionEvent
from app.infrastructure.drift_monitor import get_drift_monitor, DriftMonitor
from app.domain.remediation.policy_engine import get_policy_engine, PolicyEngine

router = APIRouter(prefix="/inference", tags=["inference"])


class PredictionRequest(BaseModel):
    model_name: str
    model_version: str
    features: Dict[str, float]
    trace_id: str | None = None


class PredictionResponse(BaseModel):
    prediction: float
    model_uri: str
    latency_ms: float


def async_log_telemetry(
    event: PredictionEvent, monitor: DriftMonitor, policy: PolicyEngine
):
    """
    Background task to simulate pushing the PredictionEvent to the Event Bus.
    And observing it in the Temporal Drift Monitor.
    """
    print(f"[Event Bus] Capturing telemetry: {event.model_dump_json(indent=2)}")
    degraded_event = monitor.observe(event)
    if degraded_event:
        print(f"[Event Bus] 🔥 NEW EVENT: {degraded_event.model_dump_json(indent=2)}")
        # Phase 8: Autonomous Remediation
        policy.evaluate(degraded_event)


@router.post("/predict", response_model=PredictionResponse)
def make_prediction(
    request: PredictionRequest,
    background_tasks: BackgroundTasks,
    engine: ModelServingEngine = Depends(get_serving_engine),
    monitor: DriftMonitor = Depends(get_drift_monitor),
    policy: PolicyEngine = Depends(get_policy_engine),
):
    start_time = time.perf_counter()

    try:
        # Extract features in the order expected by the model [lidar, radar]
        # In a real system, the feature store/contract would enforce ordering
        feature_vector = [
            request.features.get("lidar_distance_m", 0.0),
            request.features.get("radar_velocity_kmh", 0.0),
        ]

        # Inference
        prediction = engine.predict(
            request.model_name, request.model_version, feature_vector
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Build telemetry event
        event = PredictionEvent(
            model_version_id=f"{request.model_name}/{request.model_version}",
            features=request.features,
            prediction=float(prediction),
            latency_ms=latency_ms,
            trace_id=request.trace_id,
        )

        # Send telemetry to Event Bus asynchronously
        background_tasks.add_task(async_log_telemetry, event, monitor, policy)

        return PredictionResponse(
            prediction=float(prediction),
            model_uri=f"models:/{request.model_name}/{request.model_version}",
            latency_ms=latency_ms,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
