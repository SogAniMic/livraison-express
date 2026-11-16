import mongomock
import pytest
from pymongo.errors import ServerSelectionTimeoutError

from livraison_express.core.learning.labeling import BusinessRuleLabeler
from livraison_express.domain.exceptions import OrderStoreUnavailableError
from livraison_express.infrastructure.implementation.mongo.mongo_order_repository import (
    MongoOrderRepository,
)
from livraison_express.infrastructure.implementation.mongo.order_mappers import ErpOrderMapper
from tests.conftest import make_order
from tests.unit.test_erp_mapper import ERP_DOCUMENT


@pytest.fixture
def erp_collection():
    collection = mongomock.MongoClient()["livraison_express"]["orders"]
    collection.insert_many(
        [{**ERP_DOCUMENT, "order_id": f"ERP-{i:08d}", "distance_km": i % 30} for i in range(60)]
        + [{**ERP_DOCUMENT, "order_id": "ERP-BROKEN", "weather": "???"}]
    )
    return collection


def test_training_data_skips_invalid_documents_and_labels_the_rest(erp_collection):
    repository = MongoOrderRepository(
        erp_collection, ErpOrderMapper(), BusinessRuleLabeler(42), read_only=True
    )
    orders, labels = repository.get_training_data()
    assert len(orders) == len(labels) == 60
    assert repository.rejected_count == 1
    assert repository.count() == 61


def test_erp_collection_is_read_only(erp_collection):
    repository = MongoOrderRepository(erp_collection, ErpOrderMapper(), read_only=True)
    with pytest.raises(PermissionError):
        repository.save(make_order())


def test_pymongo_errors_are_translated_to_domain_errors():
    class BrokenCollection:
        name = "orders"

        def count_documents(self, _):
            raise ServerSelectionTimeoutError("connexion refusée")

    repository = MongoOrderRepository(BrokenCollection(), ErpOrderMapper(), read_only=True)
    with pytest.raises(OrderStoreUnavailableError):
        repository.count()
