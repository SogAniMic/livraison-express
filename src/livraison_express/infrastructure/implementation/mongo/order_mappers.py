"""Couche anti-corruption entre les documents MongoDB et `OrderEntity` (ADR-0006).

On ne fait pas confiance à la qualité des données : chaque document est validé
(types, bornes, valeurs autorisées) avant d'entrer dans l'application. Le vocabulaire
de l'ERP diffère de celui du modèle (`clear` / `normal`, `suburb` / `banlieue`,
capacité transporteur en nombre de véhicules et non en taux) : le mapping est fait
ici, à un seul endroit, et chaque hypothèse est tracée dans l'ADR-0006.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any, Protocol

from ....domain.entities import CustomerType, DeliveryZone, OrderEntity, Weather
from ....domain.exceptions import InvalidOrderError

ERP_WEATHER = {
    "clear": Weather.NORMAL,
    "rain": Weather.PLUIE,
    "snow": Weather.NEIGE,
    "wind": Weather.ORAGE,  # hypothèse : vent = intempérie la plus pénalisante
}
ERP_ZONE = {
    "centre": DeliveryZone.CENTRE,
    "suburb": DeliveryZone.BANLIEUE,
    "rural": DeliveryZone.RURALE,
}
ERP_CUSTOMER = {
    "individual": CustomerType.STANDARD,
    "business": CustomerType.PREMIUM,  # hypothèse : contrat B2B = service prioritaire
}
# L'ERP exprime la capacité en véhicules disponibles (5 à 50) ; le modèle attend un taux.
ERP_CARRIER_CAPACITY_MAX = 50.0


class OrderDocumentMapper(Protocol):
    def to_entity(self, document: Mapping[str, Any]) -> OrderEntity: ...

    def to_document(self, order: OrderEntity) -> dict[str, Any]: ...


def _number(document: Mapping[str, Any], key: str, errors: list[str], *, low=None, high=None):
    value = document.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        errors.append(f"{key} : nombre attendu, reçu {value!r}")
        return None
    if (low is not None and value < low) or (high is not None and value > high):
        errors.append(f"{key} : {value} hors de l'intervalle [{low}, {high}]")
        return None
    return value


def _choice(value: Any, allowed: Mapping[str, Any] | type, key: str, errors: list[str]):
    try:
        if isinstance(allowed, Mapping):
            return str(allowed[value])
        return str(allowed(value))
    except (KeyError, ValueError):
        errors.append(f"{key} : valeur inconnue {value!r}")
        return None


class CanonicalOrderMapper:
    """Documents écrits par l'application elle-même (collection `api_orders`)."""

    def to_entity(self, document: Mapping[str, Any]) -> OrderEntity:
        errors: list[str] = []
        order = _build(document, errors, canonical=True)
        if errors:
            raise InvalidOrderError(f"Commande {document.get('order_id')} invalide", errors)
        return order

    def to_document(self, order: OrderEntity) -> dict[str, Any]:
        return asdict(order)


class ErpOrderMapper(CanonicalOrderMapper):
    """Documents produits par l'ETL depuis l'ERP (collection `orders`)."""

    def to_entity(self, document: Mapping[str, Any]) -> OrderEntity:
        errors: list[str] = []
        order = _build(document, errors, canonical=False)
        if errors:
            raise InvalidOrderError(f"Commande ERP {document.get('order_id')} invalide", errors)
        return order


def _build(document: Mapping[str, Any], errors: list[str], *, canonical: bool) -> OrderEntity:
    order_id = document.get("order_id")
    if not isinstance(order_id, str) or not order_id:
        errors.append("order_id : identifiant manquant")

    hour = _number(document, "hour", errors, low=0, high=23)
    day_of_week = _number(document, "day_of_week", errors, low=0, high=6)
    weekend = document.get("weekend")
    if weekend is None and day_of_week is not None:
        weekend = int(day_of_week >= 5)  # colonne absente avant juillet 2015 : on la dérive
    elif weekend not in (0, 1):
        errors.append(f"weekend : 0 ou 1 attendu, reçu {weekend!r}")

    distance = _number(document, "distance_km", errors, low=0)
    value = _number(document, "order_value_eur", errors, low=0)
    weight = _number(document, "weight_kg", errors, low=0)
    stock = document.get("stock_available")
    if stock not in (0, 1):
        errors.append(f"stock_available : 0 ou 1 attendu, reçu {stock!r}")

    preparation = document.get("preparation_time_min")
    if preparation is not None:  # absente avant juillet 2017 : imputée par la pipeline
        preparation = _number(document, "preparation_time_min", errors, low=0)

    if canonical:
        capacity = _number(document, "carrier_capacity", errors, low=0, high=1)
        weather = _choice(document.get("weather"), Weather, "weather", errors)
        zone = _choice(document.get("delivery_zone"), DeliveryZone, "delivery_zone", errors)
        customer = _choice(document.get("customer_type"), CustomerType, "customer_type", errors)
    else:
        raw_capacity = _number(document, "carrier_capacity", errors, low=0)
        capacity = (
            None if raw_capacity is None else min(raw_capacity / ERP_CARRIER_CAPACITY_MAX, 1.0)
        )
        weather = _choice(document.get("weather"), ERP_WEATHER, "weather", errors)
        zone = _choice(document.get("delivery_zone"), ERP_ZONE, "delivery_zone", errors)
        customer = _choice(document.get("customer_type"), ERP_CUSTOMER, "customer_type", errors)

    if errors:
        return None  # type: ignore[return-value]
    return OrderEntity(
        order_id=order_id,
        hour=int(hour),
        day_of_week=int(day_of_week),
        weekend=int(weekend),
        distance_km=float(distance),
        order_value_eur=float(value),
        weight_kg=float(weight),
        stock_available=int(stock),
        preparation_time_min=None if preparation is None else float(preparation),
        carrier_capacity=round(float(capacity), 4),
        weather=weather,
        delivery_zone=zone,
        customer_type=customer,
    )
