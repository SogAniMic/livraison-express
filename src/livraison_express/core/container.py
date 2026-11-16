"""Racine de composition : assemble configuration, repositories et services ML.

La correction de la séance 1 utilisait un singleton ; il est remplacé par un objet
construit explicitement (`Container.from_settings`) : pas d'état global, et chaque
test peut construire son propre contexte (voir ARCHITECTURE.md, § limites).
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime
from functools import partial

from .. import SERVICE_NAME
from ..config import Settings
from ..domain.entities import ModelEntity
from ..domain.exceptions import ModelUnavailableError, NotEnoughTrainingDataError
from ..infrastructure.factory import Repositories, build_repositories
from .learning.ml_pipeline import MODEL_TYPE, build_model_pipeline
from .learning.ml_predict import MLPredict
from .learning.ml_trainer import MLTrainer
from .learning.order_feature import FEATURE_COLUMNS, TARGET_COLUMN
from .learning.train_test_splitter import TrainTestSplitter

logger = logging.getLogger(__name__)


class Container:
    def __init__(self, settings: Settings, repositories: Repositories):
        self.settings = settings
        self.repositories = repositories
        self.trainer = MLTrainer(
            partial(build_model_pipeline, settings.random_seed),
            TrainTestSplitter(settings.random_seed),
        )
        self._lock = threading.Lock()
        self._revision: str | None = None
        self._predictor: MLPredict | None = None
        self._model_card: ModelEntity | None = None

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> Container:
        settings = settings or Settings()
        return cls(settings, build_repositories(settings))

    # --- Entraînement ---
    def train_model(self) -> ModelEntity:
        orders, labels = self.repositories.training_orders.get_training_data()
        if len(orders) < self.settings.min_training_rows:
            raise NotEnoughTrainingDataError(
                f"{len(orders)} commande(s) valides, minimum requis : "
                f"{self.settings.min_training_rows}"
            )
        result = self.trainer.train(orders, labels)
        card = ModelEntity(
            project=SERVICE_NAME,
            model_version=self.settings.model_version,
            model_type=MODEL_TYPE,
            task="classification binaire",
            target=TARGET_COLUMN,
            threshold=self.settings.model_threshold,
            features=list(FEATURE_COLUMNS),
            metrics=result.metrics,
            trained_at=datetime.now(UTC),
            training_rows=result.training_rows,
            data_source=self.settings.repository_scheme,
            limitations=self._limitations(),
        )
        self.repositories.models.save(result.model, card)
        return card

    def _limitations(self) -> list[str]:
        limitations = ["Seuil de décision à valider avec le métier."]
        if self.settings.repository_scheme == "memory":
            limitations.append("Entraîné sur des données synthétiques (générateur du notebook).")
        else:
            limitations.append(
                "Labels issus de la règle métier (supervision faible, ADR-0006) : "
                "à remplacer par le retour terrain de la logistique."
            )
        return limitations

    # --- Service ---
    def refresh_model(self) -> bool:
        """Charge le modèle si une nouvelle révision a été écrite. Retourne `True` si disponible."""
        revision = self.repositories.models.revision()
        if revision is not None and revision == self._revision:
            return True
        with self._lock:
            if revision is not None and revision == self._revision:
                return True
            loaded = self.repositories.models.load() if revision else None
            if loaded is None:
                self._predictor, self._model_card, self._revision = None, None, None
                return False
            model, card = loaded
            self._predictor = MLPredict(model, self.settings.model_threshold, card.model_version)
            self._model_card = card
            self._revision = revision
            logger.info("Modèle %s en service (révision %s)", card.model_version, revision)
            return True

    def predictor(self) -> MLPredict:
        if not self.refresh_model() or self._predictor is None:
            raise ModelUnavailableError("Aucun modèle entraîné n'est disponible")
        return self._predictor

    def model_card(self) -> ModelEntity:
        if not self.refresh_model() or self._model_card is None:
            raise ModelUnavailableError("Aucun modèle entraîné n'est disponible")
        return self._model_card


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
