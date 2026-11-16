"""Entraînement et évaluation (cellules 26 à 30 du notebook)."""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline

from ...domain.entities import OrderEntity
from .train_test_splitter import TrainTestSplitter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrainingResult:
    model: Pipeline
    metrics: dict[str, float]
    training_rows: int


class MLTrainer:
    """Entraîne une pipeline fournie par une fabrique (aucun état partagé entre deux runs)."""

    def __init__(self, pipeline_factory, splitter: TrainTestSplitter):
        self._pipeline_factory = pipeline_factory
        self._splitter = splitter

    def train(self, orders: Sequence[OrderEntity], labels: Sequence[int]) -> TrainingResult:
        started_at = time.perf_counter()
        X_train, X_test, y_train, y_test = self._splitter.split(orders, labels)

        model = self._pipeline_factory()
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, y_proba)),
        }
        logger.info(
            "Entraînement terminé en %.2f s : %s",
            time.perf_counter() - started_at,
            ", ".join(f"{name}={value:.4f}" for name, value in metrics.items()),
        )
        return TrainingResult(model=model, metrics=metrics, training_rows=len(orders))
