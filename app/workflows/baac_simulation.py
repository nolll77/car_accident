import requests
import time
from app.domain.baac_schema import BaacSensorData

API_URL = "http://localhost:8000"


def simulate_workflow():
    print("=== Démarrage du Workflow MLOps BAAC ===")

    # 1. Enregistrement du Dataset
    print("\n[1] Enregistrement du Dataset Lidar/Radar dans le Control Plane...")
    payload = {
        "namespace": "baac-sensors",
        "name": "lidar-radar-fusion-v1",
        "owner": "equipe-perception",
        "metadata": {
            "sensor_types": ["LIDAR", "RADAR"],
            "resolution": "high",
            "schema_contract": "BaacSensorData",
        },
    }

    response = requests.post(f"{API_URL}/datasets", json=payload)
    if response.status_code == 201:
        dataset = response.json()
        print(f"✅ Dataset enregistré avec succès ! ID: {dataset['id']}")
    else:
        print(f"❌ Erreur: {response.text}")
        return

    # 2. Validation de contrat de données local (Data Quality Gate)
    print("\n[2] Passage de la Data Quality Gate (Validation Pydantic)...")
    try:
        sample = BaacSensorData(
            timestamp=time.time(),
            lidar_distance_m=15.0,
            radar_velocity_kmh=-20.0,
            brake_pressure_bar=10.0,
        )
        sample.validate_safety_invariant()
        print(
            "✅ Contrat de données BAAC respecté (Aucun invariant violé sur l'échantillon de test)."
        )
    except ValueError as e:
        print(f"❌ Violation du contrat : {e}")

    print("\n=== Workflow complété avec succès ! ===")


if __name__ == "__main__":
    simulate_workflow()
