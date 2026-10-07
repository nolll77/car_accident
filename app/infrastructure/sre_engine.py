import time
import uuid
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# --- Prometheus Metrics ---
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.001, 0.005, 0.010, 0.050, 0.100, 0.500, 1.0, 5.0],
)

# --- SRE SLO Thresholds (ex: BAAC) ---
# Objectif: 99% des requêtes d'inférence < 200ms
SLO_LATENCY_P99_MS = 200.0


async def sre_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware d'Observabilité SRE:
    - Injecte un X-Trace-Id s'il n'y en a pas
    - Mesure la latence
    - Exporte les SLI vers Prometheus
    """
    start_time = time.perf_counter()

    # 1. Traceability
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    request.state.trace_id = trace_id

    # 2. Execution
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        # 3. Telemetry Calculation
        latency_sec = time.perf_counter() - start_time
        endpoint = request.url.path
        method = request.method

        # 4. SLI Recording
        REQUEST_COUNT.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency_sec)

        # 5. Injection du trace_id dans la réponse
        if "response" in locals():
            response.headers["X-Trace-Id"] = trace_id

    return response


def get_metrics():
    """Returns the Prometheus metrics payload."""
    return generate_latest(), CONTENT_TYPE_LATEST
