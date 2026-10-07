"""
EvidenceStore append-only. Aucune dépendance externe.
_index.json fait le lien dedup_key -> episode_id pour l'idempotence.
"""

from __future__ import annotations

import json
from pathlib import Path

from agentic.core.contracts import Episode


class EvidenceStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "_index.json"
        if not self.index_path.exists():
            self.index_path.write_text("{}", encoding="utf-8")

    def _load_index(self) -> dict[str, str]:
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def _save_index(self, index: dict[str, str]) -> None:
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def find_existing_episode(self, dedup_key: str) -> str | None:
        return self._load_index().get(dedup_key)

    def next_episode_id(self) -> str:
        existing = list(self.root.glob("EP-*.json"))
        return f"EP-{len(existing) + 1:04d}"

    def save(self, episode: Episode) -> Path:
        path = self.root / f"{episode.episode_id}.json"
        path.write_text(
            json.dumps(episode.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        index = self._load_index()
        index[episode.dedup_key] = episode.episode_id
        self._save_index(index)
        return path
