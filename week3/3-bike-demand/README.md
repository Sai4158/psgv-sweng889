# Seoul Bike Demand with Local AI Guidance

This Streamlit application predicts hourly bike-rental demand with the trained
Gradient Boosting model from the course Bike Demand pipeline. After displaying
the ML prediction, it asks a local `llama3.2:1b` model running in Ollama for a
short explanation and operational recommendation.

The Ollama model does not calculate or replace the bike-demand prediction. No
OpenAI API, hosted LLM, API key, or commercial AI service is used.

## Assignment requirements

- **R1 — Machine Learning Prediction:** Valid user input produces a bike-demand
  prediction using the trained Gradient Boosting model.
- **R2 — Local LLM Capability:** The local Ollama `llama3.2:1b` model provides an
  explanation/recommendation that complements the ML prediction.
- **R3 — Failure Handling:** Invalid or missing input is handled clearly, AND if
  Ollama is unavailable, the ML prediction remains available while the
  application displays a guidance-unavailable message.
- **R4 — Separation of Responsibilities:** `app.py` handles the user interface,
  `src/predict.py` handles ML prediction, and `src/llm_service.py` handles local
  LLM interaction.

## Responsibilities

- `app.py`: Streamlit inputs and result display
- `src/predict.py`: validation, feature engineering, scaling, and ML prediction
- `src/llm_service.py`: local Ollama request and error handling
- `src/prepare_data.py`: existing preprocessing pipeline
- `src/train.py`: existing model-training pipeline

## Install dependencies

Docker installs the required Python packages from `requirements.txt` when it
builds the application image. Build the image with:

```powershell
docker compose build
```

## Prepare the ML artifacts

Place the course dataset at `data/raw/SeoulBikeData.csv`, then run:

```powershell
docker compose run --rm bike-demand python src/prepare_data.py
docker compose run --rm bike-demand python src/train.py
```

These commands create the ignored files under `data/processed/` and `models/`
that the application needs.

## Run the application

```powershell
docker compose up --build
```

The first run pulls the local `llama3.2:1b` model into a persistent Docker
volume. Open <http://localhost:8501> after the services are ready.

Stop the services with:

```powershell
docker compose down
```

## Input and failure handling

The form requires hour, weather measurements, season, holiday status, and
functioning-day status. Missing, nonnumeric, out-of-range, and impossible
negative weather measurements produce a clear validation message.

If Ollama is stopped or cannot answer, the Gradient Boosting prediction remains
visible and the page reports that AI guidance is unavailable.

## Validation

| Requirement | Validation | Evidence | Result |
| --- | --- | --- | --- |
| R1 | Normal operation | Valid input produces an ML bike-demand prediction | Pass |
| R2 | Normal operation | Local Ollama provides guidance based on the ML prediction | Pass |
| R3 | Invalid input + Ollama unavailable | Invalid input is handled clearly and the ML prediction remains available if Ollama fails | Pass |
| R4 | Project structure inspection | UI, ML prediction, and LLM interaction are separated into `app.py`, `src/predict.py`, and `src/llm_service.py` | Pass |

Run the focused automated tests inside Docker:

```powershell
docker compose run --rm bike-demand python -m pytest
```

The required manual checks are:

1. R1 and R2: valid input shows an ML prediction followed by local AI guidance.
2. R3: invalid input shows a clear error and does not attempt prediction.
3. R3: with Ollama unavailable, the ML prediction still appears with a warning.
4. R4: inspect the project structure to confirm that UI, ML prediction, and
   local LLM interaction are separated into their required files.
