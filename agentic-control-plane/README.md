# Agentic Control Plane — Milestone M0

Sqeuelette déterministe (sans LLM) du Control Plane MLOps.

## Principe

> **LLM = proposition. Code déterministe = décision, autorisation, exécution.**

Le Core ne connaît jamais BAAC, Evidently, MLflow, Postgres, GitHub ou Prefect.
Il ne connaît que des **contrats** (objets typés) et des **protocoles**.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Démo complète
python demo.py DATA-042

# Démo avec action forcée
python demo.py DATA-042 --action deploy_prod

# Test de substitution d'adapter
python demo.py test-adapter fake

# Suite de tests
pytest -v
```

## Architecture

- `agentic/core/` — Contrats, PolicyEngine, StateMachine, EvidenceStore (zéro dépendance provider)
- `agentic/runtime/` — Orchestrator, Specialist, Executor (zéro dépendance provider)
- `agentic/adapters/` — Adapters concrets (BAAC, Fake) qui implémentent le Protocol
- `governance/` — Risk Register et Autonomy Policy (YAML)
- `schemas/` — JSON Schemas de validation
- `tests/` — Suite pytest incluant un test d'invariant architecturale (AST)
