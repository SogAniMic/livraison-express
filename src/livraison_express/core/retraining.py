"""Orchestration du réentraînement (ADR-0007).

L'entraînement est un processus d'exécution, pas de construction : il n'a rien à
faire dans la CI/CD. On réentraîne quand suffisamment de nouvelles données sont
arrivées depuis le dernier modèle, vérifié à intervalle régulier par un service
dédié (`python -m livraison_express scheduler`).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass

from ..domain.exceptions import LivraisonExpressError
from .container import Container

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrainingDecision:
    should_train: bool
    reason: str


def decide(
    current_rows: int, trained_rows: int | None, min_new_orders: int, min_training_rows: int
) -> RetrainingDecision:
    if current_rows < min_training_rows:
        return RetrainingDecision(False, f"{current_rows} commandes < minimum {min_training_rows}")
    if trained_rows is None:
        return RetrainingDecision(True, "aucun modèle en service")
    new_rows = current_rows - trained_rows
    if new_rows >= min_new_orders:
        return RetrainingDecision(True, f"{new_rows} nouvelles commandes depuis le dernier modèle")
    return RetrainingDecision(False, f"{new_rows}/{min_new_orders} nouvelles commandes")


class RetrainingScheduler:
    def __init__(self, container: Container, sleep: Callable[[float], None] = time.sleep):
        self._container = container
        self._sleep = sleep

    def run_once(self) -> RetrainingDecision:
        settings = self._container.settings
        trained_rows = (
            self._container.model_card().training_rows if self._container.refresh_model() else None
        )
        decision = decide(
            self._container.repositories.training_orders.count(),
            trained_rows,
            settings.retrain_min_new_orders,
            settings.min_training_rows,
        )
        verdict = "lancé" if decision.should_train else "non nécessaire"
        logger.info("Réentraînement %s : %s", verdict, decision.reason)
        if decision.should_train:
            card = self._container.train_model()
            self._container.refresh_model()
            logger.info("Nouveau modèle : %d lignes, %s", card.training_rows, card.metrics)
        return decision

    def run_forever(self, max_iterations: int | None = None) -> None:
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            try:
                self.run_once()
            except LivraisonExpressError as error:  # base indisponible, données insuffisantes...
                logger.error("Cycle de réentraînement en échec : %s", error)
            iteration += 1
            if max_iterations is None or iteration < max_iterations:
                self._sleep(self._container.settings.retrain_check_interval_seconds)
