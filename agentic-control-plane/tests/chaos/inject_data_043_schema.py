from tests.chaos.base_injector import BaseChaosInjector


class SchemaCorruptionInjector(BaseChaosInjector):
    def __init__(self):
        super().__init__(name="data_043_schema", expected_risk_id="DATA-043")

    def inject(self) -> dict:
        # Simulation d'une colonne manquante 'secu1' dans la table usagers
        return {
            "signal_id": "schema_corruption",
            "value": 1.0,  # 1 = missing, 0 = present
            "threshold": 0.0,
            "dimensions": ["secu1", "table_usagers"],
        }


if __name__ == "__main__":
    injector = SchemaCorruptionInjector()
    print(injector.get_signal_dict())
