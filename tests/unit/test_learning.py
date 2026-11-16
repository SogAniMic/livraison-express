import numpy as np
import pytest

from livraison_express.core.learning.labeling import BusinessRuleLabeler, eligibility_probability
from livraison_express.core.learning.ml_predict import MLPredict
from livraison_express.core.learning.order_feature import FEATURE_COLUMNS, orders_to_dataframe
from livraison_express.core.learning.train_test_splitter import TrainTestSplitter
from livraison_express.domain.exceptions import NotEnoughTrainingDataError
from tests.conftest import make_order


class FakeModel:
    """Doublure : vérifie l'orchestration sans entraîner de vrai modèle."""

    def __init__(self, probability):
        self.probability = probability
        self.received = None

    def predict_proba(self, frame):
        self.received = frame
        return np.array([[1 - self.probability, self.probability]])


def test_order_id_is_never_a_feature():
    frame = orders_to_dataframe([make_order()])
    assert list(frame.columns) == FEATURE_COLUMNS
    assert "order_id" not in frame.columns


def test_missing_preparation_time_becomes_nan_for_imputation():
    frame = orders_to_dataframe([make_order(preparation_time_min=None)])
    assert frame["preparation_time_min"].isna().all()


@pytest.mark.parametrize(("probability", "decision"), [(0.51, "oui"), (0.49, "non")])
def test_threshold_turns_probability_into_decision(probability, decision):
    model = FakeModel(probability)
    prediction = MLPredict(model, threshold=0.5, model_version="9.9.9").predict(make_order())
    assert prediction.decision == decision
    assert prediction.express_eligible is (decision == "oui")
    assert prediction.model_version == "9.9.9"
    assert list(model.received.columns) == FEATURE_COLUMNS


def test_splitter_rejects_single_class():
    with pytest.raises(NotEnoughTrainingDataError):
        TrainTestSplitter(42).split([make_order()] * 10, [1] * 10)


def test_splitter_rejects_misaligned_inputs():
    with pytest.raises(ValueError):
        TrainTestSplitter(42).split([make_order()] * 3, [0, 1])


def test_business_rule_penalises_distance_and_bad_weather():
    near = eligibility_probability(make_order(distance_km=1))
    far = eligibility_probability(make_order(distance_km=30))
    storm = eligibility_probability(make_order(distance_km=1, weather="orage"))
    assert near > far
    assert near > storm


def test_labeler_is_deterministic_and_order_independent():
    orders = [make_order(order_id=f"ERP-{i:08d}", distance_km=i % 20) for i in range(200)]
    labeler = BusinessRuleLabeler(42)
    labels = labeler.label(orders)
    reversed_labels = labeler.label(list(reversed(orders)))
    assert labels == list(reversed(reversed_labels))
    assert set(labels) == {0, 1}
