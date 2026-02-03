"""
NIL Valuation Model

Machine learning model for predicting NIL market value.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
import xgboost as xgb
import lightgbm as lgb
import shap

from ..utils.config import Config
from ..feature_engineering.nil_features import NILFeatureEngineer


class NILValuator:
    """Predicts NIL market value for college football players."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the NIL valuator.

        Args:
            config: Configuration object with model parameters
        """
        self.config = config or Config()
        self.feature_engineer = NILFeatureEngineer(config)
        self.model = None
        self.model_type = "xgboost"
        self.feature_columns: List[str] = []

    def build_model(self, model_type: str = "xgboost") -> None:
        """
        Build the valuation model.

        Args:
            model_type: Type of model (xgboost, lightgbm, gbm)
        """
        self.model_type = model_type
        params = self.config.model_params.get("nil_valuator", {})

        if model_type == "xgboost":
            self.model = xgb.XGBRegressor(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 6),
                learning_rate=params.get("learning_rate", 0.1),
                random_state=42,
            )
        elif model_type == "lightgbm":
            self.model = lgb.LGBMRegressor(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 6),
                learning_rate=params.get("learning_rate", 0.1),
                random_state=42,
            )
        else:
            self.model = GradientBoostingRegressor(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 6),
                learning_rate=params.get("learning_rate", 0.1),
                random_state=42,
            )

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Train the NIL valuation model.

        Args:
            X: Feature DataFrame
            y: Target values (NIL valuations)
            validate: Whether to run cross-validation

        Returns:
            Dictionary with training metrics
        """
        if self.model is None:
            self.build_model()

        # Store feature columns
        self.feature_columns = X.columns.tolist()

        # Fit model
        self.model.fit(X, y)

        metrics = {"trained": True}

        if validate:
            cv_scores = cross_val_score(
                self.model, X, y, cv=5, scoring="neg_mean_absolute_error"
            )
            metrics["cv_mae"] = -cv_scores.mean()
            metrics["cv_mae_std"] = cv_scores.std()

        return metrics

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict NIL valuations.

        Args:
            X: Feature DataFrame

        Returns:
            Array of predicted valuations
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X)

    def predict_with_confidence(
        self,
        X: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Predict NIL valuations with confidence intervals.

        Args:
            X: Feature DataFrame

        Returns:
            Tuple of (predictions, lower_bound, upper_bound)
        """
        predictions = self.predict(X)

        # Estimate confidence based on model uncertainty
        # This is a simplified approach; production would use
        # quantile regression or bootstrapping
        std_estimate = predictions * 0.2  # 20% standard deviation estimate

        lower = predictions - 1.96 * std_estimate
        upper = predictions + 1.96 * std_estimate

        return predictions, np.maximum(lower, 0), upper

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from the model.

        Returns:
            DataFrame with feature importance scores
        """
        if self.model is None:
            raise ValueError("Model not trained.")

        if hasattr(self.model, "feature_importances_"):
            importance = self.model.feature_importances_
        else:
            importance = np.zeros(len(self.feature_columns))

        return pd.DataFrame({
            "feature": self.feature_columns,
            "importance": importance,
        }).sort_values("importance", ascending=False)

    def explain_prediction(
        self,
        X: pd.DataFrame,
        player_idx: int = 0,
    ) -> Dict[str, Any]:
        """
        Explain a prediction using SHAP values.

        Args:
            X: Feature DataFrame
            player_idx: Index of player to explain

        Returns:
            Dictionary with SHAP explanation
        """
        if self.model is None:
            raise ValueError("Model not trained.")

        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(X)

        player_shap = shap_values[player_idx]

        explanation = {
            "base_value": explainer.expected_value,
            "prediction": self.predict(X.iloc[[player_idx]])[0],
            "contributions": dict(zip(self.feature_columns, player_shap)),
        }

        return explanation

    def save(self, path: Optional[str] = None) -> str:
        """
        Save the model to disk.

        Args:
            path: Optional save path

        Returns:
            Path where model was saved
        """
        if path is None:
            path = str(Path(self.config.data_paths["models"]) / "nil_valuator.joblib")

        joblib.dump({
            "model": self.model,
            "model_type": self.model_type,
            "feature_columns": self.feature_columns,
        }, path)

        return path

    def load(self, path: Optional[str] = None) -> None:
        """
        Load a saved model.

        Args:
            path: Optional load path
        """
        if path is None:
            path = str(Path(self.config.data_paths["models"]) / "nil_valuator.joblib")

        data = joblib.load(path)
        self.model = data["model"]
        self.model_type = data["model_type"]
        self.feature_columns = data["feature_columns"]

    def value_player(
        self,
        player_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Value a single player.

        Args:
            player_data: Dictionary with player information

        Returns:
            Dictionary with valuation and breakdown
        """
        df = pd.DataFrame([player_data])
        features = self.feature_engineer.create_features(df)

        # Ensure we have all required columns
        for col in self.feature_columns:
            if col not in features.columns:
                features[col] = 0

        X = features[self.feature_columns]
        prediction, lower, upper = self.predict_with_confidence(X)

        return {
            "player_name": player_data.get("player_name", "Unknown"),
            "valuation": float(prediction[0]),
            "valuation_low": float(lower[0]),
            "valuation_high": float(upper[0]),
            "nil_tier": self.feature_engineer.calculate_nil_tier(prediction[0]),
        }
