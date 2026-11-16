"""Fabrique (design pattern Factory) : choisit les implémentations selon la configuration.

C'est le seul module qui connaît les classes concrètes de stockage. Passer de la
mémoire à MongoDB, c'est changer `ORDER_REPOSITORY_URL`, pas le code (Open/Closed).
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings
from ..core.learning.labeling import BusinessRuleLabeler
from .implementation.dev.file_model_repository import FileModelRepository
from .implementation.dev.in_memory_order_repository import InMemoryOrderRepository
from .model_repository import ModelRepository
from .order_repository import OrderRepository


@dataclass(frozen=True)
class Repositories:
    training_orders: OrderRepository  # source d'entraînement (ERP via ETL)
    collected_orders: OrderRepository  # commandes reçues par l'API
    models: ModelRepository


def build_repositories(settings: Settings) -> Repositories:
    models = FileModelRepository(settings.model_path)
    scheme = settings.repository_scheme

    if scheme == "memory":
        return Repositories(
            training_orders=InMemoryOrderRepository.with_synthetic_data(settings.random_seed),
            collected_orders=InMemoryOrderRepository(),
            models=models,
        )

    if scheme in ("mongodb", "mongodb+srv"):
        from pymongo import MongoClient

        from .implementation.mongo.mongo_order_repository import MongoOrderRepository
        from .implementation.mongo.order_mappers import CanonicalOrderMapper, ErpOrderMapper

        client = MongoClient(
            settings.order_repository_url.get_secret_value(),
            serverSelectionTimeoutMS=settings.mongo_timeout_ms,
            appname="livraison-express",
        )
        database = client[settings.mongo_database]
        return Repositories(
            training_orders=MongoOrderRepository(
                database[settings.mongo_erp_collection],
                ErpOrderMapper(),
                labeler=BusinessRuleLabeler(settings.random_seed),
                read_only=True,
            ),
            collected_orders=MongoOrderRepository(
                database[settings.mongo_collected_collection], CanonicalOrderMapper()
            ),
            models=models,
        )

    raise ValueError(f"ORDER_REPOSITORY_URL : schéma non supporté « {scheme} »")
