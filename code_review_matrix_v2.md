# Matrice de Code Review (Opérationnelle)

Ce document trace l'audit *ligne par ligne* des fichiers du projet pour purger les failles P1 et P2 (résilience, logs, exceptions, typage, timeout, rate-limits, sécurité).

| Fichier | Domaine | Checklist P1/P2 | Statut |
| :--- | :--- | :--- | :--- |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `agentic-ops-core/...` | agentic-ops-core | Least privilege, Tool boundaries, Exception swallowing | ✅ **Traité** (Least Privilege Sandboxing en place, Retry LLM Tenacity ajoutés) |
| `app/api/datasets.py` | app | Timeouts, Rate-limiting, Async/Await blocking | 🗑️ **Supprimé** (Dead code) |
| `app/api/executions.py` | app | Timeouts, Rate-limiting, Async/Await blocking | 🗑️ **Supprimé** (Dead code) |
| `app/api/inference.py` | app | Timeouts, Rate-limiting, Async/Await blocking | 🗑️ **Supprimé** (Dead code) |
| `app/dashboard.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/domain/baac_schema.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/domain/entities.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/domain/events.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/domain/executions/models.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/domain/executions/state/machine.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/domain/observations/models.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/domain/remediation/policy_engine.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/infrastructure/database.py` | app | Connection pooling, Retry backoff, Atomic rollback | ⏳ À faire |
| `app/infrastructure/drift_monitor.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/infrastructure/mlflow_adapter.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/infrastructure/models.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/infrastructure/sre_engine.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/main.py` | app | Timeouts, Rate-limiting, Async/Await blocking | ✅ **Traité** (Timeouts ajoutés, DB URL sécurisée, Exception handling OS ajouté) |
| `app/serving/model_loader.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/workflows/baac_chaos_simulation.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/workflows/baac_drift_simulation.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/workflows/baac_serving_simulation.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/workflows/baac_simulation.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/workflows/baac_sre_simulation.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `app/workflows/baac_training_dag.py` | app | Typage strict, Error handling générique | ⏳ À faire |
| `scripts/agentic_flow.py` | scripts | Typage strict, Error handling générique | ⏳ À faire |
| `scripts/batch_shap.py` | scripts | Typage strict, Error handling générique | ⏳ À faire |
| `scripts/batch_zones.py` | scripts | Typage strict, Error handling générique | ⏳ À faire |
| `scripts/generate_calendar_seed.py` | scripts | Typage strict, Error handling générique | ⏳ À faire |
| `scripts/generate_synthetic_baac.py` | scripts | Typage strict, Error handling générique | ⏳ À faire |
| `scripts/load_to_postgres.py` | scripts | Connection pooling, Retry backoff, Atomic rollback | ✅ **Traité** (CASCADE retiré, credentials passés en ENV) |
| `scripts/run_drift_analysis.py` | scripts | Typage strict, Error handling générique | ⏳ À faire |
| `scripts/run_pipeline.py` | scripts | Typage strict, Error handling générique | ⏳ À faire |
| `src/agentic_client/baac/observability.py` | src | Typage strict, Error handling générique | ⏳ À faire |
| `src/agentic_client/infra/observability.py` | src | Typage strict, Error handling générique | ⏳ À faire |
| `src/agentic_client/mlflow/observability.py` | src | Typage strict, Error handling générique | ⏳ À faire |
| `src/data/contracts.py` | src | Typage strict, Error handling générique | ⏳ À faire |
| `src/data/harmonizer.py` | src | Typage strict, Error handling générique | ⏳ À faire |
| `src/features/build_features.py` | src | Time-aware joins, NaN handling | ✅ **Traité** (Time-Aware Joins Shift(1) réparés, NaNs gérés) |
| `src/features/calendar_utils.py` | src | Time-aware joins, NaN handling | ⏳ À faire |
| `src/models/drift_monitor.py` | src | Lineage tags complets, Seed fixation | ⏳ À faire |
| `src/models/sre_engine.py` | src | Lineage tags complets, Seed fixation | ⏳ À faire |
| `src/models/train_famille.py` | src | Lineage tags complets, Seed fixation | ✅ **Traité** (Lineage total, Fixation Seeds, Protection split) |
| `src/models/train_famille_A.py` | src | Lineage tags complets, Seed fixation | ✅ **Traité** (Lineage total, Fixation Seeds, Protection split) |
| `src/warehouse/load_to_postgres.py` | src | Connection pooling, Retry backoff, Atomic rollback | ⏳ À faire |
