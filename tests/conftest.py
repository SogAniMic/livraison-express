from __future__ import annotations

import pytest

from livraison_express.config import Settings
from livraison_express.core.container import Container
from livraison_express.domain.entities import OrderEntity
from livraison_express.infrastructure.factory import Repositories
from livraison_express.infrastructure.implementation.dev.file_model_repository import (
    FileModelRepository,
)
from livraison_express.infrastructure.implementation.dev.in_memory_order_repository import (
    InMemoryOrderRepository,
)


def make_order(**overrides) -> OrderEntity:
    values = dict(
        hour=14,
        day_of_week=2,
        weekend=0,
        distance_km=3.5,
        order_value_eur=89.9,
        weight_kg=2.4,
        stock_available=1,
        preparation_time_min=18.0,
        carrier_capacity=0.85,
        weather="normal",
        delivery_zone="centre",
        customer_type="premium",
        order_id="CMD-TEST-1",
    )
    values.update(overrides)
    return OrderEntity(**values)


VALID_PAYLOAD = {
    "hour": 14,
    "day_of_week": 2,
    "weekend": 0,
    "distance_km": 3.5,
    "order_value_eur": 89.9,
    "weight_kg": 2.4,
    "stock_available": 1,
    "preparation_time_min": 18,
    "carrier_capacity": 0.85,
    "weather": "normal",
    "delivery_zone": "centre",
    "customer_type": "premium",
}


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        _env_file=None,
        environment="test",
        model_path=str(tmp_path / "artifacts" / "model.joblib"),
        min_training_rows=50,
        retrain_min_new_orders=100,
    )


@pytest.fixture
def container(settings) -> Container:
    repositories = Repositories(
        training_orders=InMemoryOrderRepository.with_synthetic_data(42, n_rows=800),
        collected_orders=InMemoryOrderRepository(),
        models=FileModelRepository(settings.model_path),
    )
    return Container(settings, repositories)


@pytest.fixture
def trained_container(container) -> Container:
    container.train_model()
    return container
