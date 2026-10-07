import hashlib


def compute_dedup_key(
    risk_id: str, signal_source: str, environment: str, detection_window: str
) -> str:
    raw = f"{risk_id}:{signal_source}:{environment}:{detection_window}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
