"""Séparation entraînement / test (cellule 22 du notebook) : 80/20 stratifié."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from sklearn.model_selection import train_test_split

from ...domain.entities import OrderEntity
from ...domain.exceptions import NotEnoughTrainingDataError
from .order_feature import orders_to_dataframe

logger = logging.getLogger(__name__)


class TrainTestSplitter:
    def __init__(self, random_seed: int, test_size: float = 0.20):
        self.random_seed = random_seed
        self.test_size = test_size

    def split(self, orders: Sequence[OrderEntity], labels: Sequence[int]):
        if len(orders) != len(labels):
            raise ValueError("Le nombre de commandes doit correspondre au nombre de labels")
        if len(set(labels)) < 2:
            raise NotEnoughTrainingDataError(
                "Les labels ne contiennent qu'une seule classe : entraînement impossible"
            )
        features = orders_to_dataframe(orders)
        X_train, X_test, y_train, y_test = train_test_split(
            features,
            list(labels),
            test_size=self.test_size,
            random_state=self.random_seed,
            stratify=list(labels),
        )
        logger.info("Split terminé (train=%d, test=%d)", len(X_train), len(X_test))
        return X_train, X_test, y_train, y_test
