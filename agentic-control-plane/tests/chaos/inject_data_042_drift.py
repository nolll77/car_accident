from tests.chaos.base_injector import BaseChaosInjector


class DriftInjector(BaseChaosInjector):
    def __init__(self):
        super().__init__(name="data_042_drift", expected_risk_id="DATA-042")

    def inject(self) -> dict:
        # Simulation d'un drift sur la feature "age" (ex: décalage de la moyenne de +15 ans)
        return {
            "signal_id": "data_drift",
            "value": 0.45,  # > 0.20 threshold
            "threshold": 0.20,
            "dimensions": ["age", "an_nais"],
        }


if __name__ == "__main__":
    injector = DriftInjector()
    print(injector.get_signal_dict())
