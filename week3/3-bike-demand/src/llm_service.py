"""Local Ollama integration for bike-demand operational guidance."""

import os
from typing import Mapping

import requests


DEFAULT_OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
DEFAULT_OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:1b')
DEFAULT_TIMEOUT = (3.0, 60.0)


class OllamaUnavailableError(RuntimeError):
    """Raised when local AI guidance cannot be obtained from Ollama."""


def build_guidance_prompt(prediction: int, observation: Mapping) -> str:
    """Build a prompt that keeps prediction and explanation responsibilities separate."""
    return f"""
A trained Gradient Boosting machine-learning model has already predicted
{prediction} bike rentals for the selected hour. Treat that value as final.

Conditions:
- Hour: {observation['hour']}:00
- Temperature: {observation['temperature_c']} °C
- Humidity: {observation['humidity_percent']}%
- Wind speed: {observation['wind_speed_m_s']} m/s
- Visibility: {observation['visibility_10m']} (10 m units)
- Solar radiation: {observation['solar_radiation_mj_m2']} MJ/m2
- Rainfall: {observation['rainfall_mm']} mm
- Snowfall: {observation['snowfall_cm']} cm
- Season: {observation['season']}
- Holiday: {'Yes' if observation['is_holiday'] else 'No'}
- Functioning day: {'Yes' if observation['is_functioning_day'] else 'No'}

In no more than three short sentences, explain the predicted demand and give one
practical bike-availability or staffing recommendation. Do not calculate,
recalculate, revise, or replace the ML prediction. Do not provide a different
prediction. Use only the conditions listed above, preserve every Yes/No value
exactly, and do not call demand high or low because no comparison threshold was
provided.
""".strip()


def get_operational_guidance(
    prediction: int,
    observation: Mapping,
    *,
    ollama_url: str = DEFAULT_OLLAMA_URL,
    model: str = DEFAULT_OLLAMA_MODEL,
    timeout=DEFAULT_TIMEOUT,
) -> str:
    """Request short guidance from a local Ollama model."""
    endpoint = f"{ollama_url.rstrip('/')}/api/generate"
    payload = {
        'model': model,
        'prompt': build_guidance_prompt(prediction, observation),
        'stream': False,
        'options': {'temperature': 0.2},
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        guidance = response.json().get('response', '').strip()
    except (requests.RequestException, ValueError, TypeError, AttributeError) as exc:
        raise OllamaUnavailableError(
            "AI guidance is unavailable because the local Ollama service "
            "could not complete the request."
        ) from exc

    if not guidance:
        raise OllamaUnavailableError(
            "AI guidance is unavailable because the local Ollama service "
            "returned an empty response."
        )
    return guidance
