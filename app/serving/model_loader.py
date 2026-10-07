import mlflow
import os


class ModelServingEngine:
    def __init__(self):
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
        mlflow.set_tracking_uri(self.tracking_uri)
        self.models = {}

    def load_model(self, model_name: str, version: str = "latest"):
        """Loads a model from MLflow registry into memory for serving."""
        model_uri = f"models:/{model_name}/{version}"
        if model_uri not in self.models:
            print(f"[Serving Engine] Loading model from {model_uri}...")
            # For this MVP, we load the scikit-learn model
            self.models[model_uri] = mlflow.sklearn.load_model(model_uri)
        return self.models[model_uri]

    def predict(self, model_name: str, version: str, features: list):
        model = self.load_model(model_name, version)
        # Model expects a 2D array, so we wrap features
        prediction = model.predict([features])
        return prediction[0]


engine = ModelServingEngine()


def get_serving_engine() -> ModelServingEngine:
    return engine
