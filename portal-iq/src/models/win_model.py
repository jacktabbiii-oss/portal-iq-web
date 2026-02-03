"""
Win Impact Model

Models the impact of roster changes on team win totals.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingRegressor
import xgboost as xgb

from ..utils.config import Config
from ..feature_engineering.roster_features import RosterFeatureEngineer


class WinImpactModel:
    """Models win impact of roster moves and player additions."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the win impact model.

        Args:
            config: Configuration object with model parameters
        """
        self.config = config or Config()
        self.feature_engineer = RosterFeatureEngineer(config)
        self.win_model = None
        self.player_value_model = None
        self.feature_columns: List[str] = []

    def build_models(self) -> None:
        """Build the win prediction models."""
        params = self.config.model_params.get("win_model", {})

        # Team win prediction model
        self.win_model = xgb.XGBRegressor(
            n_estimators=params.get("n_estimators", 100),
            max_depth=params.get("max_depth", 6),
            learning_rate=params.get("learning_rate", 0.1),
            random_state=42,
        )

        # Player marginal value model
        self.player_value_model = Ridge(alpha=1.0)

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> Dict[str, Any]:
        """
        Train the win prediction model.

        Args:
            X: Feature DataFrame (team-level features)
            y: Win totals

        Returns:
            Dictionary with training metrics
        """
        if self.win_model is None:
            self.build_models()

        self.feature_columns = X.columns.tolist()
        self.win_model.fit(X, y)

        # Calculate R-squared
        predictions = self.win_model.predict(X)
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        return {
            "r_squared": r_squared,
            "mae": np.mean(np.abs(y - predictions)),
        }

    def predict_wins(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict win totals.

        Args:
            X: Feature DataFrame

        Returns:
            Array of predicted win totals
        """
        if self.win_model is None:
            raise ValueError("Model not trained.")

        return np.clip(self.win_model.predict(X), 0, 15)

    def calculate_player_war(
        self,
        player: Dict[str, Any],
        team_context: Dict[str, Any],
    ) -> float:
        """
        Calculate Wins Above Replacement for a player.

        Args:
            player: Player information
            team_context: Team context (roster, scheme, etc.)

        Returns:
            WAR value
        """
        position = player.get("position", "")
        rating = player.get("player_rating", 50)

        # Position value weights
        position_weights = {
            "QB": 1.5, "EDGE": 0.8, "OT": 0.7, "CB": 0.6,
            "WR": 0.5, "LB": 0.5, "DL": 0.5, "RB": 0.4,
            "S": 0.4, "TE": 0.4, "OG": 0.4, "C": 0.3,
        }

        base_weight = position_weights.get(position, 0.4)

        # Rating impact (above replacement level of 40)
        rating_above_replacement = max(0, rating - 40) / 60

        # Calculate WAR
        war = base_weight * rating_above_replacement * 2

        return war

    def simulate_roster_change(
        self,
        current_roster: pd.DataFrame,
        additions: List[Dict[str, Any]],
        departures: List[str],
    ) -> Dict[str, Any]:
        """
        Simulate the impact of roster changes.

        Args:
            current_roster: Current roster DataFrame
            additions: List of players being added
            departures: List of player IDs departing

        Returns:
            Dictionary with simulation results
        """
        # Calculate current projected wins
        current_features = self.feature_engineer.create_features(current_roster)
        for col in self.feature_columns:
            if col not in current_features.columns:
                current_features[col] = 0

        current_wins = self.predict_wins(
            current_features[self.feature_columns].mean().to_frame().T
        )[0]

        # Remove departures
        new_roster = current_roster[
            ~current_roster["player_id"].isin(departures)
        ].copy()

        # Add new players
        additions_df = pd.DataFrame(additions)
        new_roster = pd.concat([new_roster, additions_df], ignore_index=True)

        # Calculate new projected wins
        new_features = self.feature_engineer.create_features(new_roster)
        for col in self.feature_columns:
            if col not in new_features.columns:
                new_features[col] = 0

        new_wins = self.predict_wins(
            new_features[self.feature_columns].mean().to_frame().T
        )[0]

        # Calculate individual impacts
        addition_impacts = []
        for player in additions:
            war = self.calculate_player_war(player, {})
            addition_impacts.append({
                "player_name": player.get("player_name", "Unknown"),
                "war": war,
            })

        return {
            "current_projected_wins": current_wins,
            "new_projected_wins": new_wins,
            "win_delta": new_wins - current_wins,
            "additions_impact": addition_impacts,
            "departures_count": len(departures),
        }

    def rank_targets_by_impact(
        self,
        targets: pd.DataFrame,
        team_roster: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Rank potential targets by win impact.

        Args:
            targets: DataFrame of potential transfer targets
            team_roster: Current team roster

        Returns:
            DataFrame with targets ranked by impact
        """
        impacts = []

        for _, target in targets.iterrows():
            simulation = self.simulate_roster_change(
                team_roster,
                additions=[target.to_dict()],
                departures=[],
            )
            impacts.append({
                "player_id": target.get("player_id"),
                "player_name": target.get("player_name"),
                "position": target.get("position"),
                "win_impact": simulation["win_delta"],
            })

        impact_df = pd.DataFrame(impacts)
        return impact_df.sort_values("win_impact", ascending=False)

    def project_season(
        self,
        roster: pd.DataFrame,
        schedule_strength: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Project full season results.

        Args:
            roster: Team roster DataFrame
            schedule_strength: Schedule strength (0-1)

        Returns:
            Dictionary with season projection
        """
        features = self.feature_engineer.create_features(roster)

        for col in self.feature_columns:
            if col not in features.columns:
                features[col] = 0

        base_wins = self.predict_wins(
            features[self.feature_columns].mean().to_frame().T
        )[0]

        # Adjust for schedule
        schedule_adjustment = (0.5 - schedule_strength) * 2
        adjusted_wins = base_wins + schedule_adjustment

        return {
            "projected_wins": round(adjusted_wins, 1),
            "win_range_low": max(0, round(adjusted_wins - 2, 0)),
            "win_range_high": min(15, round(adjusted_wins + 2, 0)),
            "playoff_probability": self._calculate_playoff_prob(adjusted_wins),
            "ny6_probability": self._calculate_ny6_prob(adjusted_wins),
        }

    def _calculate_playoff_prob(self, wins: float) -> float:
        """Calculate playoff probability based on wins."""
        if wins >= 12:
            return 0.9
        elif wins >= 11:
            return 0.6
        elif wins >= 10:
            return 0.3
        elif wins >= 9:
            return 0.1
        else:
            return 0.02

    def _calculate_ny6_prob(self, wins: float) -> float:
        """Calculate NY6 bowl probability based on wins."""
        if wins >= 11:
            return 0.8
        elif wins >= 10:
            return 0.5
        elif wins >= 9:
            return 0.25
        elif wins >= 8:
            return 0.1
        else:
            return 0.02

    def save(self, path: Optional[str] = None) -> str:
        """Save model to disk."""
        if path is None:
            path = str(Path(self.config.data_paths["models"]) / "win_model.joblib")

        joblib.dump({
            "win_model": self.win_model,
            "player_value_model": self.player_value_model,
            "feature_columns": self.feature_columns,
        }, path)

        return path

    def load(self, path: Optional[str] = None) -> None:
        """Load saved model."""
        if path is None:
            path = str(Path(self.config.data_paths["models"]) / "win_model.joblib")

        data = joblib.load(path)
        self.win_model = data["win_model"]
        self.player_value_model = data["player_value_model"]
        self.feature_columns = data["feature_columns"]
