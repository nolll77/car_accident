import requests
import random

API_URL = "http://localhost:8000"


def simulate_sre_traffic():
    print("=== Démarrage Simulation SRE (Traffic Metrics) ===")

    # 1. Générer du trafic
    for i in range(10):
        payload = {
            "model_name": "baac-braking-controller",
            "model_version": "1",
            "features": {
                "lidar_distance_m": random.uniform(5.0, 100.0),
                "radar_velocity_kmh": random.uniform(-100.0, 0.0),
            },
        }

        # Inject occasional errors to see 500 status codes (e.g. missing fields)
        if i == 5:
            payload = {"model_name": "unknown"}

        try:
            requests.post(f"{API_URL}/inference/predict", json=payload)
        except Exception as e:
            print(f"Erreur de connexion : {e}")

    # 2. Lire les métriques Prometheus
    print("\n=== Fetching Prometheus Metrics (/metrics) ===")
    try:
        response = requests.get(f"{API_URL}/metrics")
        lines = response.text.split("\n")

        print("\n[SLI] Total Requests:")
        for line in lines:
            if "http_requests_total" in line and not line.startswith("#"):
                print("  " + line)

        print("\n[SLI] Latency Buckets (p99 tracking):")
        for line in lines:
            if "http_request_latency_seconds_bucket" in line:
                print("  " + line)

    except Exception as e:
        print(f"Erreur lors du fetch des métriques: {e}")


if __name__ == "__main__":
    simulate_sre_traffic()
