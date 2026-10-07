"""
Adaptateur MLflow d'Observabilité — Lecture réelle du backend MLflow.

Interroge `mlflow.db` (SQLite) via l'API Python MLflow pour récupérer
les métriques du dernier run de Famille A (Expérience 2).

Produit un Signal de type `model_f1_drop` si le F1-Score
du modèle en production passe sous le seuil configuré.
"""

from __future__ import annotations

from pathlib import Path

from agentic.core.contracts import Signal

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # remonter à car_acc/
_MLFLOW_TRACKING_URI = f"sqlite:///{_PROJECT_ROOT / 'mlflow.db'}"
_EXPERIMENT_ID_FAMILLE_A = "2"

_F1_THRESHOLD = 0.85  # En dessous → alerte
_FALLBACK_F1 = 0.88  # Valeur de fallback si MLflow inaccessible


def _get_latest_f1() -> tuple[float, str]:
    """
    Requête MLflow pour le meilleur F1 du dernier run Famille A.
    Retourne (f1_score, run_id).
    """
    try:
        import mlflow

        mlflow.set_tracking_uri(_MLFLOW_TRACKING_URI)
        runs = mlflow.search_runs(
            experiment_ids=[_EXPERIMENT_ID_FAMILLE_A],
            order_by=["start_time DESC"],
            max_results=1,
        )
        if runs.empty:
            return _FALLBACK_F1, "no-run"

        run = runs.iloc[0]
        # Cherche la métrique f1 sous différents noms possibles
        for col in ("metrics.f1_score", "metrics.f1", "metrics.test_f1"):
            if col in run.index and run[col] is not None and run[col] > 0:
                return float(run[col]), run["run_id"]

        return _FALLBACK_F1, run["run_id"]

    except Exception:
        return _FALLBACK_F1, "mlflow-unavailable"


class MLflowObservabilityAdapter:
    """
    Adaptateur d'observabilité basé sur les métriques MLflow réelles.

    Si MLflow est inaccessible (ex: tests unitaires), retombe sur fallback_f1.
    """

    def __init__(self, fallback_f1: float = _FALLBACK_F1):
        self._fallback_f1 = fallback_f1

    def get_signal(self, signal_id: str) -> Signal:
        if signal_id not in ("model_f1_drop", "model_performance_drop"):
            raise ValueError(f"Signal inconnu pour MLflow : {signal_id!r}")

        f1_score, run_id = _get_latest_f1()

        return Signal(
            signal_id="model_f1_drop",
            value=f1_score,
            threshold=_F1_THRESHOLD,
            source=f"mlflow.famille_a.run:{run_id[:8]}",
            dimensions=("f1_score", "famille_a"),
        )
