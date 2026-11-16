"""`OrderRepository` en mémoire : tests et développement local uniquement.

Données perdues au redémarrage, rien n'est partagé entre processus : acceptable pour
un test unitaire, inacceptable en production.
"""

from __future__ import annotations

from ....domain.entities import OrderEntity
from ...order_repository import OrderRepository
from .order_generator import generate_labeled_orders


class InMemoryOrderRepository(OrderRepository):
    def __init__(self, orders: list[OrderEntity] | None = None, labels: list[int] | None = None):
        self._orders: dict[str, OrderEntity] = {}
        self._labels: dict[str, int] = {}
        for order, label in zip(orders or [], labels or [], strict=False):
            self._orders[order.order_id] = order
            self._labels[order.order_id] = label

    @classmethod
    def with_synthetic_data(cls, random_seed: int, n_rows: int = 6000) -> InMemoryOrderRepository:
        orders, labels = generate_labeled_orders(n_rows=n_rows, random_state=random_seed)
        return cls(orders, labels)

    def save(self, order: OrderEntity) -> None:
        if not order.order_id:
            raise ValueError("order_id obligatoire pour enregistrer une commande")
        self._orders[order.order_id] = order

    def get(self, order_id: str) -> OrderEntity | None:
        return self._orders.get(order_id)

    def get_all(self) -> list[OrderEntity]:
        return list(self._orders.values())

    def count(self) -> int:
        return len(self._orders)

    def get_training_data(self) -> tuple[list[OrderEntity], list[int]]:
        orders = [order for order in self._orders.values() if order.order_id in self._labels]
        return orders, [self._labels[order.order_id] for order in orders]
