"""Streamlit interface for ML bike-demand prediction and local AI guidance."""

import streamlit as st

from src.llm_service import OllamaUnavailableError, get_operational_guidance
from src.predict import InputValidationError, predict_hourly_demand


def parse_number(raw_value: str, label: str) -> float:
    """Parse a required numeric Streamlit text input."""
    value = raw_value.strip()
    if not value:
        raise InputValidationError(f"{label} is required.")
    try:
        return float(value)
    except ValueError as exc:
        raise InputValidationError(f"{label} must be a number.") from exc


st.set_page_config(page_title="Seoul Bike Demand", page_icon="🚲")
st.title("Seoul Bike Demand")
st.write(
    "Enter one hour of operating conditions. The trained machine-learning "
    "model calculates demand; the local AI only explains the result."
)

with st.form("prediction_form"):
    left, right = st.columns(2)

    with left:
        hour = st.text_input("Hour (0–23)", "8")
        temperature = st.text_input("Temperature (°C)", "15")
        humidity = st.text_input("Humidity (%)", "55")
        wind_speed = st.text_input("Wind speed (m/s)", "2")
        visibility = st.text_input("Visibility (10 m units)", "1500")

    with right:
        solar_radiation = st.text_input("Solar radiation (MJ/m2)", "0.5")
        rainfall = st.text_input("Rainfall (mm)", "0")
        snowfall = st.text_input("Snowfall (cm)", "0")
        season = st.selectbox("Season", ("Autumn", "Spring", "Summer", "Winter"))
        holiday = st.selectbox("Holiday?", ("No", "Yes"))
        functioning_day = st.selectbox("Functioning day?", ("Yes", "No"))

    submitted = st.form_submit_button("Predict demand", type="primary")

if submitted:
    try:
        observation = {
            'hour': parse_number(hour, 'Hour'),
            'temperature_c': parse_number(temperature, 'Temperature'),
            'humidity_percent': parse_number(humidity, 'Humidity'),
            'wind_speed_m_s': parse_number(wind_speed, 'Wind speed'),
            'visibility_10m': parse_number(visibility, 'Visibility'),
            'solar_radiation_mj_m2': parse_number(
                solar_radiation, 'Solar radiation'
            ),
            'rainfall_mm': parse_number(rainfall, 'Rainfall'),
            'snowfall_cm': parse_number(snowfall, 'Snowfall'),
            'season': season,
            'is_holiday': holiday == 'Yes',
            'is_functioning_day': functioning_day == 'Yes',
        }
        prediction = predict_hourly_demand(observation)
    except InputValidationError as exc:
        st.error(f"Invalid input: {exc}")
    except (FileNotFoundError, RuntimeError) as exc:
        st.error(f"The ML prediction could not be created: {exc}")
    else:
        st.subheader("Machine-learning prediction")
        st.metric("Predicted hourly rentals", prediction)
        st.caption("Calculated by the trained Gradient Boosting model.")

        st.subheader("Local AI guidance")
        with st.spinner("Asking the local Ollama model..."):
            try:
                guidance = get_operational_guidance(prediction, observation)
            except OllamaUnavailableError:
                st.warning(
                    "AI guidance is unavailable. The machine-learning "
                    "prediction above is still available."
                )
            else:
                st.info(guidance)
