"""Erreurs du domaine.

Les couches supérieures (API, CLI) ne connaissent que ces erreurs, jamais celles de
pymongo ou de scikit-learn : l'infrastructure traduit ses erreurs techniques ici
(principe d'inversion de dépendance, et pas de fuite d'informations techniques).
"""


class LivraisonExpressError(Exception):
    """Racine des erreurs applicatives."""


class InvalidOrderError(LivraisonExpressError):
    """Une commande ne respecte pas le contrat de données."""

    def __init__(self, message: str, details: list[str] | None = None):
        super().__init__(message)
        self.details = details or []


class OrderStoreUnavailableError(LivraisonExpressError):
    """Le support de stockage des commandes est injoignable."""


class ModelUnavailableError(LivraisonExpressError):
    """Aucun modèle entraîné n'est disponible pour prédire."""


class NotEnoughTrainingDataError(LivraisonExpressError):
    """Le jeu d'entraînement est vide ou ne contient qu'une seule classe."""
