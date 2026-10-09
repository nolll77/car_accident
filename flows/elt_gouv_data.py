import os
import requests
from prefect import flow, task, get_run_logger
from sqlalchemy import create_engine
import pyarrow.parquet as pq

# We need to add the parent directory to sys.path to import src
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data.harmonizer import BAACHarmonizer


@task(retries=3, retry_delay_seconds=5)
def fetch_2023_urls():
    logger = get_run_logger()
    url = "https://www.data.gouv.fr/api/1/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024/"

    logger.info(f"Fetching dataset info from {url}")
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()

    urls = {}
    for res in data.get("resources", []):
        title = res.get("title", "").lower()
        file_url = res.get("url", "")

        if "2023" in title or "2023.csv" in file_url:
            if "caract" in title:
                urls["caracteristiques"] = file_url
            elif "lieux" in title:
                urls["lieux"] = file_url
            elif "vehicules" in title:
                urls["vehicules"] = file_url
            elif "usagers" in title:
                urls["usagers"] = file_url

    if len(urls) < 4:
        logger.warning(
            f"Did not find all 4 tables for 2023. Found: {list(urls.keys())}"
        )
    else:
        logger.info(f"Successfully found URLs for all 4 tables: {urls}")

    return urls


@task(retries=2, retry_delay_seconds=10)
def download_to_raw(urls: dict):
    logger = get_run_logger()
    os.makedirs("data/raw", exist_ok=True)

    for name, url in urls.items():
        filepath = f"data/raw/{name}.csv"
        logger.info(f"Downloading {name} from {url} to {filepath}...")

        with requests.get(url, stream=True, timeout=20) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

    logger.info("All files downloaded successfully.")


@task
def run_harmonizer():
    logger = get_run_logger()
    logger.info("Running BAACHarmonizer to clean and validate data...")

    harmonizer = BAACHarmonizer(
        raw_dir="data/raw", output_dir="data/harmonized", config_dir="config"
    )
    results = harmonizer.run_full_pipeline()

    tables_processed = list(results.keys())
    logger.info(f"Harmonization complete for {len(tables_processed)} tables.")
    return tables_processed


@task
def load_to_postgres_chunked(tables: list):
    logger = get_run_logger()
    engine = create_engine("postgresql://mlops:mlops_password@localhost:5432/mlops_db")

    for table in tables:
        pg_table = f"raw_{table}"
        parquet_path = f"data/harmonized/{table}.parquet"

        if not os.path.exists(parquet_path):
            logger.warning(f"File {parquet_path} does not exist, skipping.")
            continue

        logger.info(f"Loading {parquet_path} to {pg_table} in chunks (streaming)...")

        # Drop cascade to avoid dbt view locks
        with engine.begin() as conn:
            from sqlalchemy import text

            conn.execute(text(f"DROP TABLE IF EXISTS {pg_table}"))

        parquet_file = pq.ParquetFile(parquet_path)
        total_rows = 0

        # Streaming chunk by chunk to avoid RAM explosion on millions of rows
        for batch in parquet_file.iter_batches(batch_size=20000):
            df = batch.to_pandas()
            df.columns = [c.lower() for c in df.columns]
            df.to_sql(pg_table, engine, if_exists="append", index=False)
            total_rows += len(df)

        logger.info(f"Loaded {total_rows} rows into {pg_table}")


@task
def run_dbt():
    logger = get_run_logger()
    import subprocess

    logger.info("Triggering dbt build...")

    # We use the virtualenv dbt command
    env = os.environ.copy()
    env["PATH"] = f"{os.path.abspath('.venv/bin')}:{env.get('PATH', '')}"

    res = subprocess.run(
        ["dbt", "build"], cwd="dbt_warehouse", capture_output=True, text=True, env=env
    )

    if res.returncode != 0:
        logger.error(
            f"❌ dbt build failed!\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )
        raise RuntimeError("dbt build failed")
    else:
        logger.info("✅ dbt build successful.")


@flow(
    name="ELT_Gouv_Data_Pipeline",
    description="Extract data.gouv.fr, Harmonize, Load chunked to Postgres, Transform via dbt",
)
def elt_flow():
    urls = fetch_2023_urls()
    download_to_raw(urls)
    tables = run_harmonizer()
    load_to_postgres_chunked(tables)
    run_dbt()


if __name__ == "__main__":
    elt_flow()
