from tests.chaos.base_injector import BaseChaosInjector


class PgSaturationInjector(BaseChaosInjector):
    def __init__(self):
        super().__init__(name="infra_005_pg_saturation", expected_risk_id="INFRA-005")

    def inject(self) -> dict:
        # Simulation d'une saturation de connexions PostgreSQL
        return {
            "signal_id": "postgres_connection_saturation",
            "value": 99.0,  # 99% usage
            "threshold": 90.0,
            "dimensions": ["pg_stat_activity", "pool_active"],
        }


if __name__ == "__main__":
    injector = PgSaturationInjector()
    print(injector.get_signal_dict())
