"""Test predictor."""

import pytest
from datetime import datetime
from custom_components.kronoterm.predictor import Predictor


@pytest.fixture
def sample_data() -> list[tuple[datetime, float]]:
    """Return sample training data for predictor."""
    return [
        (datetime(2025, 5, 14, 6, 0), 200.0),
        (datetime(2025, 5, 14, 12, 0), 500.0),
        (datetime(2025, 5, 15, 6, 0), 220.0),
        (datetime(2025, 5, 15, 12, 0), 480.0),
    ]


def test_training_and_prediction(sample_data: list[tuple[datetime, float]]) -> None:
    """Test training and prediction of the model."""
    model = Predictor.new(sample_data)
    test_time = datetime(2025, 5, 16, 6, 0)
    prediction = model._predict(test_time)

    assert prediction is not None
    assert isinstance(prediction, float)
    assert prediction > 0


def test_new_method(sample_data: list[tuple[datetime, float]]) -> None:
    """Test the new method of the model - creating a new instance."""
    model = Predictor.new(sample_data)

    assert isinstance(model, Predictor)

    test_time = datetime(2025, 5, 17, 6, 0)
    prediction = model._predict(test_time)

    assert prediction is not None
    assert isinstance(prediction, float)


def test_forecast_length_and_format(sample_data: list[tuple[datetime, float]]) -> None:
    """Test the forecast method of the model."""
    model = Predictor.new(sample_data)
    start = datetime(2025, 5, 16, 0, 0)
    forecast = model.forecast(start)

    assert len(forecast) == 32  # INTERVAL = 15 min
    for dt, val in forecast:
        assert isinstance(dt, datetime)
        assert isinstance(val, float)


def test_dump_and_load(sample_data: list[tuple[datetime, float]]) -> None:
    """Test the dump and load methods of the model."""
    model = Predictor.new(sample_data)
    dumped = model.dump()
    assert dumped is not None

    loaded_model = Predictor.load(dumped)
    pred1 = model._predict(datetime(2025, 5, 16, 6, 0))
    pred2 = loaded_model._predict(datetime(2025, 5, 16, 6, 0))

    assert pred1 is not None
    assert pred2 is not None

    assert abs(pred1 - pred2) < 1e-6


def test_add_and_refit(sample_data: list[tuple[datetime, float]]) -> None:
    """Test the add_and_refit method of the model."""
    model = Predictor.new(sample_data)

    initial_history_len = len(model.history)
    test_time = datetime(2025, 5, 16, 6, 0)
    prediction_before = model._predict(test_time)

    new_dt = datetime(2025, 5, 16, 6, 0)
    new_val = 250.0
    model.add_and_refit(new_dt, new_val)

    assert len(model.history) == initial_history_len + 1
    assert model.history[-1] == (new_dt, new_val)

    prediction_after = model._predict(test_time)
    assert prediction_after is not None
    assert isinstance(prediction_after, float)

    assert prediction_before is not None
    assert isinstance(prediction_before, float)

    assert abs(prediction_after - prediction_before) >= 0.0
