"""Prédiction d'une commande (cellule 34 du notebook)."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime

from ...domain.entities import OrderEntity, PredictionEntity
from .order_feature import orders_to_dataframe


class MLPredict:
    """Transforme un score en décision métier.

    Le seuil n'est pas le modèle : le modèle produit une probabilité, le seuil la
    traduit en « oui » / « non ». On peut ajuster le seuil sans réentraîner.
    """

    def __init__(
        self,
        model,
        threshold: float,
        model_version: str,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self._model = model
        self._threshold = threshold
        self._model_version = model_version
        self._clock = clock

    def predict(self, order: OrderEntity) -> PredictionEntity:
        started_at = time.perf_counter()
        probability = float(self._model.predict_proba(orders_to_dataframe([order]))[0, 1])
        eligible = probability >= self._threshold
        return PredictionEntity(
            order_id=order.order_id,
            express_eligible=bool(eligible),
            decision="oui" if eligible else "non",
            probability=round(probability, 4),
            model_version=self._model_version,
            predicted_at=self._clock(),
            latency_ms=round((time.perf_counter() - started_at) * 1000, 3),
        )
