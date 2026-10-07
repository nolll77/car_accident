import requests
import time
import uuid

API_URL = "http://localhost:8000"


def simulate_serving_workflow():
    print("=== Démarrage du Workflow Serving BAAC ===")

    # Simuler des requêtes entrantes de la voiture (capteurs)
    scenarios = [
        {"desc": "Cas Nominal (loin)", "lidar": 50.0, "radar": -10.0},
        {"desc": "Danger (très proche, rapide)", "lidar": 4.0, "radar": -60.0},
        {"desc": "Suivi normal", "lidar": 20.0, "radar": 0.0},
    ]

    for i, s in enumerate(scenarios):
        print(f"\n[{i+1}] Envoi requête: {s['desc']}")
        payload = {
            "model_name": "baac-braking-controller",
            "model_version": "1",  # Version we just trained
            "features": {
                "lidar_distance_m": s["lidar"],
                "radar_velocity_kmh": s["radar"],
            },
            "trace_id": str(uuid.uuid4()),
        }

        try:
            response = requests.post(f"{API_URL}/inference/predict", json=payload)
            if response.status_code == 200:
                result = response.json()
                print(
                    f"✅ Prédiction (Pression freinage): {result['prediction']:.2f} bars (Latence: {result['latency_ms']:.2f}ms)"
                )
            else:
                print(f"❌ Erreur API: {response.status_code} - {response.text}")
        except requests.exceptions.ConnectionError:
            print(
                "❌ Erreur: Impossible de se connecter à l'API. Le serveur FastAPI tourne-t-il ?"
            )
            return

        time.sleep(0.5)

    print(
        "\n=== Fin de la simulation (Vérifiez les logs serveur pour le Bus d'Événements) ==="
    )


if __name__ == "__main__":
    simulate_serving_workflow()
