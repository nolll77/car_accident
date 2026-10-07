import os
import mlflow
import mlflow.sklearn
from typing import Dict, Any, Optional


class MLflowAdapter:
    def __init__(self):
        # Fallback to local sqlite if MLFLOW_TRACKING_URI is not set
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
        mlflow.set_tracking_uri(self.tracking_uri)

    def log_training_run(
        self,
        experiment_name: str,
        run_name: str,
        params: Dict[str, Any],
        metrics: Dict[str, float],
        model: Any = None,
    ) -> str:
        """
        Logs parameters, metrics and optionally a scikit-learn model to MLflow.
        Returns the MLflow run_id.
        """
        mlflow.set_experiment(experiment_name)

        with mlflow.start_run(run_name=run_name) as run:
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)

            if model:
                # Assuming scikit-learn model for BAAC v0.1
                mlflow.sklearn.log_model(model, "model")

            return run.info.run_id

    def register_model(self, run_id: str, model_name: str) -> Optional[str]:
        """
        Registers a logged model to the MLflow Model Registry.
        Returns the model version.
        """
        model_uri = f"runs:/{run_id}/model"
        try:
            mv = mlflow.register_model(model_uri, model_name)
            return mv.version
        except Exception as e:
            print(f"Failed to register model: {e}")
            return None
