"""Tests d'intégration sur un vrai MongoDB (CI : service `mongo`, local : `MONGO_URI=...`)."""

import os
import uuid

import pytest

pytestmark = pytest.mark.integration

MONGO_URI = os.getenv("MONGO_URI")


@pytest.fixture
def database():
    if not MONGO_URI:
        pytest.skip("MONGO_URI non défini")
    from pymongo import MongoClient

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    name = f"livraison_express_test_{uuid.uuid4().hex[:8]}"
    yield client[name]
    client.drop_database(name)
    client.close()


def test_train_and_predict_end_to_end_on_erp_documents(database, tmp_path):
    from livraison_express.config import Settings
    from livraison_express.core.container import Container
    from tests.conftest import make_order
    from tests.unit.test_erp_mapper import ERP_DOCUMENT

    database["orders"].insert_many(
        [
            {
                **ERP_DOCUMENT,
                "order_id": f"ERP-{i:08d}",
                "distance_km": float(1 + i % 40),
                "stock_available": i % 2,
                "weather": ["clear", "rain", "wind", "snow"][i % 4],
            }
            for i in range(400)
        ]
    )
    settings = Settings(
        _env_file=None,
        order_repository_url=MONGO_URI,
        mongo_database=database.name,
        model_path=str(tmp_path / "model.joblib"),
        min_training_rows=100,
    )
    container = Container.from_settings(settings)
    card = container.train_model()
    assert card.training_rows == 400
    assert card.data_source == "mongodb"

    container.repositories.collected_orders.save(make_order(order_id="CMD-INTEG"))
    assert database["api_orders"].count_documents({}) == 1
    assert database["orders"].count_documents({}) == 400  # la collection ERP n'est pas modifiée
    assert container.predictor().predict(make_order()).decision in {"oui", "non"}
