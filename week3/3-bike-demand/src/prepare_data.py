"""
Data Preparation and Feature Engineering for Seoul Bike Demand.

This module handles:
- Loading raw data
- Feature engineering (temporal features, encoding categoricals)
- Handling multicollinearity
- Scaling features
- Temporal train/test split
- Saving processed datasets
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os


def load_raw_data(filepath: str) -> pd.DataFrame:
    """Load raw dataset."""
    print(f"\n{'='*60}")
    print("STEP 1: LOADING RAW DATA")
    print(f"{'='*60}")
    df = pd.read_csv(filepath, encoding='latin-1')
    print(f"✓ Loaded {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"  Columns: {list(df.columns)}")
    return df


def drop_multicollinear_features(df: pd.DataFrame) -> pd.DataFrame:
    """Remove highly correlated features."""
    print(f"\n{'='*60}")
    print("STEP 2: HANDLING MULTICOLLINEARITY")
    print(f"{'='*60}")

    # Drop dew point temperature (correlation with temperature = 0.913)
    if 'Dew point temperature(°C)' in df.columns:
        df = df.drop('Dew point temperature(°C)', axis=1)
        print("✓ Dropped 'Dew point temperature(°C)' (corr with temp: 0.913)")

    # Drop Date (will use extracted features instead)
    if 'Date' in df.columns:
        df = df.drop('Date', axis=1)
        print("✓ Dropped 'Date' (will use hour, month, day_of_week instead)")

    print(f"  Remaining columns: {list(df.columns)}")
    return df


def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer temporal features from hour."""
    print(f"\n{'='*60}")
    print("STEP 3: ENGINEERING TEMPORAL FEATURES")
    print(f"{'='*60}")

    # Peak hour (6-10 PM = hours 18-22): high demand
    df['is_peak_hour'] = ((df['Hour'] >= 18) & (df['Hour'] <= 22)).astype(int)
    print(f"✓ Created 'is_peak_hour' (1 if 6-10 PM, 0 otherwise)")

    # Night hours (0-6 AM = hours 0-6): low demand
    df['is_night'] = (df['Hour'] < 6).astype(int)
    print(f"✓ Created 'is_night' (1 if midnight-6 AM, 0 otherwise)")

    # Working day (vs. non-functioning day)
    df['is_working_day'] = (df['Functioning Day'] == 'Yes').astype(int)
    print(f"✓ Created 'is_working_day' (based on Functioning Day)")

    # Drop Functioning Day (already encoded)
    df = df.drop('Functioning Day', axis=1)

    print(f"  Feature count: {df.shape[1]}")
    return df


def encode_categorical_features(df: pd.DataFrame) -> pd.DataFrame:
    """One-hot encode categorical variables."""
    print(f"\n{'='*60}")
    print("STEP 4: ENCODING CATEGORICAL FEATURES")
    print(f"{'='*60}")

    # Convert Holiday to binary
    df['is_holiday'] = (df['Holiday'] == 'Holiday').astype(int)
    df = df.drop('Holiday', axis=1)
    print(f"✓ Encoded 'Holiday' → 'is_holiday' (binary)")

    # One-hot encode Seasons
    seasons_encoded = pd.get_dummies(df['Seasons'], prefix='season', drop_first=True)
    df = pd.concat([df, seasons_encoded], axis=1)
    df = df.drop('Seasons', axis=1)
    print(f"✓ One-hot encoded 'Seasons' → {list(seasons_encoded.columns)}")

    print(f"  Feature count: {df.shape[1]}")
    print(f"  New columns: {list(df.columns)}")
    return df


def scale_numerical_features(df: pd.DataFrame, fit_scaler: bool = True) -> tuple:
    """Scale numerical features using StandardScaler."""
    print(f"\n{'='*60}")
    print("STEP 5: SCALING NUMERICAL FEATURES")
    print(f"{'='*60}")

    # Identify numerical columns (exclude target and binary features)
    numerical_cols = [
        'Hour', 'Temperature(°C)', 'Humidity(%)', 'Wind speed (m/s)',
        'Visibility (10m)', 'Solar Radiation (MJ/m2)', 'Rainfall(mm)', 'Snowfall (cm)'
    ]

    print(f"✓ Scaling {len(numerical_cols)} numerical features:")
    print(f"  {numerical_cols}")

    scaler = StandardScaler()
    df[numerical_cols] = scaler.fit_transform(df[numerical_cols])

    print(f"✓ Scaling complete (mean≈0, std≈1)")
    return df, scaler


def create_train_test_split(df: pd.DataFrame, test_size: float = 0.2) -> tuple:
    """
    Create temporal train/test split (no random shuffle).

    Important: For time series, we split chronologically to avoid data leakage.
    """
    print(f"\n{'='*60}")
    print("STEP 6: TEMPORAL TRAIN/TEST SPLIT")
    print(f"{'='*60}")

    split_idx = int(len(df) * (1 - test_size))

    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    print(f"✓ Chronological split (no random shuffle to preserve time series):")
    print(f"  Train: {train_df.shape[0]} rows ({100*(1-test_size):.0f}%)")
    print(f"  Test:  {test_df.shape[0]} rows ({100*test_size:.0f}%)")
    print(f"  Why: Prevents data leakage in time series modeling")

    return train_df, test_df


def separate_features_target(df: pd.DataFrame, target_col: str = 'Rented Bike Count') -> tuple:
    """Separate features (X) and target (y)."""
    X = df.drop(target_col, axis=1)
    y = df[target_col]
    return X, y


def save_processed_data(train_df: pd.DataFrame, test_df: pd.DataFrame,
                        scaler, output_dir: str = 'data/processed/') -> None:
    """Save processed data and scaler for later use."""
    print(f"\n{'='*60}")
    print("STEP 7: SAVING PROCESSED DATA")
    print(f"{'='*60}")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Save train and test data
    train_file = os.path.join(output_dir, 'train.csv')
    test_file = os.path.join(output_dir, 'test.csv')
    scaler_file = os.path.join(output_dir, 'scaler.pkl')

    train_df.to_csv(train_file, index=False)
    test_df.to_csv(test_file, index=False)

    with open(scaler_file, 'wb') as f:
        pickle.dump(scaler, f)

    print(f"✓ Saved train data: {train_file}")
    print(f"✓ Saved test data: {test_file}")
    print(f"✓ Saved scaler object: {scaler_file}")
    print(f"\n  Train shape: {train_df.shape}")
    print(f"  Test shape: {test_df.shape}")


def print_summary(df: pd.DataFrame) -> None:
    """Print final data summary."""
    print(f"\n{'='*60}")
    print("FINAL DATA SUMMARY")
    print(f"{'='*60}")
    print(f"\nDataset shape: {df.shape}")
    print(f"\nFeature types:")
    print(df.dtypes)
    print(f"\nFirst few rows:")
    print(df.head())
    print(f"\nBasic statistics:")
    print(df.describe())


def main(raw_data_path: str = 'data/raw/SeoulBikeData.csv',
         output_dir: str = 'data/processed/') -> None:
    """Run complete data preparation pipeline."""
    print("\n" + "="*60)
    print("SEOUL BIKE DEMAND - DATA PREPARATION & FEATURE ENGINEERING")
    print("="*60)

    # Load data
    df = load_raw_data(raw_data_path)

    # Feature engineering pipeline
    df = drop_multicollinear_features(df)
    df = create_temporal_features(df)
    df = encode_categorical_features(df)
    df, scaler = scale_numerical_features(df)

    # Split data
    train_df, test_df = create_train_test_split(df, test_size=0.2)

    # Save processed data
    save_processed_data(train_df, test_df, scaler, output_dir)

    # Print summary
    print_summary(df)

    print(f"\n{'='*60}")
    print("DATA PREPARATION COMPLETE ✓")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
