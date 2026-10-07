"""
Adaptateur BAAC d'Observabilité — Stratégie A (Lecture Prometheus réelle).

Lit `reports/drift/prometheus_metrics.txt` généré par Evidently AI
pour produire un Signal de dérive réel sur les données BAAC.

Ce fichier remplace le mock statique précédent (value=0.27 hardcodé).
"""

from __future__ import annotations

import re
from pathlib import Path

from agentic.core.contracts import Signal

# Chemin vers le fichier de métriques Prometheus généré par Evidently
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # remonter à car_acc/
_PROMETHEUS_PATH = _PROJECT_ROOT / "reports" / "drift" / "prometheus_metrics.txt"

# Seuils d'alerte
_DRIFT_SHARE_THRESHOLD = 0.30  # > 30% de features en dérive → alerte
_FEATURE_DRIFT_THRESHOLD = 0.20  # Seuil Jensen-Shannon par feature


def _parse_prometheus_file(path: Path) -> dict[str, float]:
    """
    Parse le format Prometheus text exposition.
    Retourne un dict {metric_name_or_label: value}.
    """
    metrics: dict[str, float] = {}
    if not path.exists():
        return metrics

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Ligne avec label ex: mlops_baac_feature_drift_score{feature="an_nais"} 0.394
        label_match = re.match(r'(\w+)\{feature="([^"]+)"\}\s+([\d.e+\-]+)', line)
        if label_match:
            metric, feature, value = label_match.groups()
            metrics[f"{metric}[{feature}]"] = float(value)
            continue
        # Ligne simple ex: mlops_baac_drift_share 0.75
        simple_match = re.match(r"(\w+)\s+([\d.e+\-]+)", line)
        if simple_match:
            metric, value = simple_match.groups()
            metrics[metric] = float(value)

    return metrics


class BAACObservabilityAdapter:
    """
    Adaptateur d'observabilité BAAC — lecture réelle des métriques Evidently.

    Si `prometheus_metrics.txt` est absent (ex: tests unitaires), retombe sur
    le score de simulation passé en argument (fallback_score).
    """

    def __init__(self, fallback_score: float = 0.27):
        self._fallback = fallback_score

    def get_signal(self, signal_id: str) -> Signal:
        if signal_id != "data_drift":
            raise ValueError(f"Signal inconnu pour BAAC : {signal_id!r}")

        metrics = _parse_prometheus_file(_PROMETHEUS_PATH)

        if not metrics:
            # Pas de fichier Prometheus → fallback (tests unitaires, CI sans pipeline)
            return Signal(
                signal_id="data_drift",
                value=self._fallback,
                threshold=_DRIFT_SHARE_THRESHOLD,
                source="baac.evidently.fallback",
                dimensions=("age",),
            )

        drift_share = metrics.get("mlops_baac_drift_share", self._fallback)

        # Collecte des features en dérive réelle (au-dessus du seuil feature)
        drifted = [
            key.replace("mlops_baac_feature_drift_score[", "").rstrip("]")
            for key, val in metrics.items()
            if key.startswith("mlops_baac_feature_drift_score")
            and val > _FEATURE_DRIFT_THRESHOLD
        ]
        # Trier par score descendant pour mettre en avant les features les plus driftées
        feature_scores = {
            key.replace("mlops_baac_feature_drift_score[", "").rstrip("]"): val
            for key, val in metrics.items()
            if key.startswith("mlops_baac_feature_drift_score")
        }
        dimensions = tuple(
            sorted(drifted, key=lambda f: feature_scores.get(f, 0), reverse=True)[:5]
        )

        return Signal(
            signal_id="data_drift",
            value=drift_share,
            threshold=_DRIFT_SHARE_THRESHOLD,
            source="baac.evidently.prometheus",
            dimensions=dimensions,
        )
