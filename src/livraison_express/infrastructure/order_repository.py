"""Abstraction : où l'application lit et range les commandes.

Contrat attendu de toute implémentation
(vérifié par `tests/unit/test_order_repository_contract.py`) :

- `save` est idempotent sur `order_id` (pas de doublon) ;
- `get` renvoie `None` pour un identifiant inconnu, sans lever d'exception ;
- les erreurs levées sont celles de `domain/exceptions.py`, jamais celles de la
  bibliothèque de stockage (l'application ne connaît pas l'infrastructure) ;
- `get_training_data` renvoie commandes et labels alignés, dans le même ordre.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.entities import OrderEntity


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: OrderEntity) -> None:
        """Enregistre une commande (dont l'`order_id` est renseigné)."""

    @abstractmethod
    def get(self, order_id: str) -> OrderEntity | None:
        """Retourne la commande ou `None` si elle est inconnue."""

    @abstractmethod
    def get_all(self) -> list[OrderEntity]:
        """Retourne toutes les commandes valides."""

    @abstractmethod
    def count(self) -> int:
        """Nombre de commandes stockées."""

    @abstractmethod
    def get_training_data(self) -> tuple[list[OrderEntity], list[int]]:
        """Commandes et labels `express_eligible` alignés."""

    def ping(self) -> bool:
        """Le support répond-il ? Utilisé par la sonde `/health/ready`."""
        return True
