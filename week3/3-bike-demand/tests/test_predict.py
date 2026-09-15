import numpy as np
import pytest

from src.predict import (
    InputValidationError,
    MODEL_FEATURES,
    NUMERICAL_FEATURES,
    predict_hourly_demand,
)


VALID_OBSERVATION = {
    'hour': 19,
    'temperature_c': 20,
    'humidity_percent': 50,
    'wind_speed_m_s': 2,
    'visibility_10m': 1500,
    'solar_radiation_mj_m2': 0.5,
    'rainfall_mm': 0,
    'snowfall_cm': 0,
    'season': 'Summer',
    'is_holiday': False,
    'is_functioning_day': True,
}


class IdentityScaler:
    feature_names_in_ = np.array(NUMERICAL_FEATURES)

    def transform(self, frame):
        assert list(frame.columns) == NUMERICAL_FEATURES
        return frame.to_numpy()


class RecordingModel:
    feature_names_in_ = np.array(MODEL_FEATURES)

    def __init__(self, result):
        self.result = result
        self.received = None

    def predict(self, frame):
        self.received = frame
        return np.array([self.result])


def test_single_prediction_uses_training_feature_order():
    model = RecordingModel(321.4)

    result = predict_hourly_demand(
        VALID_OBSERVATION, model=model, scaler=IdentityScaler()
    )

    assert result == 321
    assert list(model.received.columns) == MODEL_FEATURES
    assert model.received.iloc[0]['is_peak_hour'] == 1
    assert model.received.iloc[0]['season_Summer'] == 1


def test_negative_prediction_is_clamped_to_zero():
    result = predict_hourly_demand(
        VALID_OBSERVATION,
        model=RecordingModel(-25.7),
        scaler=IdentityScaler(),
    )

    assert result == 0


def test_missing_observation_value_is_rejected():
    observation = {**VALID_OBSERVATION}
    del observation['temperature_c']

    with pytest.raises(InputValidationError, match='Temperature is required'):
        predict_hourly_demand(
            observation, model=RecordingModel(100), scaler=IdentityScaler()
        )


@pytest.mark.parametrize(
    ('field', 'value', 'message'),
    [
        ('hour', 24, 'Hour must be'),
        ('humidity_percent', 101, 'Humidity must be'),
        ('rainfall_mm', -1, 'Rainfall cannot be negative'),
    ],
)
def test_invalid_observation_is_rejected(field, value, message):
    observation = {**VALID_OBSERVATION, field: value}

    with pytest.raises(InputValidationError, match=message):
        predict_hourly_demand(
            observation, model=RecordingModel(100), scaler=IdentityScaler()
        )
