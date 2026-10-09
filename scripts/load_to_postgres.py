import pandas as pd
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    import os

    db_url = os.environ.get(
        "DATABASE_URL_LOCAL", "postgresql://mlops:mock@localhost:5432/mlops_db"
    )
    engine = create_engine(db_url)

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
        # [ALERTE MLOPS] P1: Suppression du DROP TABLE CASCADE dangereux
        with engine.begin() as conn:
            from sqlalchemy import text

            # 1. On supprime l'ancienne table de backup (sans cascade)
            conn.execute(text(f"DROP TABLE IF EXISTS {old_table}"))
            # 2. On renomme la prod actuelle vers le backup
            conn.execute(
                text(f"ALTER TABLE IF EXISTS {pg_table} RENAME TO {old_table}")
            )
            # 3. On promeut le staging en prod
            conn.execute(text(f"ALTER TABLE {staging_table} RENAME TO {pg_table}"))

        logger.info(f"Swap atomique réussi pour {pg_table}: {len(df)} lignes promues.")


if __name__ == "__main__":
    main()
