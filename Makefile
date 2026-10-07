.PHONY: help infra-up infra-down install pipeline data-repro dbt-run features train serve drift batch-shap batch-zones

help:
	@echo "🚗 BAAC MLOps - Commandes Disponibles"
	@echo "-------------------------------------------------"
	@echo "Infrastructure:"
	@echo "  make infra-up      - Démarre tous les services Docker (Postgres, MLflow, Superset, etc.)"
	@echo "  make infra-down    - Arrête tous les services Docker"
	@echo ""
	@echo "Développement:"
	@echo "  make install       - Installe les dépendances via uv et configure les hooks"
	@echo ""
	@echo "Pipeline MLOps:"
	@echo "  make pipeline      - Lance le pipeline complet Prefect (DVC -> dbt -> Feast -> Train -> Batches)"
	@echo "  make data-repro    - Lance uniquement le DAG de données DVC (Génération & Harmonisation)"
	@echo "  make dbt-run       - Exécute les transformations dbt dans le Data Warehouse"
	@echo "  make features      - Applique les définitions Feast (feast apply)"
	@echo "  make train         - Entraîne les modèles Famille A, B, C et log dans MLflow"
	@echo ""
	@echo "Serving & Monitoring:"
	@echo "  make serve         - Lance l'API FastAPI en local (port 8000)"
	@echo "  make drift         - Lance l'analyse de dérive Evidently AI"
	@echo "  make batch-shap    - Calcule l'importance globale des features (SHAP)"
	@echo "  make batch-zones   - Agrège les risques par zone géographique pour Superset"

infra-up:
	docker-compose up -d

infra-down:
	docker-compose down

install:
	uv sync
	.venv/bin/pre-commit install

pipeline:
	.venv/bin/python scripts/run_pipeline.py

data-repro:
	.venv/bin/dvc repro

dbt-run:
	cd dbt_warehouse && dbt build

features:
	cd feature_repo && feast apply

train:
	export MLFLOW_S3_ENDPOINT_URL=http://localhost:9000 && \
	export AWS_ACCESS_KEY_ID=minioadmin && \
	export AWS_SECRET_ACCESS_KEY=minioadminpassword && \
	.venv/bin/python src/models/train_famille.py

serve:
	.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

drift:
	.venv/bin/python scripts/run_drift_analysis.py

batch-shap:
	.venv/bin/python scripts/batch_shap.py

batch-zones:
	.venv/bin/python scripts/batch_zones.py
