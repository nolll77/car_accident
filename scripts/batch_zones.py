import pandas as pd
from sqlalchemy import create_engine
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("batch_zones")


def run_zones_batch():
    logger.info("Starting Geographic Zones Explainer Batch...")
    engine = create_engine("postgresql://mlops:mlops_password@localhost:5432/mlops_db")

    try:
        # Fetch recent predictions with their features
        logger.info("Fetching recent shadow logs...")
        df_logs = pd.read_sql(
            "SELECT usager_id, predicted_gravity FROM production_shadow_log", engine
        )

        if df_logs.empty:
            logger.warning("No predictions found in shadow log.")
            return

        df_logs["predicted_gravity"] = pd.to_numeric(
            df_logs["predicted_gravity"], errors="coerce"
        )

        # Extract num_acc from usager_id
        # format is typically NumAcc_NumVeh_Place
        df_logs["num_acc"] = (
            df_logs["usager_id"].astype(str).apply(lambda x: x.split("_")[0])
        )

        logger.info("Fetching geographic data from raw_caracteristiques...")
        df_carac = pd.read_sql("SELECT num_acc, dep FROM raw_caracteristiques", engine)
        df_carac["num_acc"] = df_carac["num_acc"].astype(str)

        logger.info("Joining logs with geographic data...")
        df_merged = pd.merge(df_logs, df_carac, on="num_acc", how="left")

        # Fallback if dep is missing (e.g. synthetic issues)
        df_merged["dep"] = df_merged["dep"].fillna("UNKNOWN")

        # Aggregate by département
        logger.info("Aggregating risk by département...")
        agg_df = (
            df_merged.groupby("dep")
            .agg(
                prediction_count=("usager_id", "count"),
                average_predicted_risk=("predicted_gravity", "mean"),
            )
            .reset_index()
        )

        agg_df["calculated_at"] = pd.Timestamp.now()

        # Save to PostgreSQL
        logger.info("Saving to expl_zones_risk table...")
        agg_df.to_sql(
            "expl_zones_risk", engine, schema="public", if_exists="replace", index=False
        )

        logger.info("Zones Explainer Batch completed successfully.")

    except Exception as e:
        logger.error(f"Error during Zones batch: {e}")
        raise


if __name__ == "__main__":
    run_zones_batch()
