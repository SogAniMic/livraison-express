"""`OrderRepository` MongoDB (ADR-0005 : la base analytique plutôt que la base de production).

- Une instance par collection : la collection `orders` alimentée par l'ETL est
  utilisée en lecture seule pour l'entraînement ; les commandes reçues par l'API sont
  écrites dans une collection séparée (`api_orders`) pour ne jamais altérer les
  données de référence.
- Les documents invalides sont écartés et comptés (journalisés), jamais propagés.
- Les erreurs pymongo sont traduites en erreurs du domaine.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from typing import Any

from pymongo import ASCENDING
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from ....domain.entities import OrderEntity
from ....domain.exceptions import InvalidOrderError, OrderStoreUnavailableError
from ...order_repository import OrderRepository
from .order_mappers import OrderDocumentMapper

logger = logging.getLogger(__name__)

PROJECTION = {"_id": False}


class MongoOrderRepository(OrderRepository):
    def __init__(
        self,
        collection: Collection,
        mapper: OrderDocumentMapper,
        labeler=None,
        read_only: bool = False,
    ):
        self._collection = collection
        self._mapper = mapper
        self._labeler = labeler
        self._read_only = read_only
        self.rejected_count = 0
        if not read_only:
            self._guard(lambda: collection.create_index([("order_id", ASCENDING)], unique=True))

    # --- Contrat OrderRepository ---
    def save(self, order: OrderEntity) -> None:
        if self._read_only:
            raise PermissionError(f"Collection {self._collection.name} en lecture seule")
        if not order.order_id:
            raise ValueError("order_id obligatoire pour enregistrer une commande")
        document = self._mapper.to_document(order)
        self._guard(
            lambda: self._collection.replace_one(
                {"order_id": order.order_id}, document, upsert=True
            )
        )

    def get(self, order_id: str) -> OrderEntity | None:
        document = self._guard(
            lambda: self._collection.find_one({"order_id": order_id}, PROJECTION)
        )
        if document is None:
            return None
        try:
            return self._mapper.to_entity(document)
        except InvalidOrderError as error:
            logger.warning("%s : %s", error, "; ".join(error.details))
            return None

    def get_all(self) -> list[OrderEntity]:
        return list(self._iter_valid_orders())

    def count(self) -> int:
        return self._guard(lambda: self._collection.count_documents({}))

    def get_training_data(self) -> tuple[list[OrderEntity], list[int]]:
        if self._labeler is None:
            raise NotImplementedError(
                f"Aucune stratégie d'étiquetage configurée pour {self._collection.name}"
            )
        orders = self.get_all()
        return orders, self._labeler.label(orders)

    def ping(self) -> bool:
        try:
            self._collection.database.client.admin.command("ping")
            return True
        except PyMongoError:
            return False

    # --- Interne ---
    def _iter_valid_orders(self) -> Iterator[OrderEntity]:
        self.rejected_count = 0
        cursor = self._guard(
            lambda: list(self._collection.find({}, PROJECTION).sort("order_id", ASCENDING))
        )
        for document in cursor:
            try:
                yield self._mapper.to_entity(document)
            except InvalidOrderError as error:
                self.rejected_count += 1
                logger.debug("%s : %s", error, "; ".join(error.details))
        if self.rejected_count:
            logger.warning(
                "%d document(s) rejeté(s) par le contrôle qualité dans %s",
                self.rejected_count,
                self._collection.name,
            )

    @staticmethod
    def _guard(operation) -> Any:
        try:
            return operation()
        except PyMongoError as error:
            raise OrderStoreUnavailableError("Base de commandes MongoDB indisponible") from error
