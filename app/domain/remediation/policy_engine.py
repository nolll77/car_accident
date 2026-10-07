import requests
from datetime import datetime

from app.domain.observations.models import ModelDegradedEvent


class PolicyEngine:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.last_retrain_time = None
        self.cooldown_seconds = (
            60  # Anti-flapping: don't retrain more than once a minute
        )

    def evaluate(self, event: ModelDegradedEvent) -> bool:
        print(f"[Policy Engine] Evaluating degradation event: {event.reason}")

        # 1. Cooldown Check
        if self.last_retrain_time:
            delta = (datetime.utcnow() - self.last_retrain_time).total_seconds()
            if delta < self.cooldown_seconds:
                print(
                    f"[Policy Engine] ❌ Denied: Cooldown active ({(self.cooldown_seconds - delta):.0f}s left)."
                )
                return False

        # 2. Threshold Check (Already checked by DriftMonitor, but policy can override)
        if event.drift_score > 3.0:
            print(
                "[Policy Engine] ✅ Approved: Drift score is critical. Triggering Remediation."
            )
            self.trigger_retraining()
            self.last_retrain_time = datetime.utcnow()
            return True

        print("[Policy Engine] ❌ Denied: Drift score below policy threshold.")
        return False

    def trigger_retraining(self):
        """Triggers the 'Forward Flow' DAG via the Platform API."""
        print("[Policy Engine] 🔄 Triggering Autonomous Retraining DAG...")

        payload = {
            "type": "baac_training_dag",
            "input_data": {
                "trigger_source": "autonomous_remediation",
                "reason": "data_drift",
            },
        }

        try:
            response = requests.post(f"{self.api_url}/executions/", json=payload)
            if response.status_code == 201:
                print(
                    f"[Policy Engine] ✅ DAG Triggered! Execution ID: {response.json()['id']}"
                )
            else:
                print(
                    f"[Policy Engine] ❌ Failed to trigger DAG: {response.status_code} - {response.text}"
                )
        except Exception as e:
            print(f"[Policy Engine] ❌ Connection error when triggering DAG: {e}")


policy_engine = PolicyEngine()


def get_policy_engine() -> PolicyEngine:
    return policy_engine
