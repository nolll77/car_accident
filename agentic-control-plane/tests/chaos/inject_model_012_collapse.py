from tests.chaos.base_injector import BaseChaosInjector


class ModelCollapseInjector(BaseChaosInjector):
    def __init__(self):
        super().__init__(name="model_012_collapse", expected_risk_id="MODEL-012")

    def inject(self) -> dict:
        # Simulation d'une chute brutale de F1-score
        return {
            "signal_id": "model_performance_drop",
            "value": 0.65,  # < 0.85 threshold (supposons qu'un signal breached est géré par la condition de l'orchestrator ou de l'alerte)
            "threshold": 0.85,
            "dimensions": ["f1_score", "class_1"],
        }


if __name__ == "__main__":
    injector = ModelCollapseInjector()
    print(injector.get_signal_dict())
