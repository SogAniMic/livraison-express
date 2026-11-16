"""Abstraction : où l'application range le modèle entraîné et sa model card.

Un service de prédiction ne réentraîne jamais au démarrage : il charge un artefact
produit par un job d'entraînement (séparation entraîner / servir).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..domain.entities import ModelEntity


class ModelRepository(ABC):
    @abstractmethod
    def save(self, model: object, model_card: ModelEntity) -> None:
        """Écrit le modèle et ses métadonnées de façon cohérente."""

    @abstractmethod
    def load(self) -> tuple[object, ModelEntity] | None:
        """Retourne (modèle, model card) ou `None` si aucun artefact n'existe."""

    @abstractmethod
    def revision(self) -> str | None:
        """Identifiant de la révision stockée : change à chaque nouvel entraînement."""
