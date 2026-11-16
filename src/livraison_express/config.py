"""Configuration lue depuis l'environnement (principe 12-factor).

Aucun secret, aucune URL de base de données et aucun chemin de modèle n'est écrit en
dur dans le code métier. Priorité : variables d'environnement > fichier `.env` >
valeurs par défaut ci-dessous. `.env.example` documente chaque clé.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Général ---
    environment: Literal["local", "test", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    random_seed: int = 42

    # --- Modèle (ADR-0000) ---
    model_path: str = "artifacts/express_delivery_model.joblib"
    model_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    model_version: str = "1.0.0"

    # --- Stockage des commandes (ADR-0005) ---
    # memory:// (dev, données synthétiques) ou mongodb://hote:27017
    order_repository_url: SecretStr = SecretStr("memory://")
    mongo_database: str = "livraison_express"
    # Collection alimentée par l'ETL depuis l'ERP : lecture seule pour l'application.
    mongo_erp_collection: str = "orders"
    # Collection propre à l'application : commandes reçues via POST /v1/orders.
    mongo_collected_collection: str = "api_orders"
    mongo_timeout_ms: int = 3000

    # --- Réentraînement (ADR-0007) ---
    retrain_min_new_orders: int = Field(default=500, ge=1)
    retrain_check_interval_seconds: float = Field(default=300, gt=0)
    min_training_rows: int = Field(default=200, ge=10)

    @property
    def repository_scheme(self) -> str:
        return self.order_repository_url.get_secret_value().split("://", 1)[0]
