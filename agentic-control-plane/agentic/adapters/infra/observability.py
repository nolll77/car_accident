"""
Adaptateur Infra d'Observabilité — Fraîcheur du Shadow Log et cohérence DVC.

Vérifie l'état de santé de l'infrastructure de données :
  1. Existence et fraîcheur du `shadow_log.csv` (logs de prédictions production)
  2. Présence des fichiers parquet harmonisés (sortie du pipeline DVC)

Produit un Signal de type `shadow_log_staleness`.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from agentic.core.contracts import Signal

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent  # remonter à car_acc/
_SHADOW_LOG_PATH = _PROJECT_ROOT / "data" / "production_logs" / "shadow_log.csv"
_USAGERS_PARQUET = _PROJECT_ROOT / "data" / "harmonized" / "usagers.parquet"

# Seuils d'alerte
_STALENESS_THRESHOLD_HOURS = 24.0  # Shadow log trop ancien → signal breach
_STALENESS_FALLBACK_HOURS = 0.0  # Si absent → 0 (pas de log = toujours breach)


def _file_age_hours(path: Path) -> float | None:
    """Retourne l'âge du fichier en heures, ou None s'il n'existe pas."""
    if not path.exists():
        return None
    mtime = os.path.getmtime(path)
    return (time.time() - mtime) / 3600.0


class InfraObservabilityAdapter:
    """
    Adaptateur d'observabilité infra — vérifie la fraîcheur du shadow log
    et la disponibilité des artefacts DVC.

    Si le fichier est absent, le signal est en breach par construction
    (on ne peut pas monitorer le drift sans log de production).
    """

    def get_signal(self, signal_id: str) -> Signal:
        if signal_id not in ("shadow_log_staleness", "infra_health"):
            raise ValueError(f"Signal inconnu pour Infra : {signal_id!r}")

        age_hours = _file_age_hours(_SHADOW_LOG_PATH)
        parquet_ok = _USAGERS_PARQUET.exists()

        if age_hours is None:
            # Fichier absent : état critique (value élevée pour breach)
            value = _STALENESS_THRESHOLD_HOURS * 10
            source = "infra.shadow_log.missing"
            dims = ("shadow_log_absent", "no_production_data")
        else:
            value = age_hours
            source = "infra.shadow_log.present"
            dims = (
                f"age_h={age_hours:.1f}",
                "parquet_ok" if parquet_ok else "parquet_missing",
            )

        return Signal(
            signal_id="shadow_log_staleness",
            value=value,
            threshold=_STALENESS_THRESHOLD_HOURS,
            source=source,
            dimensions=dims,
        )
