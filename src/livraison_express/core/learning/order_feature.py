"""Contrat des features : défini une seule fois (DRY), partagé par l'entraînement et l'API."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from ...domain.entities import OrderEntity

TARGET_COLUMN = "express_eligible"

NUMERIC_FEATURES = [
    "hour",
    "day_of_week",
    "weekend",
    "distance_km",
    "order_value_eur",
    "weight_kg",
    "stock_available",
    "preparation_time_min",
    "carrier_capacity",
]

CATEGORICAL_FEATURES = ["weather", "delivery_zone", "customer_type"]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def orders_to_dataframe(orders: Iterable[OrderEntity]) -> pd.DataFrame:
    """Convertir des entités en table de features.

    Le domaine reste indépendant de pandas : la conversion n'a lieu qu'à la frontière
    avec la couche d'apprentissage. `order_id` n'est volontairement pas transmis.
    """
    frame = pd.DataFrame(
        [{feature: getattr(order, feature) for feature in FEATURE_COLUMNS} for order in orders],
        columns=FEATURE_COLUMNS,
    )
    frame[NUMERIC_FEATURES] = frame[NUMERIC_FEATURES].astype(float)
    return frame
