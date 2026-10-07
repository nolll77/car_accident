"""
Fake adapter — variation sémantique volontaire pour prouver que le Core
reste générique. L'adapter normalise vers le SignalContract commun.
"""

from __future__ import annotations
from agentic.core.contracts import Signal


class FakeObservabilityAdapter:
    def __init__(self, simulated_value: float = 0.31):
        self._value = simulated_value

    def get_signal(self, signal_id: str) -> Signal:
        if signal_id != "data_drift":
            raise ValueError(f"Signal inconnu pour Fake : {signal_id}")
        # Provider fictif avec vocabulaire différent en interne
        raw = {
            "metric_name": "feature_distribution_shift",
            "score": self._value,
            "dims": ["age", "vehicle_type"],
        }
        return Signal(
            signal_id="data_drift",
            value=raw["score"],
            threshold=0.20,
            source="fake.other_provider",
            dimensions=tuple(raw["dims"]),
        )
