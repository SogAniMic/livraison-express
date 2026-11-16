"""Étiquetage des commandes de l'ERP (ADR-0006).

Les commandes de l'ERP ne contiennent pas la cible `express_eligible` : l'ERP sait
qu'une commande existe, pas si elle a pu être livrée dans la journée. En attendant
que le service logistique fournisse ce retour terrain, on applique la règle métier
qui a servi à produire le jeu du notebook (cellule 8) : c'est de la *supervision
faible* (weak supervision), documentée comme une limite du modèle.

Le tirage aléatoire est déterministe par commande (graine + identifiant) : le même
historique produit toujours les mêmes labels, quel que soit l'ordre de lecture.
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Sequence
from typing import Protocol

from ...domain.entities import OrderEntity

ZONE_PENALTY = {"centre": 0.0, "proche_banlieue": 0.10, "banlieue": 0.25, "rurale": 0.45}
WEATHER_PENALTY = {"normal": 0.0, "pluie": 0.10, "neige": 0.25, "orage": 0.30}
DEFAULT_PREPARATION_TIME_MIN = 25.0  # moyenne du générateur du notebook


class Labeler(Protocol):
    def label(self, orders: Sequence[OrderEntity]) -> list[int]: ...


def business_score(order: OrderEntity) -> float:
    """Score métier de la cellule 8 du notebook (avant sigmoïde)."""
    preparation = (
        DEFAULT_PREPARATION_TIME_MIN
        if order.preparation_time_min is None
        else order.preparation_time_min
    )
    return (
        2.5
        - 0.18 * order.distance_km
        - 0.035 * preparation
        - 0.035 * order.weight_kg
        - ZONE_PENALTY.get(order.delivery_zone, 0.0)
        - WEATHER_PENALTY.get(order.weather, 0.0)
        + 1.8 * order.stock_available
        + 1.3 * order.carrier_capacity
        + (0.15 if order.customer_type == "premium" else 0.0)
        - 0.40 * order.weekend
        - 0.08 * max(order.hour - 18, 0)
    )


def eligibility_probability(order: OrderEntity) -> float:
    return 1.0 / (1.0 + math.exp(-business_score(order)))


class BusinessRuleLabeler:
    """Label = tirage de Bernoulli de probabilité sigmoïde(score métier)."""

    def __init__(self, random_seed: int):
        self._random_seed = random_seed

    def _draw(self, order: OrderEntity, index: int) -> float:
        key = f"{self._random_seed}:{order.order_id or index}".encode()
        seed = int.from_bytes(hashlib.sha256(key).digest()[:8], "big")
        return random.Random(seed).random()

    def label(self, orders: Sequence[OrderEntity]) -> list[int]:
        return [
            int(self._draw(order, index) < eligibility_probability(order))
            for index, order in enumerate(orders)
        ]
