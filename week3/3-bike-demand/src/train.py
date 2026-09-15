"""
Model Training and Evaluation for Seoul Bike Demand Forecasting.

This module handles:
- Loading prepared train and test data
- Training machine learning models
- Evaluating model performance
- Saving trained models for inference
"""

import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os


def load_processed_data(data_dir: str = 'data/processed/') -> tuple:
    """Load processed train and test data."""
    print(f"\n{'='*60}")
    print("STEP 1: LOADING PROCESSED DATA")
    print(f"{'='*60}")

    train_file = os.path.join(data_dir, 'train.csv')
    test_file = os.path.join(data_dir, 'test.csv')
    scaler_file = os.path.join(data_dir, 'scaler.pkl')

    # Load data
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)

    # Load scaler
    with open(scaler_file, 'rb') as f:
        scaler = pickle.load(f)

    print(f"✓ Loaded train data: {train_df.shape}")
    print(f"✓ Loaded test data: {test_df.shape}")
    print(f"✓ Loaded scaler object")

    return train_df, test_df, scaler


def separate_features_target(df: pd.DataFrame, target_col: str = 'Rented Bike Count') -> tuple:
    """Separate features and target variable."""
    X = df.drop(target_col, axis=1)
    y = df[target_col]
    return X, y


def train_gradient_boosting(X_train: pd.DataFrame, y_train: pd.Series) -> object:
    """Train Gradient Boosting model."""
    print(f"\n{'='*60}")
    print("STEP 2: TRAINING GRADIENT BOOSTING MODEL")
    print(f"{'='*60}")

    print(f"\nModel: GradientBoostingRegressor")
    print(f"Hyperparameters:")
    print(f"  - n_estimators: 200 (number of trees)")
    print(f"  - learning_rate: 0.1 (shrinkage)")
    print(f"  - max_depth: 7 (tree depth)")
    print(f"  - random_state: 42 (reproducibility)")

    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=7,
        random_state=42,
        verbose=0
    )

    print(f"\n⏳ Training on {X_train.shape[0]} samples with {X_train.shape[1]} features...")
    model.fit(X_train, y_train)
    print(f"✓ Training complete")

    return model


def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> object:
    """Train Random Forest model as baseline."""
    print(f"\nModel: RandomForestRegressor (baseline)")
    print(f"Hyperparameters:")
    print(f"  - n_estimators: 100 (number of trees)")
    print(f"  - max_depth: 20 (tree depth)")
    print(f"  - random_state: 42 (reproducibility)")

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=20,
        random_state=42,
        n_jobs=-1
    )

    print(f"⏳ Training on {X_train.shape[0]} samples with {X_train.shape[1]} features...")
    model.fit(X_train, y_train)
    print(f"✓ Training complete")

    return model


def evaluate_model(model, X_train: pd.DataFrame, y_train: pd.Series,
                  X_test: pd.DataFrame, y_test: pd.Series, model_name: str) -> dict:
    """Evaluate model on train and test sets."""
    print(f"\n{'='*60}")
    print(f"STEP 3: EVALUATING {model_name.upper()}")
    print(f"{'='*60}")

    # Predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    # Calculate metrics
    metrics = {
        'train_mae': mean_absolute_error(y_train, y_train_pred),
        'test_mae': mean_absolute_error(y_test, y_test_pred),
        'train_rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
        'test_rmse': np.sqrt(mean_squared_error(y_test, y_test_pred)),
        'train_r2': r2_score(y_train, y_train_pred),
        'test_r2': r2_score(y_test, y_test_pred),
    }

    # Print results
    print(f"\nTraining Set Performance:")
    print(f"  MAE (Mean Absolute Error):  {metrics['train_mae']:.2f} bikes")
    print(f"  RMSE (Root Mean Squared Error): {metrics['train_rmse']:.2f} bikes")
    print(f"  R² Score:                   {metrics['train_r2']:.4f}")

    print(f"\nTest Set Performance:")
    print(f"  MAE (Mean Absolute Error):  {metrics['test_mae']:.2f} bikes")
    print(f"  RMSE (Root Mean Squared Error): {metrics['test_rmse']:.2f} bikes")
    print(f"  R² Score:                   {metrics['test_r2']:.4f}")

    # Overfitting check
    overfitting_ratio = metrics['test_mae'] / metrics['train_mae']
    print(f"\nOverfitting Check:")
    print(f"  Test MAE / Train MAE Ratio: {overfitting_ratio:.2f}")
    if overfitting_ratio > 1.2:
        print(f"  ⚠️  Warning: Model may be overfitting (ratio > 1.2)")
    else:
        print(f"  ✓ Model generalization looks good")

    return metrics


def print_feature_importance(model, X_train: pd.DataFrame, top_n: int = 10) -> None:
    """Print feature importance for tree-based models."""
    if hasattr(model, 'feature_importances_'):
        print(f"\nTop {top_n} Important Features:")
        importances = pd.DataFrame({
            'feature': X_train.columns,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)

        for idx, row in importances.head(top_n).iterrows():
            bar_length = int(row['importance'] * 50)
            bar = '█' * bar_length
            print(f"  {row['feature']:25s} {bar} {row['importance']:.4f}")


def save_model(model, filepath: str) -> None:
    """Save trained model."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    print(f"✓ Model saved: {filepath}")


def main(data_dir: str = 'data/processed/',
         models_dir: str = 'models/') -> None:
    """Run complete model training pipeline."""
    print("\n" + "="*60)
    print("SEOUL BIKE DEMAND - MODEL TRAINING & EVALUATION")
    print("="*60)

    # Load data
    train_df, test_df, scaler = load_processed_data(data_dir)

    # Separate features and target
    X_train, y_train = separate_features_target(train_df)
    X_test, y_test = separate_features_target(test_df)

    print(f"\n{'='*60}")
    print("DATA SUMMARY")
    print(f"{'='*60}")
    print(f"Training set:  {X_train.shape[0]} samples, {X_train.shape[1]} features")
    print(f"Test set:      {X_test.shape[0]} samples, {X_test.shape[1]} features")
    print(f"Target variable: {y_train.name}")

    # Train models
    print(f"\n{'='*60}")
    print("TRAINING MODELS")
    print(f"{'='*60}")

    # Gradient Boosting (primary model)
    gb_model = train_gradient_boosting(X_train, y_train)
    gb_metrics = evaluate_model(gb_model, X_train, y_train, X_test, y_test, 'Gradient Boosting')
    print_feature_importance(gb_model, X_train)

    # Random Forest (baseline)
    print(f"\n")
    rf_model = train_random_forest(X_train, y_train)
    rf_metrics = evaluate_model(rf_model, X_train, y_train, X_test, y_test, 'Random Forest')
    print_feature_importance(rf_model, X_train)

    # Model comparison
    print(f"\n{'='*60}")
    print("MODEL COMPARISON")
    print(f"{'='*60}")
    print(f"\nTest Set Performance Summary:")
    print(f"{'Model':<20} {'MAE':<12} {'RMSE':<12} {'R²':<10}")
    print(f"{'-'*54}")
    print(f"{'Gradient Boosting':<20} {gb_metrics['test_mae']:<12.2f} {gb_metrics['test_rmse']:<12.2f} {gb_metrics['test_r2']:<10.4f}")
    print(f"{'Random Forest':<20} {rf_metrics['test_mae']:<12.2f} {rf_metrics['test_rmse']:<12.2f} {rf_metrics['test_r2']:<10.4f}")

    # Save models
    print(f"\n{'='*60}")
    print("SAVING MODELS")
    print(f"{'='*60}")
    save_model(gb_model, os.path.join(models_dir, 'gradient_boosting_model.pkl'))
    save_model(rf_model, os.path.join(models_dir, 'random_forest_model.pkl'))

    # Recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    if gb_metrics['test_r2'] > rf_metrics['test_r2']:
        print(f"✓ Gradient Boosting is the better model (higher R²)")
        print(f"  Use 'gradient_boosting_model.pkl' for predictions")
    else:
        print(f"✓ Random Forest is the better model (higher R²)")
        print(f"  Use 'random_forest_model.pkl' for predictions")

    print(f"\nNext steps:")
    print(f"  1. Use the best model for predictions on new data")
    print(f"  2. Analyze residuals to identify improvement areas")
    print(f"  3. Hyperparameter tuning if needed")
    print(f"  4. Deploy model to production")

    print(f"\n{'='*60}")
    print("MODEL TRAINING COMPLETE ✓")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
