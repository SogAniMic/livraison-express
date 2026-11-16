"""`ModelRepository` sur le système de fichiers (ADR-0000, option A : répertoire local).

Écrit quatre fichiers cohérents dans le répertoire de `MODEL_PATH` :
le `.joblib`, `metrics.json`, `features.json` (cellule 41 du notebook) et
`model_card.json` (cellule 55). L'écriture passe par un fichier temporaire puis un
renommage atomique : l'API ne lit jamais un modèle à moitié écrit.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import joblib

from ....domain.entities import ModelEntity
from ...model_repository import ModelRepository

logger = logging.getLogger(__name__)


class FileModelRepository(ModelRepository):
    def __init__(self, model_path: str):
        self._model_path = Path(model_path)
        self._card_path = self._model_path.parent / "model_card.json"

    def save(self, model: object, model_card: ModelEntity) -> None:
        directory = self._model_path.parent
        directory.mkdir(parents=True, exist_ok=True)
        card = asdict(model_card)
        card["trained_at"] = model_card.trained_at.isoformat() if model_card.trained_at else None

        write = self._atomic_write_text
        write(directory / "metrics.json", json.dumps(model_card.metrics, indent=2))
        write(directory / "features.json", json.dumps(model_card.features, indent=2))
        self._atomic_write_text(self._card_path, json.dumps(card, indent=2, ensure_ascii=False))
        tmp_model = self._model_path.with_suffix(".tmp")
        joblib.dump(model, tmp_model)
        os.replace(tmp_model, self._model_path)  # en dernier : marque la nouvelle révision
        logger.info("Modèle sauvegardé (%s)", self._model_path)

    def load(self) -> tuple[object, ModelEntity] | None:
        if not self._model_path.exists() or not self._card_path.exists():
            return None
        model = joblib.load(self._model_path)
        raw = json.loads(self._card_path.read_text(encoding="utf-8"))
        if raw.get("trained_at"):
            raw["trained_at"] = datetime.fromisoformat(raw["trained_at"])
        logger.info("Modèle chargé depuis %s", self._model_path)
        return model, ModelEntity(**raw)

    def revision(self) -> str | None:
        try:
            stat = self._model_path.stat()
        except FileNotFoundError:
            return None
        return f"{stat.st_mtime_ns}-{stat.st_size}"

    @staticmethod
    def _atomic_write_text(path: Path, content: str) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
