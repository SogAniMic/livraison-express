import pytest
from fastapi.testclient import TestClient

from livraison_express.api.app import create_app
from tests.conftest import VALID_PAYLOAD


@pytest.fixture
def client(trained_container):
    with TestClient(create_app(trained_container)) as test_client:
        yield test_client


@pytest.fixture
def client_without_model(container):
    with TestClient(create_app(container)) as test_client:
        yield test_client


def test_health_never_depends_on_the_model(client_without_model):
    response = client_without_model.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_is_503_without_model(client_without_model):
    response = client_without_model.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["model"] == "missing"


def test_ready_when_model_loaded(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["checks"] == {"model": "loaded", "order_store": "reachable"}


def test_prediction(client):
    response = client.post("/v1/predictions", json={**VALID_PAYLOAD, "order_id": "CMD-42"})
    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] == "CMD-42"
    assert body["decision"] in {"oui", "non"}
    assert 0 <= body["probability"] <= 1
    assert body["model_version"] == "1.0.0"


def test_prediction_503_without_model(client_without_model):
    response = client_without_model.post("/v1/predictions", json=VALID_PAYLOAD)
    assert response.status_code == 503
    assert response.json()["error"] == "model_unavailable"


@pytest.mark.parametrize(
    "payload",
    [
        {k: v for k, v in VALID_PAYLOAD.items() if k != "distance_km"},  # variable absente
        {**VALID_PAYLOAD, "express_eligible": 1},  # variable en trop (fuite de la cible)
        {**VALID_PAYLOAD, "weather": "clear"},  # vocabulaire inconnu
        {**VALID_PAYLOAD, "carrier_capacity": 25},  # hors bornes
    ],
)
def test_invalid_orders_return_422_with_error_contract(client, payload):
    response = client.post("/v1/predictions", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["details"]


def test_order_collection_round_trip(client):
    created = client.post("/v1/orders", json=VALID_PAYLOAD)
    assert created.status_code == 202
    order_id = created.json()["order_id"]
    fetched = client.get(f"/v1/orders/{order_id}")
    assert fetched.status_code == 200
    assert fetched.json()["distance_km"] == VALID_PAYLOAD["distance_km"]


def test_unknown_order_is_404(client):
    response = client.get("/v1/orders/CMD-INCONNUE")
    assert response.status_code == 404
    assert response.json()["error"] == "order_not_found"


def test_model_card(client):
    body = client.get("/v1/model").json()
    assert body["target"] == "express_eligible"
    assert set(body["metrics"]) == {"accuracy", "precision", "recall", "f1_score", "roc_auc"}
    assert "order_id" not in body["features"]


def test_api_reloads_a_new_model_revision(client, trained_container):
    first = client.get("/v1/model").json()["trained_at"]
    trained_container.train_model()
    assert client.get("/v1/model").json()["trained_at"] != first
