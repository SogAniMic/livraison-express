from livraison_express.core.retraining import RetrainingScheduler, decide
from tests.conftest import make_order


def test_decide_without_model_trains_when_enough_rows():
    assert decide(1000, None, 500, 200).should_train


def test_decide_waits_for_minimum_rows():
    assert not decide(100, None, 500, 200).should_train


def test_decide_waits_for_enough_new_orders():
    assert not decide(1200, 1000, 500, 200).should_train
    assert decide(1500, 1000, 500, 200).should_train


def test_scheduler_trains_then_retrains_only_after_new_data(container):
    scheduler = RetrainingScheduler(container, sleep=lambda _: None)
    assert scheduler.run_once().should_train  # pas encore de modèle
    assert not scheduler.run_once().should_train  # rien de nouveau

    repository = container.repositories.training_orders
    for index in range(100):
        repository._orders[f"NEW-{index}"] = make_order(order_id=f"NEW-{index}")
        repository._labels[f"NEW-{index}"] = index % 2
    assert scheduler.run_once().should_train
    assert container.model_card().training_rows == 900


def test_run_once_does_not_sleep_after_the_last_cycle(container):
    sleeps = []
    RetrainingScheduler(container, sleep=sleeps.append).run_forever(max_iterations=1)
    assert sleeps == []
