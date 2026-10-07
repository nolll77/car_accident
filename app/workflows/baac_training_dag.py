import random
import time
from sklearn.ensemble import RandomForestRegressor
from app.infrastructure.mlflow_adapter import MLflowAdapter
from app.domain.executions.models import ExecutionStatus
from app.domain.executions.state.machine import transition


def run_baac_training_dag():
    print("=== Démarrage du DAG d'entraînement BAAC ===")

    # 1. State Machine: Transition to RUNNING
    current_state = ExecutionStatus.QUEUED
    current_state = transition(current_state, ExecutionStatus.RUNNING)
    print(f"[DAG Engine] Status transition to: {current_state}")

    # 2. Simulation de la préparation des données
    print("\n[DataOps] Préparation du Dataset Lidar/Radar fusionné...")
    time.sleep(1)

    # 3. Entraînement du Modèle
    print(
        "\n[MLOps] Entraînement du modèle RandomForest pour l'évitement (Freinage)..."
    )
    # Synthetic data: X = [lidar_distance_m, radar_velocity_kmh]
    X_train = [[15.0, -30.0], [5.0, -50.0], [25.0, -10.0], [2.0, -60.0]]
    # y = brake_pressure_bar (target)
    y_train = [10.0, 45.0, 0.0, 60.0]

    model = RandomForestRegressor(n_estimators=10, max_depth=3)
    model.fit(X_train, y_train)

    # Synthetic metrics
    metrics = {"mse": random.uniform(1.0, 5.0), "r2_score": random.uniform(0.85, 0.99)}
    params = {
        "n_estimators": 10,
        "max_depth": 3,
        "dataset_id": "7870e850-a2b2-4295-bd6a-d594b03d77a5",
    }
    print(f"✅ Entraînement terminé. Métriques: {metrics}")

    # 4. MLflow Tracking & Registry
    print("\n[MLflow] Enregistrement du modèle et des artefacts...")
    mlflow_adapter = MLflowAdapter()
    run_id = mlflow_adapter.log_training_run(
        experiment_name="baac-avoidance-model",
        run_name="rf-baseline",
        params=params,
        metrics=metrics,
        model=model,
    )
    print(f"✅ Modèle loggé avec run_id: {run_id}")

    version = mlflow_adapter.register_model(run_id, "baac-braking-controller")
    print(f"✅ Modèle enregistré dans le Model Registry. Version: {version}")

    # 5. State Machine: Transition to SUCCEEDED
    current_state = transition(current_state, ExecutionStatus.SUCCEEDED)
    print(f"\n[DAG Engine] Status transition to: {current_state}")

    print("\n=== Workflow complété avec succès ! ===")


if __name__ == "__main__":
    run_baac_training_dag()
