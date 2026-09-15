"""
Exploratory Data Analysis for Seoul Bike Demand Dataset.

This module performs comprehensive EDA to understand:
- Target variable distribution (bike rental demand)
- Temporal patterns (hourly, daily, seasonal trends)
- Weather feature impacts
- Data quality issues (missing values, outliers)
- Feature correlations and relationships
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def load_data(filepath: str) -> pd.DataFrame:
    """Load the raw dataset."""
    df = pd.read_csv(filepath, encoding='latin-1')
    print(f"✓ Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns\n")
    return df


def examine_structure(df: pd.DataFrame) -> None:
    """Examine dataset structure and basic info."""
    print("=" * 60)
    print("DATASET STRUCTURE")
    print("=" * 60)
    print(f"\nShape: {df.shape}")
    print(f"\nData types:\n{df.dtypes}")
    print(f"\nFirst few rows:\n{df.head()}")
    print(f"\nColumn names:\n{df.columns.tolist()}\n")


def check_missing_values(df: pd.DataFrame) -> None:
    """Check for missing values and data quality issues."""
    print("=" * 60)
    print("MISSING VALUES & DATA QUALITY")
    print("=" * 60)
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("✓ No missing values detected\n")
    else:
        print(f"\nMissing values:\n{missing[missing > 0]}\n")

    # Check for duplicates
    duplicates = df.duplicated().sum()
    print(f"Duplicate rows: {duplicates}")
    print()


def analyze_target_variable(df: pd.DataFrame) -> None:
    """Analyze the target variable (Rented Bike Count)."""
    print("=" * 60)
    print("TARGET VARIABLE: Rented Bike Count")
    print("=" * 60)
    target = df['Rented Bike Count']
    print(f"\nStatistics:")
    print(f"  Count:     {target.count()}")
    print(f"  Mean:      {target.mean():.2f}")
    print(f"  Median:    {target.median():.2f}")
    print(f"  Std Dev:   {target.std():.2f}")
    print(f"  Min:       {target.min()}")
    print(f"  Max:       {target.max()}")
    print(f"  Q1 (25%):  {target.quantile(0.25):.2f}")
    print(f"  Q3 (75%):  {target.quantile(0.75):.2f}")
    print()

    # Distribution shape
    skewness = target.skew()
    kurtosis_val = target.kurtosis()
    print(f"Distribution shape:")
    print(f"  Skewness: {skewness:.2f} {'(right-skewed)' if skewness > 0 else '(left-skewed)'}")
    print(f"  Kurtosis: {kurtosis_val:.2f}\n")


def analyze_numerical_features(df: pd.DataFrame) -> None:
    """Analyze numerical features."""
    print("=" * 60)
    print("NUMERICAL FEATURES")
    print("=" * 60)
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Remove target from this analysis
    numerical_cols = [col for col in numerical_cols if col != 'Rented Bike Count']

    print(f"\nNumerical features: {len(numerical_cols)}")
    print(f"{numerical_cols}\n")
    print(df[numerical_cols].describe().to_string())
    print()


def analyze_categorical_features(df: pd.DataFrame) -> None:
    """Analyze categorical features."""
    print("=" * 60)
    print("CATEGORICAL FEATURES")
    print("=" * 60)
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

    print(f"\nCategorical features: {len(categorical_cols)}")
    for col in categorical_cols:
        print(f"\n{col}:")
        print(df[col].value_counts())
    print()


def analyze_temporal_patterns(df: pd.DataFrame) -> None:
    """Analyze temporal patterns in bike demand."""
    print("=" * 60)
    print("TEMPORAL PATTERNS")
    print("=" * 60)

    # Hour of day analysis
    hourly_demand = df.groupby('Hour')['Rented Bike Count'].agg(['mean', 'min', 'max', 'std'])
    print("\nDemand by Hour of Day:")
    print(f"  Peak hour:  {hourly_demand['mean'].idxmax()} ({hourly_demand['mean'].max():.2f} bikes avg)")
    print(f"  Low hour:   {hourly_demand['mean'].idxmin()} ({hourly_demand['mean'].min():.2f} bikes avg)")
    print()

    # Season analysis
    seasonal_demand = df.groupby('Seasons')['Rented Bike Count'].agg(['mean', 'std', 'count'])
    print("\nDemand by Season:")
    print(seasonal_demand.to_string())
    print()

    # Holiday analysis
    holiday_demand = df.groupby('Holiday')['Rented Bike Count'].agg(['mean', 'std', 'count'])
    print("\nDemand by Holiday:")
    print(holiday_demand.to_string())
    print()


def analyze_correlations(df: pd.DataFrame) -> None:
    """Analyze correlations between features and target."""
    print("=" * 60)
    print("FEATURE CORRELATIONS")
    print("=" * 60)

    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    corr_with_target = df[numerical_cols].corr()['Rented Bike Count'].sort_values(ascending=False)

    print("\nCorrelation with target (Rented Bike Count):")
    print(corr_with_target.to_string())
    print()

    # Check multicollinearity
    print("Feature correlation matrix (top correlations):")
    corr_matrix = df[numerical_cols].corr()
    # Get upper triangle to avoid duplicates
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)
    high_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            if abs(corr_matrix.iloc[i, j]) > 0.7:
                high_corr_pairs.append((i, j))

    if len(high_corr_pairs) > 0:
        print("High correlations (|r| > 0.7) detected:")
        for i, j in high_corr_pairs:
            print(f"  {corr_matrix.index[i]} <-> {corr_matrix.columns[j]}: {corr_matrix.iloc[i, j]:.3f}")
    else:
        print("  No high correlations (|r| > 0.7) detected")
    print()


def detect_outliers(df: pd.DataFrame) -> None:
    """Detect outliers using IQR method."""
    print("=" * 60)
    print("OUTLIER DETECTION")
    print("=" * 60)

    target = df['Rented Bike Count']
    Q1 = target.quantile(0.25)
    Q3 = target.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = (target < lower_bound) | (target > upper_bound)
    print(f"\nOutliers (IQR method):")
    print(f"  Lower bound: {lower_bound:.2f}")
    print(f"  Upper bound: {upper_bound:.2f}")
    print(f"  Outlier count: {outliers.sum()} ({100 * outliers.sum() / len(df):.2f}%)")
    print()


def generate_summary(df: pd.DataFrame) -> None:
    """Generate final summary insights."""
    print("=" * 60)
    print("KEY INSIGHTS & NEXT STEPS")
    print("=" * 60)
    print("""
1. TARGET VARIABLE:
   - Analyze skewness; may need log transformation
   - Understand peak and off-peak demand patterns

2. TEMPORAL EFFECTS:
   - Strong hourly and seasonal patterns expected
   - Hour and Seasons should be important features
   - Consider time-based features (e.g., is_weekend, is_working_day)

3. WEATHER FEATURES:
   - Correlation with demand will guide feature selection
   - Multicollinearity may require feature engineering

4. DATA PREPARATION STEPS:
   - Handle categorical variables (encoding for Seasons, Holiday)
   - Scale numerical features
   - Create derived temporal features
   - Consider train/test split based on time (to avoid data leakage)

5. MODELING CONSIDERATIONS:
   - Regression task (predicting continuous bike count)
   - Time series nature suggests autoregressive features
   - May benefit from ensemble methods (Random Forest, Gradient Boosting)
    """)
    print()


def main(data_path: str = "data/raw/SeoulBikeData.csv") -> None:
    """Run complete exploratory data analysis."""
    print("\n" + "=" * 60)
    print("SEOUL BIKE DEMAND - EXPLORATORY DATA ANALYSIS")
    print("=" * 60 + "\n")

    df = load_data(data_path)

    examine_structure(df)
    check_missing_values(df)
    analyze_target_variable(df)
    analyze_numerical_features(df)
    analyze_categorical_features(df)
    analyze_temporal_patterns(df)
    analyze_correlations(df)
    detect_outliers(df)
    generate_summary(df)

    print("=" * 60)
    print("EDA COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
