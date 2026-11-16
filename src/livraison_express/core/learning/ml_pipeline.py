"""Pipeline scikit-learn (cellule 24 du notebook) : prétraitement + régression logistique.

Une pipeline unique garantit que les mêmes transformations sont appliquées à
l'entraînement et à la prédiction.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .order_feature import CATEGORICAL_FEATURES, NUMERIC_FEATURES

MODEL_TYPE = "LogisticRegression"


def build_model_pipeline(random_seed: int) -> Pipeline:
    numeric = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric, NUMERIC_FEATURES),
            ("categorical", categorical, CATEGORICAL_FEATURES),
        ]
    )
    classifier = LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=random_seed
    )
    return Pipeline(steps=[("preprocessor", preprocessor), ("classifier", classifier)])
