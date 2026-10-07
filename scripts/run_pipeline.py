import os
import sys
import subprocess
import logging
from pathlib import Path
from prefect import task, flow, get_run_logger

# Configure logging fallback
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)


@task
def run_script_task(script_path: str, cwd: str, task_name: str, is_dvc: bool = False):
    logger = get_run_logger()
    logger.info(f"Running {task_name} via {script_path}...")

    if is_dvc:
        cmd = [script_path, "repro"]
    else:
        # ensure we use the current python executable (the venv one)
        cmd = [sys.executable, script_path]

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent.absolute())

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)

    if result.returncode != 0:
        logger.error(
            f"❌ Error running {task_name}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        raise RuntimeError(f"Task {task_name} failed with code {result.returncode}")
    else:
        logger.info(f"✅ Successfully ran {task_name}")


@task
def run_dbt_task(dbt_dir: str):
    logger = get_run_logger()
    logger.info(f"Running dbt build in {dbt_dir}...")

    # Dbt needs to be run from the dbt virtual environment if it is installed there,
    # but here we use the global command assuming dbt-postgres is installed.
    # Actually, we can run `dbt build` via subprocess using bash and the activated venv.
    env = os.environ.copy()

    result = subprocess.run(
        ["dbt", "build"], cwd=dbt_dir, capture_output=True, text=True, env=env
    )

    if result.returncode != 0:
        logger.error(
            f"❌ Error running dbt build\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        raise RuntimeError(f"dbt build failed with code {result.returncode}")
    else:
        logger.info("✅ Successfully ran dbt build")


@flow(name="MLOps_End_to_End_Pipeline")
def baac_mlops_pipeline():
    logger = get_run_logger()
    base_dir = Path(__file__).parent.parent.absolute()

    logger.info("🚀 Starting BAAC MLOps Pipeline...")

    # 1. Run DVC Pipeline (Generates data and harmonizes it, taking advantage of caching)
    run_script_task(
        script_path=str(base_dir / ".venv" / "bin" / "dvc"),
        cwd=str(base_dir),
        task_name="DVC Pipeline (Data Gen & Harmonization)",
        is_dvc=True,
    )

    # 2. Load to Postgres
    run_script_task(
        script_path=str(base_dir / "scripts" / "load_to_postgres.py"),
        cwd=str(base_dir),
        task_name="Postgres Loading",
    )

    # 4. Run dbt build
    run_dbt_task(dbt_dir=str(base_dir / "dbt_warehouse"))

    # 5. Train models
    run_script_task(
        script_path=str(base_dir / "src" / "models" / "train_famille.py"),
        cwd=str(base_dir),
        task_name="Model Training (Families A, B, C)",
    )

    # 6. Run Explainability Batches (SHAP & Zones)
    run_script_task(
        script_path=str(base_dir / "scripts" / "batch_shap.py"),
        cwd=str(base_dir),
        task_name="Global SHAP Explainer Batch",
    )

    run_script_task(
        script_path=str(base_dir / "scripts" / "batch_zones.py"),
        cwd=str(base_dir),
        task_name="Geographic Zones Explainer Batch",
    )

    logger.info("🎉 PIPELINE COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    baac_mlops_pipeline()
