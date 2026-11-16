"""Objets métier : indépendants de FastAPI, pandas, scikit-learn et MongoDB."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum


class Weather(StrEnum):
    NORMAL = "normal"
    PLUIE = "pluie"
    NEIGE = "neige"
    ORAGE = "orage"


class DeliveryZone(StrEnum):
    CENTRE = "centre"
    PROCHE_BANLIEUE = "proche_banlieue"
    BANLIEUE = "banlieue"
    RURALE = "rurale"


class CustomerType(StrEnum):
    STANDARD = "standard"
    PREMIUM = "premium"


@dataclass(frozen=True)
class OrderEntity:
    """Une commande, décrite par les features du notebook (cellule 20).

    `preparation_time_min` peut être absent pour les données historiques (colonne
    ajoutée en 2017 dans l'ERP) : la pipeline l'impute par la médiane.
    `order_id` identifie la commande mais n'est jamais une feature.
    """

    hour: int
    day_of_week: int
    weekend: int
    distance_km: float
    order_value_eur: float
    weight_kg: float
    stock_available: int
    preparation_time_min: float | None
    carrier_capacity: float
    weather: str
    delivery_zone: str
    customer_type: str
    order_id: str | None = None

    def with_id(self, order_id: str) -> OrderEntity:
        return replace(self, order_id=order_id)


@dataclass(frozen=True)
class PredictionEntity:
    """Résultat métier d'une prédiction (cellule 34 du notebook)."""

    order_id: str | None
    express_eligible: bool
    decision: str
    probability: float
    model_version: str
    predicted_at: datetime
    latency_ms: float | None = None


@dataclass(frozen=True)
class ModelEntity:
    """Model card (cellule 55 du notebook), alignée sur le schéma `ModelCard` de l'OpenAPI."""

    project: str
    model_version: str
    model_type: str
    task: str
    target: str
    threshold: float
    features: list[str]
    metrics: dict[str, float]
    trained_at: datetime | None = None
    training_rows: int = 0
    data_source: str = "unknown"
    limitations: list[str] = field(default_factory=list)
