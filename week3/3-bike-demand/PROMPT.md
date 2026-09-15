# Generation Prompts for 3-bike-demand

This file documents the AI-assisted development prompts used to generate each component of the bike-demand forecasting project for reproducibility and transparency.

---

## 1. Exploratory Data Analysis (`src/explore_data.py`)

### Prompt

```
Create a comprehensive exploratory data analysis (EDA) script for the Seoul Bike Demand dataset.

The script should implement the following functions as a professional machine learning engineer would:

1. Load the raw dataset from CSV (handle encoding if needed)
2. Examine dataset structure (shape, dtypes, first rows, column names)
3. Check data quality (missing values, duplicates)
4. Analyze the target variable "Rented Bike Count":
   - Descriptive statistics (mean, median, std, min, max, quartiles)
   - Distribution shape (skewness, kurtosis)
5. Analyze numerical features with summary statistics
6. Analyze categorical features with value counts
7. Explore temporal patterns:
   - Average demand by hour of day (peak and low hours)
   - Average demand by season
   - Average demand by holiday vs. non-holiday
8. Calculate feature correlations with the target variable
9. Identify high correlations between features (multicollinearity)
10. Detect outliers using the IQR method
11. Provide key insights and recommendations for data preparation and modeling

Output should be:
- Well-formatted, easy-to-read terminal output
- Clear section headers
- Concise statistics and insights
- Actionable recommendations for next steps

Keep the code simple, readable, and well-documented with Google-style docstrings.
```

### Purpose

Understand the dataset structure, identify patterns, detect data quality issues, and guide feature engineering decisions for machine learning modeling.

---

## How to Reproduce

To regenerate this script with the same or similar output:

1. Use the prompt above with an AI assistant (Claude, ChatGPT, Copilot, etc.)
2. Run it against the Seoul Bike Sharing Demand dataset
3. The output should provide identical insights about temporal patterns, feature correlations, and data quality

---

---

## 2. Data Preparation and Feature Engineering (`src/prepare_data.py`)

### Prompt

```
Create a data preparation and feature engineering script for the Seoul Bike Demand dataset.

The script should implement the following functions:

1. Load raw dataset from CSV
2. Handle multicollinearity:
   - Drop 'Dew point temperature' (correlation with temperature = 0.913)
   - Drop 'Date' column (replace with engineered features)
3. Create temporal features from 'Hour':
   - is_peak_hour: 1 if hour is 18-22 (6-10 PM, peak demand), 0 otherwise
   - is_night: 1 if hour is 0-6 (midnight-6 AM, low demand), 0 otherwise
   - is_working_day: binary encoding of 'Functioning Day' column
4. Encode categorical variables:
   - Convert 'Holiday' to binary: 'is_holiday' (1=Holiday, 0=No Holiday)
   - One-hot encode 'Seasons' (drop first to avoid multicollinearity)
5. Scale numerical features using StandardScaler:
   - Hour, Temperature(°C), Humidity(%), Wind speed, Visibility, Solar Radiation, Rainfall, Snowfall
6. Create temporal train/test split (chronological, no random shuffle):
   - Train: first 80% of data
   - Test: last 20% of data
   - Reason: Avoids data leakage in time series
7. Save processed data:
   - Train and test sets as CSV files
   - Scaler object as pickle file (for later prediction)
8. Include print statements throughout to show progress and statistics

Output should:
- Show each processing step clearly
- Display feature count at each stage
- Explain why each transformation is necessary
- Print final data shape and statistics
- Save train.csv, test.csv, and scaler.pkl to data/processed/

Keep the code simple, readable, and well-documented with Google-style docstrings.
```

### Purpose

Transform raw data into machine learning-ready format with engineered features, proper scaling, and temporal train/test split to ensure model reproducibility and prevent data leakage.

---

## 3. Model Training and Evaluation (`src/train.py`)

### Prompt

```
Create a model training and evaluation script for the Seoul Bike Demand regression task.

The script should implement the following:

1. Load processed data:
   - Load train.csv and test.csv from data/processed/
   - Load scaler.pkl for reference
2. Separate features (X) and target (y):
   - Target: 'Rented Bike Count'
   - Features: all other columns
3. Train two regression models:
   a. Gradient Boosting (primary model):
      - Use GradientBoostingRegressor
      - n_estimators=200, learning_rate=0.1, max_depth=7, random_state=42
   b. Random Forest (baseline):
      - Use RandomForestRegressor
      - n_estimators=100, max_depth=20, random_state=42
4. Evaluate both models on train and test sets:
   - Calculate MAE (Mean Absolute Error)
   - Calculate RMSE (Root Mean Squared Error)
   - Calculate R² Score
   - Print results for both train and test sets
   - Check for overfitting (ratio of test MAE to train MAE)
5. Display feature importance:
   - Show top 10 important features for each model
   - Use visual bars (█) for clarity
6. Compare models:
   - Show side-by-side comparison of test performance
   - Recommend the better model
7. Save trained models:
   - Save Gradient Boosting model as models/gradient_boosting_model.pkl
   - Save Random Forest model as models/random_forest_model.pkl
8. Include comprehensive print statements:
   - Show each processing step
   - Display hyperparameters
   - Show training progress
   - Display all metrics clearly
   - Provide recommendations for next steps

Output should be:
- Clear section headers for each step
- Readable metrics and comparisons
- Feature importance visualization
- Model comparison summary
- Recommendations for production deployment

Keep the code simple, readable, and well-documented with Google-style docstrings.
```

### Purpose

Train machine learning models on prepared data, evaluate performance on train and test sets, compare models, and save the best model for inference and production deployment.

---

## 4. Predictions and Inference (`src/predict.py`)

### Prompt

```
Create a predictions and inference script for the Seoul Bike Demand forecasting models.

The script should implement the following:

1. Load trained models:
   - Load gradient_boosting_model.pkl
   - Load random_forest_model.pkl
   - Load scaler.pkl (for reference)
2. Load test data:
   - Load test.csv from data/processed/
   - Separate features (X_test) and target (y_test)
3. Make predictions:
   - Use Gradient Boosting model to predict
   - Use Random Forest model to predict
4. Evaluate predictions:
   - Calculate MAE (Mean Absolute Error)
   - Calculate RMSE (Root Mean Squared Error)
   - Calculate R² Score
   - Analyze residuals (actual - predicted)
   - Print residual statistics
5. Display sample predictions:
   - Show first 10 predictions with actual values
   - Include prediction error and error percentage for each
6. Analyze prediction distributions:
   - Show distribution statistics for each model's predictions
   - Compare with actual test data distribution
7. Save predictions:
   - Save Gradient Boosting predictions to predictions/gradient_boosting_predictions.csv
   - Save Random Forest predictions to predictions/random_forest_predictions.csv
   - Include columns: actual_demand, predicted_demand, error, error_percentage
8. Compare models:
   - Side-by-side comparison of MAE, RMSE, R²
   - Recommend better model based on metrics
9. Include comprehensive print statements:
   - Show each step progress
   - Display all metrics clearly
   - Provide actionable recommendations
   - Suggest next steps (deployment, monitoring, retraining)

Output should be:
- Clear section headers for each step
- Readable metrics and comparisons
- Sample predictions with interpretable errors
- Distribution analysis
- Model recommendations for production

Keep the code simple, readable, and well-documented with Google-style docstrings.
```

### Purpose

Load trained models, make predictions on test data, evaluate prediction quality, analyze residuals and distributions, and save results for stakeholder review and production deployment.

---

## Reproducibility and Deployment

This complete pipeline (EDA → Preparation → Training → Predictions) can be reproduced by:

1. Running the documented prompts with any AI assistant
2. Using the same Seoul Bike Sharing Dataset
3. Following the same hyperparameters and preprocessing steps
4. All scripts include print statements for transparency and debugging

For production deployment:
- Use the trained models in `models/` directory
- Preprocess new data using the same steps in `prepare_data.py`
- Use `predict.py` as template for batch or real-time predictions
- Monitor prediction accuracy and retrain periodically

---

## 5. Lesson 3 Assignment: Streamlit and Local Ollama Integration

### Architecture and implementation prompt

```text
Extend the existing Bike Demand project without replacing its ML pipeline.
Use the better-performing trained Gradient Boosting model for one hourly
prediction. Keep app.py for Streamlit UI, src/predict.py for ML inference, and
src/llm_service.py for local Ollama calls. The local LLM must explain the ML
result or recommend an operational action; it must not calculate or replace the
prediction. Show the ML result even when Ollama is unavailable.
```

### Preprocessing review prompt

```text
Inspect the saved scaler, trained model, and processed training CSV before
implementing single-row inference. Recreate the eight scaled numerical fields,
the peak/night/working-day/holiday indicators, and the three season dummy
columns in exactly the same order used during training. Reject missing or
invalid inputs and prevent a negative displayed rental count.
```

### Validation prompt

```text
Validate the assignment requirements using this exact mapping:

R1 — Machine Learning Prediction: Valid user input produces a bike-demand
prediction using the trained Gradient Boosting model.

R2 — Local LLM Capability: The local Ollama `llama3.2:1b` model provides an
explanation/recommendation that complements the ML prediction.

R3 — Failure Handling: Invalid or missing input is handled clearly, AND if
Ollama is unavailable, the ML prediction remains available while the
application displays a guidance-unavailable message.

R4 — Separation of Responsibilities: `app.py` handles the user interface,
`src/predict.py` handles ML prediction, and `src/llm_service.py` handles local
LLM interaction.

For R1 and R2, test normal operation. For R3, test both invalid input and an
unavailable Ollama service. For R4, inspect the project structure. Add small
focused tests for feature order, nonnegative output, input validation, prompt
responsibility, and the Ollama failure path. Do not use a hosted LLM or an
OpenAI API.
```

### Requirements traceability

| Requirement | Validation | Evidence | Result |
| --- | --- | --- | --- |
| R1 | Normal operation | Valid input produces an ML bike-demand prediction | Pass |
| R2 | Normal operation | Local Ollama provides guidance based on the ML prediction | Pass |
| R3 | Invalid input + Ollama unavailable | Invalid input is handled clearly and the ML prediction remains available if Ollama fails | Pass |
| R4 | Project structure inspection | UI, ML prediction, and LLM interaction are separated into `app.py`, `src/predict.py`, and `src/llm_service.py` | Pass |

### Human review notes

The saved artifacts were inspected before implementation. The scaler and model
feature orders were treated as authoritative, Gradient Boosting was selected
from the measured test results, and the generated tests were run inside Docker
before application validation.
