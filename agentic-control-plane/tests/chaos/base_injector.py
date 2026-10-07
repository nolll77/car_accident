class BaseChaosInjector:
    def __init__(self, name: str, expected_risk_id: str):
        self.name = name
        self.expected_risk_id = expected_risk_id

    def inject(self) -> dict:
        """
        Implémente l'injection de chaos.
        Retourne le payload brut du signal simulé.
        """
        raise NotImplementedError

    def get_signal_dict(self) -> dict:
        payload = self.inject()
        payload["source"] = f"chaos.{self.name}"
        return payload
