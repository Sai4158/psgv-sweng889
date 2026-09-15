import requests
import pytest

from src.llm_service import (
    OllamaUnavailableError,
    build_guidance_prompt,
    get_operational_guidance,
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


def test_prompt_assigns_prediction_only_to_ml_model():
    prompt = build_guidance_prompt(321, VALID_OBSERVATION)

    assert 'already predicted\n321 bike rentals' in prompt
    assert 'Do not calculate' in prompt
    assert 'Do not provide a different' in prompt


def test_ollama_response_is_returned(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {'response': 'Stage additional bikes before the peak hour.'}

    monkeypatch.setattr(requests, 'post', lambda *args, **kwargs: FakeResponse())

    guidance = get_operational_guidance(321, VALID_OBSERVATION)

    assert guidance == 'Stage additional bikes before the peak hour.'


def test_ollama_connection_failure_has_clear_error(monkeypatch):
    def fail_request(*args, **kwargs):
        raise requests.ConnectionError('offline')

    monkeypatch.setattr(requests, 'post', fail_request)

    with pytest.raises(OllamaUnavailableError, match='AI guidance is unavailable'):
        get_operational_guidance(321, VALID_OBSERVATION)
