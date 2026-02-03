"""
Draft Projection Model

Predicts NFL draft outcomes for college players.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
import joblib
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.model_selection import cross_val_score
import xgboost as xgb

from ..utils.config import Config
from ..feature_engineering.draft_features import DraftFeatureEngineer


class DraftProjector:
    """Projects NFL draft outcomes for college players."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the draft projector.

        Args:
            config: Configuration object with model parameters
        """
        self.config = config or Config()
        self.feature_engineer = DraftFeatureEngineer(config)
        self.draft_probability_model = None
        self.draft_position_model = None
        self.feature_columns: List[str] = []

    def build_models(self) -> None:
        """Build the draft prediction models."""
        params = self.config.model_params.get("draft_projector", {})

        # Model for predicting if player will be drafted
        self.draft_probability_model = xgb.XGBClassifier(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 6),
            learning_rate=params.get("learning_rate", 0.1),
            random_state=42,
        )

        # Model for predicting draft position
        self.draft_position_model = xgb.XGBRegressor(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 6),
            learning_rate=params.get("learning_rate", 0.1),
            random_state=42,
        )

    def train(
        self,
        X: pd.DataFrame,
        y_drafted: pd.Series,
        y_pick: pd.Series,
    ) -> Dict[str, Any]:
        """
        Train both draft models.

        Args:
            X: Feature DataFrame
            y_drafted: Binary target (1 = drafted)
            y_pick: Draft pick number (for drafted players)

        Returns:
            Dictionary with training metrics
        """
        if self.draft_probability_model is None:
            self.build_models()

        self.feature_columns = X.columns.tolist()

        # Train probability model on all data
        self.draft_probability_model.fit(X, y_drafted)

        # Train position model only on drafted players
        drafted_mask = y_drafted == 1
        if drafted_mask.sum() > 0:
            self.draft_position_model.fit(X[drafted_mask], y_pick[drafted_mask])

        # Calculate metrics
        prob_cv = cross_val_score(
            self.draft_probability_model, X, y_drafted, cv=5, scoring="roc_auc"
        )

        return {
            "probability_auc": prob_cv.mean(),
            "probability_auc_std": prob_cv.std(),
        }

    def predict(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Generate draft projections.

        Args:
            X: Feature DataFrame

        Returns:
            DataFrame with draft projections
        """
        if self.draft_probability_model is None:
            raise ValueError("Models not trained.")

        draft_prob = self.draft_probability_model.predict_proba(X)[:, 1]
        draft_pick = self.draft_position_model.predict(X)

        # Calculate round from pick
        def pick_to_round(pick: float) -> int:
            if pick <= 32:
                return 1
            elif pick <= 64:
                return 2
            elif pick <= 100:
                return 3
            elif pick <= 135:
                return 4
            elif pick <= 176:
                return 5
            elif pick <= 220:
                return 6
            else:
                return 7

        results = pd.DataFrame({
            "draft_probability": draft_prob,
            "projected_pick": np.clip(draft_pick, 1, 260),
            "projected_round": [pick_to_round(p) for p in draft_pick],
        })

        # Add draft grade
        results["draft_grade"] = self._calculate_draft_grade(
            draft_prob, draft_pick
        )

        return results

    def _calculate_draft_grade(
        self,
        probabilities: np.ndarray,
        picks: np.ndarray,
    ) -> np.ndarray:
        """Calculate overall draft grade 0-100."""
        # Higher probability and lower pick = higher grade
        prob_component = probabilities * 50
        pick_component = 50 * (1 - np.clip(picks, 1, 260) / 260)

        return np.clip(prob_component + pick_component, 0, 100)

    def get_draft_board(
        self,
        players: pd.DataFrame,
        position: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Generate a draft board ranking players.

        Args:
            players: DataFrame with player data
            position: Optional position filter

        Returns:
            DataFrame with draft board
        """
        if position:
            players = players[players["position"] == position].copy()

        features = self.feature_engineer.create_features(players)

        for col in self.feature_columns:
            if col not in features.columns:
                features[col] = 0

        X = features[self.feature_columns]
        projections = self.predict(X)

        board = players.copy()
        board["draft_probability"] = projections["draft_probability"]
        board["projected_pick"] = projections["projected_pick"]
        board["projected_round"] = projections["projected_round"]
        board["draft_grade"] = projections["draft_grade"]

        return board.sort_values("draft_grade", ascending=False)

    def compare_to_historical(
        self,
        player_features: Dict[str, Any],
        position: str,
    ) -> pd.DataFrame:
        """
        Compare a player to historical draft picks at their position.

        Args:
            player_features: Dictionary of player features
            position: Player position

        Returns:
            DataFrame with comparable players
        """
        # This would compare to historical data
        # Placeholder implementation
        return pd.DataFrame({
            "comparable_player": [],
            "draft_year": [],
            "draft_pick": [],
            "similarity_score": [],
        })

    def project_career_value(
        self,
        draft_pick: int,
        position: str,
    ) -> Dict[str, Any]:
        """
        Project career value based on draft position.

        Args:
            draft_pick: Projected draft pick
            position: Player position

        Returns:
            Dictionary with career projections
        """
        # Rookie contract value (simplified)
        if draft_pick <= 10:
            rookie_value = 30_000_000
        elif draft_pick <= 32:
            rookie_value = 15_000_000
        elif draft_pick <= 64:
            rookie_value = 6_000_000
        else:
            rookie_value = 3_000_000

        # Career earnings potential
        position_multipliers = {
            "QB": 3.0, "EDGE": 2.5, "OT": 2.2, "WR": 2.0,
            "CB": 1.8, "DL": 1.7, "LB": 1.5, "RB": 1.2,
        }
        multiplier = position_multipliers.get(position, 1.5)

        return {
            "rookie_contract_value": rookie_value,
            "career_earnings_potential": rookie_value * multiplier * 2,
            "pro_bowl_probability": max(0.05, 0.5 - (draft_pick * 0.01)),
            "all_pro_probability": max(0.01, 0.3 - (draft_pick * 0.008)),
        }

    def save(self, path: Optional[str] = None) -> str:
        """Save models to disk."""
        if path is None:
            path = str(Path(self.config.data_paths["models"]) / "draft_projector.joblib")

        joblib.dump({
            "probability_model": self.draft_probability_model,
            "position_model": self.draft_position_model,
            "feature_columns": self.feature_columns,
        }, path)

        return path

    def load(self, path: Optional[str] = None) -> None:
        """Load saved models."""
        if path is None:
            path = str(Path(self.config.data_paths["models"]) / "draft_projector.joblib")

        data = joblib.load(path)
        self.draft_probability_model = data["probability_model"]
        self.draft_position_model = data["position_model"]
        self.feature_columns = data["feature_columns"]
