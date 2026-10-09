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

        staging_table = f"{pg_table}_staging"
        old_table = f"{pg_table}_old"

        # Écriture dans le staging
        df.to_sql(staging_table, engine, if_exists="replace", index=False)
        
        # Atomic Swap
        with engine.begin() as conn:
            from sqlalchemy import text
            conn.execute(text(f"DROP TABLE IF EXISTS {old_table} CASCADE"))
            conn.execute(text(f"ALTER TABLE IF EXISTS {pg_table} RENAME TO {old_table}"))
            conn.execute(text(f"ALTER TABLE {staging_table} RENAME TO {pg_table}"))
            
        logger.info(f"Swap atomique réussi pour {pg_table}: {len(df)} lignes promues.")


if __name__ == "__main__":
    main()
