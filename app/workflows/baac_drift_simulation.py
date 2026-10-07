import requests
import time
import random

API_URL = "http://localhost:8000"


def simulate_drift():
    print("=== Démarrage Simulation Data Drift ===")
    print("Envoi de 10 requêtes avec des données capteurs totalement décalées...")
    print("Lidar attendu: ~30m. On envoie: ~100m (Autoroute rapide et vide)")

    for i in range(15):
        payload = {
            "model_name": "baac-braking-controller",
            "model_version": "1",
            "features": {
                # Huge drift on Lidar (Baseline mean is 30, std 15. We send 100+)
                "lidar_distance_m": random.uniform(90.0, 110.0),
                "radar_velocity_kmh": random.uniform(-30.0, 0.0),
            },
        }

        try:
            response = requests.post(f"{API_URL}/inference/predict", json=payload)
            if response.status_code == 200:
                print(
                    f"[{i+1}] Req OK -> Prédiction: {response.json()['prediction']:.2f} bars"
                )
            else:
                print(f"[{i+1}] Erreur API: {response.status_code}")
        except Exception as e:
            print(f"Erreur de connexion : {e}")

        time.sleep(0.2)

    print("\n=== Fin Simulation ===")
    print(
        "Vérifiez les logs de l'API (uvicorn) pour voir l'événement 🔥 ModelDegradedEvent (Drift)."
    )


if __name__ == "__main__":
    simulate_drift()
