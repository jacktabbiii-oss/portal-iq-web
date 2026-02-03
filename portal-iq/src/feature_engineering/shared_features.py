"""
Shared Feature Engineering

Common feature engineering utilities used across models.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from sklearn.preprocessing import StandardScaler, LabelEncoder

from ..utils.config import Config


class SharedFeatureEngineer:
    """Shared feature engineering utilities."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the shared feature engineer.

        Args:
            config: Configuration object with settings
        """
        self.config = config or Config()
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}

    def normalize_features(
        self,
        df: pd.DataFrame,
        columns: List[str],
        fit: bool = True,
    ) -> pd.DataFrame:
        """
        Normalize numerical features using StandardScaler.

        Args:
            df: DataFrame with features
            columns: Columns to normalize
            fit: Whether to fit the scaler (False for inference)

        Returns:
            DataFrame with normalized features
        """
        df = df.copy()
        available_cols = [c for c in columns if c in df.columns]

        for col in available_cols:
            if fit:
                scaler = StandardScaler()
                df[f"{col}_scaled"] = scaler.fit_transform(
                    df[[col]].fillna(0)
                )
                self.scalers[col] = scaler
            elif col in self.scalers:
                df[f"{col}_scaled"] = self.scalers[col].transform(
                    df[[col]].fillna(0)
                )

        return df

    def encode_categorical(
        self,
        df: pd.DataFrame,
        columns: List[str],
        fit: bool = True,
    ) -> pd.DataFrame:
        """
        Encode categorical features.

        Args:
            df: DataFrame with features
            columns: Columns to encode
            fit: Whether to fit the encoder (False for inference)

        Returns:
            DataFrame with encoded features
        """
        df = df.copy()
        available_cols = [c for c in columns if c in df.columns]

        for col in available_cols:
            if fit:
                encoder = LabelEncoder()
                df[f"{col}_encoded"] = encoder.fit_transform(
                    df[col].fillna("unknown").astype(str)
                )
                self.encoders[col] = encoder
            elif col in self.encoders:
                # Handle unseen categories
                df[f"{col}_encoded"] = df[col].apply(
                    lambda x: (
                        self.encoders[col].transform([str(x)])[0]
                        if str(x) in self.encoders[col].classes_
                        else -1
                    )
                )

        return df

    def create_interaction_features(
        self,
        df: pd.DataFrame,
        feature_pairs: List[Tuple[str, str]],
    ) -> pd.DataFrame:
        """
        Create interaction features between pairs of columns.

        Args:
            df: DataFrame with features
            feature_pairs: List of column pairs to interact

        Returns:
            DataFrame with interaction features
        """
        df = df.copy()

        for col1, col2 in feature_pairs:
            if col1 in df.columns and col2 in df.columns:
                # Multiplicative interaction
                df[f"{col1}_x_{col2}"] = df[col1] * df[col2]

                # Ratio (with small epsilon to avoid division by zero)
                df[f"{col1}_div_{col2}"] = df[col1] / (df[col2] + 1e-6)

        return df

    def create_polynomial_features(
        self,
        df: pd.DataFrame,
        columns: List[str],
        degree: int = 2,
    ) -> pd.DataFrame:
        """
        Create polynomial features.

        Args:
            df: DataFrame with features
            columns: Columns to create polynomial features for
            degree: Maximum polynomial degree

        Returns:
            DataFrame with polynomial features
        """
        df = df.copy()
        available_cols = [c for c in columns if c in df.columns]

        for col in available_cols:
            for d in range(2, degree + 1):
                df[f"{col}_pow{d}"] = df[col] ** d

        return df

    def create_lag_features(
        self,
        df: pd.DataFrame,
        columns: List[str],
        lags: List[int],
        group_col: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Create lag features for time series data.

        Args:
            df: DataFrame with features
            columns: Columns to create lags for
            lags: List of lag periods
            group_col: Optional column to group by

        Returns:
            DataFrame with lag features
        """
        df = df.copy()
        available_cols = [c for c in columns if c in df.columns]

        for col in available_cols:
            for lag in lags:
                if group_col and group_col in df.columns:
                    df[f"{col}_lag{lag}"] = df.groupby(group_col)[col].shift(lag)
                else:
                    df[f"{col}_lag{lag}"] = df[col].shift(lag)

        return df

    def create_rolling_features(
        self,
        df: pd.DataFrame,
        columns: List[str],
        windows: List[int],
        functions: List[str] = ["mean", "std"],
        group_col: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Create rolling window features.

        Args:
            df: DataFrame with features
            columns: Columns to create rolling features for
            windows: List of window sizes
            functions: Aggregation functions to apply
            group_col: Optional column to group by

        Returns:
            DataFrame with rolling features
        """
        df = df.copy()
        available_cols = [c for c in columns if c in df.columns]

        for col in available_cols:
            for window in windows:
                for func in functions:
                    col_name = f"{col}_roll{window}_{func}"
                    if group_col and group_col in df.columns:
                        df[col_name] = (
                            df.groupby(group_col)[col]
                            .transform(lambda x: x.rolling(window).agg(func))
                        )
                    else:
                        df[col_name] = df[col].rolling(window).agg(func)

        return df

    def handle_missing_values(
        self,
        df: pd.DataFrame,
        numeric_strategy: str = "median",
        categorical_strategy: str = "mode",
    ) -> pd.DataFrame:
        """
        Handle missing values in the DataFrame.

        Args:
            df: DataFrame with potential missing values
            numeric_strategy: Strategy for numeric columns (median, mean, zero)
            categorical_strategy: Strategy for categorical columns (mode, unknown)

        Returns:
            DataFrame with handled missing values
        """
        df = df.copy()

        for col in df.columns:
            if df[col].isna().any():
                if df[col].dtype in ["int64", "float64"]:
                    if numeric_strategy == "median":
                        df[col] = df[col].fillna(df[col].median())
                    elif numeric_strategy == "mean":
                        df[col] = df[col].fillna(df[col].mean())
                    else:
                        df[col] = df[col].fillna(0)
                else:
                    if categorical_strategy == "mode":
                        mode_val = df[col].mode()
                        df[col] = df[col].fillna(
                            mode_val[0] if len(mode_val) > 0 else "unknown"
                        )
                    else:
                        df[col] = df[col].fillna("unknown")

        return df

    def remove_outliers(
        self,
        df: pd.DataFrame,
        columns: List[str],
        method: str = "iqr",
        threshold: float = 1.5,
    ) -> pd.DataFrame:
        """
        Remove outliers from numerical columns.

        Args:
            df: DataFrame with potential outliers
            columns: Columns to check for outliers
            method: Outlier detection method (iqr, zscore)
            threshold: Threshold for outlier detection

        Returns:
            DataFrame with outliers removed
        """
        df = df.copy()
        available_cols = [c for c in columns if c in df.columns]

        for col in available_cols:
            if df[col].dtype not in ["int64", "float64"]:
                continue

            if method == "iqr":
                q1 = df[col].quantile(0.25)
                q3 = df[col].quantile(0.75)
                iqr = q3 - q1
                lower = q1 - threshold * iqr
                upper = q3 + threshold * iqr
                df = df[(df[col] >= lower) & (df[col] <= upper)]
            elif method == "zscore":
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                df = df[z_scores < threshold]

        return df
