"""Script to load harmonized Parquet files into PostgreSQL."""

import pandas as pd
from sqlalchemy import create_engine
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://mlops:mlops_password@localhost:5432/mlops_db"


def load_harmonized_to_postgres() -> None:
    """Load harmonized parquet tables into raw PostgreSQL tables."""
    engine = create_engine(DATABASE_URL)

    tables = {
        "raw_caracteristiques": "data/harmonized/caracteristiques.parquet",
        "raw_lieux": "data/harmonized/lieux.parquet",
        "raw_vehicules": "data/harmonized/vehicules.parquet",
        "raw_usagers": "data/harmonized/usagers.parquet",
    }

    for table_name, parquet_path in tables.items():
        try:
            logger.info(f"Loading {parquet_path} into table {table_name}")
            df = pd.read_parquet(parquet_path)
            df.to_sql(table_name, engine, if_exists="replace", index=False)
            logger.info(f"Loaded {len(df)} rows into {table_name}")
        except Exception as e:
            logger.error(f"Failed to load {table_name} from {parquet_path}: {e}")


if __name__ == "__main__":
    load_harmonized_to_postgres()
