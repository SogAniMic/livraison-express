"""API HTTP (FastAPI) conforme à `docs/api/openapi.yml` (opérations des séances 1 et 3).

Le modèle n'est jamais entraîné ici : l'API charge l'artefact produit par le job
d'entraînement, et recharge automatiquement une nouvelle révision écrite par le
scheduler (ADR-0007). Sans modèle, l'API démarre quand même : `/health/ready` et
`/v1/predictions` répondent 503.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .. import SERVICE_NAME, __version__
from ..core.container import Container, configure_logging
from ..domain.exceptions import ModelUnavailableError, OrderStoreUnavailableError
from .schemas import (
    Error,
    HealthStatus,
    ModelCard,
    OrderAccepted,
    OrderFeatures,
    Prediction,
    ReadinessStatus,
)

logger = logging.getLogger(__name__)

ERROR_RESPONSES = {
    422: {"model": Error, "description": "Commande invalide"},
    503: {"model": Error, "description": "Service indisponible"},
}


def _error(status_code: int, error: str, message: str, details: list[str] | None = None):
    body = Error(error=error, message=message, details=details or [])
    return JSONResponse(status_code=status_code, content=body.model_dump())


def create_app(container: Container | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if getattr(app.state, "container", None) is None:
            app.state.container = Container.from_settings()
        configure_logging(app.state.container.settings.log_level)
        if not app.state.container.refresh_model():
            logger.warning("API démarrée sans modèle : lancez `python -m livraison_express train`")
        yield

    app = FastAPI(
        title=f"{SERVICE_NAME} API",
        version=__version__,
        description="API de prédiction d'éligibilité à la livraison express.",
        lifespan=lifespan,
    )
    app.state.container = container

    def get_container(request: Request) -> Container:
        return request.app.state.container

    # --- Gestion des erreurs : format `Error` du contrat, sans fuite technique ---
    @app.exception_handler(RequestValidationError)
    async def on_validation_error(_: Request, exc: RequestValidationError):
        details = [
            f"{'.'.join(str(part) for part in err['loc'][1:])} : {err['msg']}"
            for err in exc.errors()
        ]
        return _error(422, "validation_error", "Commande invalide", details)

    @app.exception_handler(ModelUnavailableError)
    async def on_model_unavailable(_: Request, exc: ModelUnavailableError):
        return _error(503, "model_unavailable", str(exc))

    @app.exception_handler(OrderStoreUnavailableError)
    async def on_store_unavailable(_: Request, exc: OrderStoreUnavailableError):
        logger.error("Stockage indisponible : %s", exc.__cause__)
        return _error(503, "order_store_unavailable", str(exc))

    # --- health ---
    @app.get("/health", tags=["health"], response_model=HealthStatus)
    def get_health() -> HealthStatus:
        return HealthStatus(service=SERVICE_NAME, version=__version__)

    @app.get(
        "/health/ready",
        tags=["health"],
        response_model=ReadinessStatus,
        responses={503: {"model": ReadinessStatus}},
    )
    def get_readiness(request: Request):
        container = get_container(request)
        checks = {
            "model": "loaded" if container.refresh_model() else "missing",
            "order_store": (
                "reachable" if container.repositories.collected_orders.ping() else "unreachable"
            ),
        }
        ready = checks["model"] == "loaded" and checks["order_store"] == "reachable"
        body = ReadinessStatus(
            status="ready" if ready else "not_ready", checks=checks, version=__version__
        )
        return JSONResponse(status_code=200 if ready else 503, content=body.model_dump(mode="json"))

    # --- orders ---
    @app.post(
        "/v1/orders",
        tags=["orders"],
        status_code=status.HTTP_202_ACCEPTED,
        response_model=OrderAccepted,
        responses={422: ERROR_RESPONSES[422]},
    )
    def create_order(payload: OrderFeatures, request: Request) -> OrderAccepted:
        order = payload.to_entity()
        if not order.order_id:
            order = order.with_id(f"CMD-{uuid.uuid4().hex[:12].upper()}")
        get_container(request).repositories.collected_orders.save(order)
        return OrderAccepted(order_id=order.order_id)

    @app.get(
        "/v1/orders/{order_id}",
        tags=["orders"],
        response_model=OrderFeatures,
        responses={404: {"model": Error}},
    )
    def get_order(order_id: str, request: Request):
        order = get_container(request).repositories.collected_orders.get(order_id)
        if order is None:
            return _error(404, "order_not_found", f"Commande inconnue : {order_id}")
        return OrderFeatures.from_entity(order)

    # --- predictions ---
    @app.post(
        "/v1/predictions",
        tags=["predictions"],
        response_model=Prediction,
        responses=ERROR_RESPONSES,
    )
    def create_prediction(payload: OrderFeatures, request: Request) -> Prediction:
        order = payload.to_entity()
        if not order.order_id:
            order = order.with_id(f"CMD-{uuid.uuid4().hex[:12].upper()}")
        prediction = get_container(request).predictor().predict(order)
        return Prediction(**asdict(prediction))

    # --- model ---
    @app.get(
        "/v1/model",
        tags=["model"],
        response_model=ModelCard,
        responses={503: ERROR_RESPONSES[503]},
    )
    def get_model_card(request: Request) -> ModelCard:
        card = get_container(request).model_card()
        return ModelCard.model_validate(asdict(card), from_attributes=False)

    return app
