"""
Portal Prediction Model

Predicts transfer portal entries and destinations.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
import xgboost as xgb
import lightgbm as lgb

from ..utils.config import Config
from ..feature_engineering.portal_features import PortalFeatureEngineer


class PortalPredictor:
    """Predicts portal entries and transfer destinations."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the portal predictor.

        Args:
            config: Configuration object with model parameters
        """
        self.config = config or Config()
        self.feature_engineer = PortalFeatureEngineer(config)
        self.entry_model = None
        self.destination_model = None
        self.feature_columns: List[str] = []

    def build_models(self, model_type: str = "xgboost") -> None:
        """
        Build the prediction models.

        Args:
            model_type: Type of model (xgboost, lightgbm, rf)
        """
        params = self.config.model_params.get("portal_predictor", {})

        if model_type == "xgboost":
            self.entry_model = xgb.XGBClassifier(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 6),
                learning_rate=params.get("learning_rate", 0.1),
                random_state=42,
            )
            self.destination_model = xgb.XGBClassifier(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 6),
                learning_rate=params.get("learning_rate", 0.1),
                random_state=42,
            )
        elif model_type == "lightgbm":
            self.entry_model = lgb.LGBMClassifier(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 6),
                learning_rate=params.get("learning_rate", 0.1),
                random_state=42,
            )
            self.destination_model = lgb.LGBMClassifier(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 6),
                learning_rate=params.get("learning_rate", 0.1),
                random_state=42,
            )
        else:
            self.entry_model = RandomForestClassifier(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 10),
                random_state=42,
            )
            self.destination_model = RandomForestClassifier(
                n_estimators=params.get("n_estimators", 100),
                max_depth=params.get("max_depth", 10),
                random_state=42,
            )

    def train_entry_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> Dict[str, Any]:
        """
        Train the portal entry prediction model.

        Args:
            X: Feature DataFrame
            y: Binary target (1 = entered portal)

        Returns:
            Dictionary with training metrics
        """
        if self.entry_model is None:
            self.build_models()

        self.feature_columns = X.columns.tolist()
        self.entry_model.fit(X, y)

        cv_scores = cross_val_score(
            self.entry_model, X, y, cv=5, scoring="roc_auc"
        )

        return {
            "cv_auc": cv_scores.mean(),
            "cv_auc_std": cv_scores.std(),
        }

    def train_destination_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> Dict[str, Any]:
        """
        Train the destination prediction model.

        Args:
            X: Feature DataFrame
            y: Target school labels

        Returns:
            Dictionary with training metrics
        """
        if self.destination_model is None:
            self.build_models()

        self.destination_model.fit(X, y)

        cv_scores = cross_val_score(
            self.destination_model, X, y, cv=5, scoring="accuracy"
        )

        return {
            "cv_accuracy": cv_scores.mean(),
            "cv_accuracy_std": cv_scores.std(),
        }

    def predict_portal_entry(
        self,
        X: pd.DataFrame,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict probability of entering the portal.

        Args:
            X: Feature DataFrame

        Returns:
            Tuple of (predictions, probabilities)
        """
        if self.entry_model is None:
            raise ValueError("Entry model not trained.")

        predictions = self.entry_model.predict(X)
        probabilities = self.entry_model.predict_proba(X)[:, 1]

        return predictions, probabilities

    def predict_destination(
        self,
        X: pd.DataFrame,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Predict likely transfer destinations.

        Args:
            X: Feature DataFrame (one row per player-school pair)
            top_n: Number of top destinations to return

        Returns:
            List of destination predictions with probabilities
        """
        if self.destination_model is None:
            raise ValueError("Destination model not trained.")

        probabilities = self.destination_model.predict_proba(X)
        classes = self.destination_model.classes_

        results = []
        for i in range(len(X)):
            player_probs = probabilities[i]
            top_indices = np.argsort(player_probs)[::-1][:top_n]

            destinations = [
                {
                    "school": classes[idx],
                    "probability": float(player_probs[idx]),
                    "rank": j + 1,
                }
                for j, idx in enumerate(top_indices)
            ]
            results.append(destinations)

        return results

    def get_at_risk_players(
        self,
        roster: pd.DataFrame,
        threshold: float = 0.5,
    ) -> pd.DataFrame:
        """
        Identify players at risk of entering the portal.

        Args:
            roster: DataFrame with roster information
            threshold: Probability threshold for "at risk"

        Returns:
            DataFrame of at-risk players
        """
        features = self.feature_engineer.create_features(roster)

        for col in self.feature_columns:
            if col not in features.columns:
                features[col] = 0

        X = features[self.feature_columns]
        _, probabilities = self.predict_portal_entry(X)

        roster["portal_probability"] = probabilities
        at_risk = roster[roster["portal_probability"] >= threshold].copy()

        return at_risk.sort_values("portal_probability", ascending=False)

    def analyze_player_fit(
        self,
        player: Dict[str, Any],
        schools: List[str],
    ) -> pd.DataFrame:
        """
        Analyze fit between a player and potential schools.

        Args:
            player: Player information dictionary
            schools: List of schools to evaluate

        Returns:
            DataFrame with fit scores for each school
        """
        destination_features = self.feature_engineer.create_destination_features(
            player, schools
        )

        # Get probability for each school
        predictions = self.predict_destination(destination_features)

        results = []
        for i, school in enumerate(schools):
            results.append({
                "school": school,
                "fit_score": predictions[0][i]["probability"] if i < len(predictions[0]) else 0,
                "position_need": destination_features.iloc[i].get("position_need", 0.5),
                "nil_potential": destination_features.iloc[i].get("nil_potential", 0.5),
            })

        return pd.DataFrame(results).sort_values("fit_score", ascending=False)

    def save(self, path: Optional[str] = None) -> str:
        """Save models to disk."""
        if path is None:
            path = str(Path(self.config.data_paths["models"]) / "portal_predictor.joblib")

        joblib.dump({
            "entry_model": self.entry_model,
            "destination_model": self.destination_model,
            "feature_columns": self.feature_columns,
        }, path)

        return path

    def load(self, path: Optional[str] = None) -> None:
        """Load saved models."""
        if path is None:
            path = str(Path(self.config.data_paths["models"]) / "portal_predictor.joblib")

        data = joblib.load(path)
        self.entry_model = data["entry_model"]
        self.destination_model = data["destination_model"]
        self.feature_columns = data["feature_columns"]
