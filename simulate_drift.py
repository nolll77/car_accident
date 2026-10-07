"""
Simulation SRE : Injection de Data Drift.
Ce script pollue les logs de production avec des profils aberrants
pour forcer le SRE Engine à déclencher un ré-entraînement.
"""

import pandas as pd
import os
from src.models.sre_engine import ContinuousTrainingEngine


def inject_drift():
    log_dir = "data/production_logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "shadow_log.csv")

    # Création de données totalement en dehors de la distribution d'entraînement
    # On simule soudainement une immense vague d'usagers nés en 1920 (très âgés)
    drift_data = pd.DataFrame(
        {
            "usager_id": [f"drift_{i}" for i in range(500)],
            "place": [1] * 500,
            "catu": [2] * 500,
            "sexe": [1] * 500,
            "an_nais": [1920] * 500,  # Dérive massive (au lieu de ~1985)
            "is_metropole": [True] * 500,
            "is_motorise": [True] * 500,
            "predicted_gravity": [4] * 500,
            "timestamp": pd.to_datetime("now"),
        }
    )

    # Injection dans le Shadow Log
    print("😈 Injection de Data Drift dans la production...")
    drift_data.to_csv(
        log_file, mode="a", header=not os.path.exists(log_file), index=False
    )
    print(f"500 lignes aberrantes (Année Naissance: 1920) écrites dans {log_file}")


def test_sre_reaction():
    print("\n🛡️ Démarrage de la boucle SRE...")
    engine = ContinuousTrainingEngine()
    engine.run_sre_loop()


if __name__ == "__main__":
    inject_drift()
    test_sre_reaction()
