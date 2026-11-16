"""Tests de contrat : toute implémentation d'OrderRepository doit les passer (Liskov)."""

import mongomock
import pytest

from livraison_express.core.learning.labeling import BusinessRuleLabeler
from livraison_express.infrastructure.implementation.dev.in_memory_order_repository import (
    InMemoryOrderRepository,
)
from livraison_express.infrastructure.implementation.mongo.mongo_order_repository import (
    MongoOrderRepository,
)
from livraison_express.infrastructure.implementation.mongo.order_mappers import (
    CanonicalOrderMapper,
)
from tests.conftest import make_order


def in_memory():
    return InMemoryOrderRepository()


def mongo():
    collection = mongomock.MongoClient()["livraison_express"]["api_orders"]
    return MongoOrderRepository(collection, CanonicalOrderMapper(), BusinessRuleLabeler(42))


@pytest.fixture(params=[in_memory, mongo], ids=["memory", "mongo"])
def repository(request):
    return request.param()


def test_get_unknown_returns_none(repository):
    assert repository.get("inconnue") is None


def test_save_then_get(repository):
    order = make_order(order_id="CMD-1")
    repository.save(order)
    assert repository.get("CMD-1") == order


def test_save_is_idempotent(repository):
    repository.save(make_order(order_id="CMD-1"))
    repository.save(make_order(order_id="CMD-1", distance_km=9.0))
    assert repository.count() == 1
    assert repository.get("CMD-1").distance_km == 9.0


def test_get_all(repository):
    for index in range(3):
        repository.save(make_order(order_id=f"CMD-{index}"))
    assert {order.order_id for order in repository.get_all()} == {"CMD-0", "CMD-1", "CMD-2"}


def test_save_requires_an_identifier(repository):
    with pytest.raises(ValueError):
        repository.save(make_order(order_id=None))
