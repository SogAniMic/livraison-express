"""Schémas HTTP, alignés champ pour champ sur `docs/api/openapi.yml` (le contrat fait foi).

Ils vivent dans la couche API : le domaine ne dépend pas de pydantic.
`extra="forbid"` : une variable en trop produit une 422, comme l'exige le contrat.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..domain.entities import CustomerType, DeliveryZone, OrderEntity, Weather


class OrderFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str | None = Field(default=None, examples=["CMD-000001"], max_length=64)
    hour: int = Field(ge=0, le=23, examples=[14])
    day_of_week: int = Field(ge=0, le=6, description="0 = lundi ... 6 = dimanche", examples=[2])
    weekend: Literal[0, 1] = Field(examples=[0])
    distance_km: float = Field(ge=0, examples=[3.5])
    order_value_eur: float = Field(ge=0, examples=[89.9])
    weight_kg: float = Field(ge=0, examples=[2.4])
    stock_available: Literal[0, 1] = Field(examples=[1])
    preparation_time_min: float = Field(ge=0, examples=[18])
    carrier_capacity: float = Field(ge=0, le=1, examples=[0.85])
    weather: Weather
    delivery_zone: DeliveryZone
    customer_type: CustomerType

    def to_entity(self) -> OrderEntity:
        data = self.model_dump()
        data["weather"] = self.weather.value
        data["delivery_zone"] = self.delivery_zone.value
        data["customer_type"] = self.customer_type.value
        return OrderEntity(**data)

    @classmethod
    def from_entity(cls, order: OrderEntity) -> OrderFeatures:
        return cls.model_validate(order.__dict__)


class OrderAccepted(BaseModel):
    order_id: str
    status: Literal["accepted"] = "accepted"


class Prediction(BaseModel):
    order_id: str
    express_eligible: bool
    decision: Literal["oui", "non"]
    probability: float = Field(ge=0, le=1)
    model_version: str
    predicted_at: datetime
    latency_ms: float | None = None


class ModelCard(BaseModel):
    project: str
    model_version: str
    model_type: str
    task: str
    target: str
    threshold: float
    trained_at: datetime | None = None
    features: list[str]
    metrics: dict[str, float]
    limitations: list[str] = []


class HealthStatus(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str


class ReadinessStatus(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, str]
    version: str | None = None


class Error(BaseModel):
    error: str
    message: str
    details: list[str] = []
