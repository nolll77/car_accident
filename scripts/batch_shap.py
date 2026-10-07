import os
import pandas as pd
from sqlalchemy import create_engine
import mlflow
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("batch_shap")

os.environ["MLFLOW_S3_ENDPOINT_URL"] = "http://localhost:9000"
os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadminpassword"


def run_shap_batch():
    logger.info("Starting Global Explainer Batch (Feature Importance)...")

    # Connect to DB
    engine = create_engine("postgresql://mlops:mlops_password@localhost:5432/mlops_db")

    try:
        # 1. Fetch recent data to know the features
        logger.info("Fetching recent data from dbt_baac.features_famille_a...")
        df = pd.read_sql("SELECT * FROM dbt_baac.features_famille_a LIMIT 1", engine)

        _X = df.drop(
            columns=["num_acc", "is_grave", "event_timestamp", "an"], errors="ignore"
        )

        # 2. Fetch the latest production model
        logger.info("Fetching production model Famille_A from MLflow...")
        mlflow.set_tracking_uri("http://localhost:5000")
        client = mlflow.tracking.MlflowClient()

        try:
            model_version = client.get_latest_versions(
                "Famille_A", stages=["Production"]
            )[0]
            model_uri = "models:/Famille_A/Production"
        except IndexError:
            logger.warning("No model in Production stage. Fetching the latest version.")
            model_version = client.get_latest_versions("Famille_A")[0]
            model_uri = f"models:/Famille_A/{model_version.version}"

        model = mlflow.sklearn.load_model(model_uri)

        # 3. Extract Feature Importances
        logger.info("Extracting global feature importance...")
        # Our model is a Pipeline: [preprocessor, classifier]
        classifier = model.named_steps["classifier"]
        importances = classifier.feature_importances_

        # Getting feature names after preprocessing
        preprocessor = model.named_steps["preprocessor"]

        try:
            feature_names = preprocessor.get_feature_names_out()
        except AttributeError:
            # Fallback if scikit-learn version < 1.0 or issues
            feature_names = [f"feature_{i}" for i in range(len(importances))]

        importance_df = pd.DataFrame(
            {
                "feature": feature_names,
                "mean_abs_shap": importances,  # Reusing the column name for Superset compatibility
                "calculated_at": pd.Timestamp.now(),
            }
        ).sort_values("mean_abs_shap", ascending=False)

        # 4. Save to PostgreSQL for Superset
        logger.info("Saving to expl_shap_global table...")
        importance_df.to_sql(
            "expl_shap_global",
            engine,
            schema="public",
            if_exists="replace",
            index=False,
        )

        logger.info("Global Explainer Batch completed successfully.")

    except Exception as e:
        logger.error(f"Error during Explainer batch: {e}")
        raise


if __name__ == "__main__":
    run_shap_batch()
