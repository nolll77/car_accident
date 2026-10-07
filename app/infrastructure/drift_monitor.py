from typing import List, Dict
import numpy as np

from app.domain.observations.models import PredictionEvent, ModelDegradedEvent


class DriftMonitor:
    def __init__(self, baseline_stats: Dict[str, Dict[str, float]]):
        """
        baseline_stats = {
            "lidar_distance_m": {"mean": 25.0, "std": 10.0},
            "radar_velocity_kmh": {"mean": -20.0, "std": 15.0}
        }
        """
        self.baseline = baseline_stats
        self.recent_events: List[PredictionEvent] = []
        self.window_size = 10  # Evaluate drift every 10 events for simulation

    def observe(self, event: PredictionEvent) -> ModelDegradedEvent | None:
        self.recent_events.append(event)

        if len(self.recent_events) >= self.window_size:
            degraded_event = self.evaluate_drift()
            self.recent_events.clear()
            return degraded_event
        return None

    def evaluate_drift(self) -> ModelDegradedEvent | None:
        if not self.recent_events:
            return None

        # Extract features from recent window
        features = {"lidar_distance_m": [], "radar_velocity_kmh": []}
        for event in self.recent_events:
            for f in features.keys():
                if f in event.features:
                    features[f].append(event.features[f])

        # Compare with baseline
        for feature_name, values in features.items():
            if not values:
                continue

            current_mean = np.mean(values)
            baseline_mean = self.baseline.get(feature_name, {}).get("mean", 0.0)
            baseline_std = self.baseline.get(feature_name, {}).get("std", 1.0)

            # Simple Z-score logic for Drift (Drift if |Z| > 3.0)
            # In real life, we would use KS-test or PSI (Population Stability Index)
            z_score = abs((current_mean - baseline_mean) / (baseline_std + 1e-9))

            if z_score > 3.0:
                print(f"🚨 DRIFT DETECTED on {feature_name}! Z-Score: {z_score:.2f}")
                return ModelDegradedEvent(
                    model_version_id=self.recent_events[-1].model_version_id,
                    drift_score=float(z_score),
                    feature_name=feature_name,
                    reason=f"Significant distribution shift on {feature_name} (Z-Score > 3)",
                )
        return None


# Singleton Drift Monitor
# Fake baseline for the BAAC Lidar/Radar dataset
BAAC_BASELINE = {
    "lidar_distance_m": {"mean": 30.0, "std": 15.0},
    "radar_velocity_kmh": {"mean": -30.0, "std": 20.0},
}
monitor = DriftMonitor(baseline_stats=BAAC_BASELINE)


def get_drift_monitor() -> DriftMonitor:
    return monitor
