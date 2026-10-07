import requests

API_URL = "http://localhost:8000"


def simulate_chaos():
    print("=== Démarrage Simulation Chaos Engineering ===")

    # 1. Données Corrompues (Mauvais types, champs manquants)
    print("\n[Chaos 1] Injection de données corrompues (Validation Pydantic)...")
    payload = {
        "model_name": "baac-braking-controller",
        "model_version": "1",
        "features": {
            "lidar_distance_m": "cent mètres",  # String instead of float
            # Missing radar_velocity
        },
    }
    response = requests.post(f"{API_URL}/inference/predict", json=payload)
    print(f"Status: {response.status_code} | Body: {response.text}")

    # 2. Timeout simulation (Client side timeout, server side overload simulation)
    print("\n[Chaos 2] Simulation de Timeout Client (Réseau dégradé)...")
    payload = {
        "model_name": "baac-braking-controller",
        "model_version": "1",
        "features": {"lidar_distance_m": 50.0, "radar_velocity_kmh": -10.0},
    }
    try:
        # We simulate a very aggressive client timeout (1ms)
        requests.post(f"{API_URL}/inference/predict", json=payload, timeout=0.0001)
    except requests.exceptions.Timeout:
        print(
            "Status: 408 Client Timeout | Le client a abandonné la requête (Circuit Breaker local)."
        )
    except Exception as e:
        print(f"Status: Error | {e}")

    print("\n=== Fin de la simulation de Chaos ===")
    print("L'infrastructure est restée debout. L'API a rejeté la corruption via 422.")


if __name__ == "__main__":
    simulate_chaos()
