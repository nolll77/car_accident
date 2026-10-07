import pandas as pd
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    engine = create_engine("postgresql://mlops:mlops_password@localhost:5432/mlops_db")

    tables = {
        "caracteristiques": "raw_caracteristiques",
        "lieux": "raw_lieux",
        "vehicules": "raw_vehicules",
        "usagers": "raw_usagers",
    }

    for parquet_name, pg_table in tables.items():
        logger.info(f"Loading {parquet_name} to {pg_table}...")
        df = pd.read_parquet(f"data/harmonized/{parquet_name}.parquet")
        df.columns = [c.lower() for c in df.columns]

        # Drop table cascade so dbt views don't block
        with engine.connect() as conn:
            from sqlalchemy import text

            conn.execute(text(f"DROP TABLE IF EXISTS {pg_table} CASCADE"))
            conn.commit()

        # Write to postgres, replace if exists
        df.to_sql(pg_table, engine, if_exists="replace", index=False)
        logger.info(f"Loaded {len(df)} rows into {pg_table}")


if __name__ == "__main__":
    main()
