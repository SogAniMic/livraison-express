import pytest

from livraison_express.domain.exceptions import InvalidOrderError
from livraison_express.infrastructure.implementation.mongo.order_mappers import (
    CanonicalOrderMapper,
    ErpOrderMapper,
)

ERP_DOCUMENT = {
    "order_id": "ERP-00011001",
    "hour": 9,
    "day_of_week": 5,
    "weekend": 1,
    "distance_km": 12.3,
    "order_value_eur": 45.0,
    "weight_kg": 3.2,
    "stock_available": 1,
    "preparation_time_min": 20.5,
    "carrier_capacity": 25.0,
    "weather": "rain",
    "delivery_zone": "suburb",
    "customer_type": "business",
}


def test_erp_vocabulary_is_translated_to_model_vocabulary():
    order = ErpOrderMapper().to_entity(ERP_DOCUMENT)
    assert order.weather == "pluie"
    assert order.delivery_zone == "banlieue"
    assert order.customer_type == "premium"
    assert order.carrier_capacity == 0.5  # 25 véhicules / 50


def test_historical_rows_without_migrated_columns_are_accepted():
    document = {**ERP_DOCUMENT, "weekend": None, "preparation_time_min": None}
    order = ErpOrderMapper().to_entity(document)
    assert order.weekend == 1  # dérivé de day_of_week
    assert order.preparation_time_min is None  # imputé par la pipeline


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("hour", 27),
        ("distance_km", -1),
        ("distance_km", "loin"),
        ("weather", "tornade"),
        ("stock_available", 3),
        ("order_id", None),
    ],
)
def test_invalid_documents_are_rejected_with_details(field, value):
    with pytest.raises(InvalidOrderError) as error:
        ErpOrderMapper().to_entity({**ERP_DOCUMENT, field: value})
    assert any(field in detail for detail in error.value.details)


def test_canonical_mapper_round_trip():
    order = ErpOrderMapper().to_entity(ERP_DOCUMENT)
    mapper = CanonicalOrderMapper()
    assert mapper.to_entity(mapper.to_document(order)) == order


def test_canonical_mapper_refuses_erp_vocabulary():
    with pytest.raises(InvalidOrderError):
        CanonicalOrderMapper().to_entity(ERP_DOCUMENT)
