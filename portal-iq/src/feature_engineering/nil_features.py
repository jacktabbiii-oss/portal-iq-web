"""
NIL Feature Engineering

Creates features for NIL valuation models.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List

from ..utils.config import Config


class NILFeatureEngineer:
    """Engineers features for NIL valuation predictions."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the NIL feature engineer.

        Args:
            config: Configuration object with settings
        """
        self.config = config or Config()
        self.nil_tiers = self.config.nil_tiers

    def create_features(self, player_data: pd.DataFrame) -> pd.DataFrame:
        """
        Create all NIL-related features.

        Args:
            player_data: DataFrame with player information

        Returns:
            DataFrame with engineered features
        """
        df = player_data.copy()

        # Position features
        df = self._add_position_features(df)

        # School/market features
        df = self._add_school_features(df)

        # Performance features
        df = self._add_performance_features(df)

        # Social media features
        df = self._add_social_features(df)

        # Recruiting features
        df = self._add_recruiting_features(df)

        return df

    def _add_position_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add position-based features."""
        # Position value tier
        position_tiers = {
            "QB": 5, "RB": 4, "WR": 4, "TE": 3,
            "OL": 2, "DL": 3, "LB": 3, "DB": 3,
            "K": 1, "P": 1,
        }
        df["position_value_tier"] = df["position"].map(position_tiers).fillna(2)

        # Position scarcity
        position_scarcity = {
            "QB": 1.0, "LT": 0.9, "EDGE": 0.85, "CB": 0.8,
            "WR": 0.6, "RB": 0.5, "TE": 0.7,
        }
        df["position_scarcity"] = df["position"].map(position_scarcity).fillna(0.5)

        # One-hot encode positions
        position_dummies = pd.get_dummies(df["position"], prefix="pos")
        df = pd.concat([df, position_dummies], axis=1)

        return df

    def _add_school_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add school and market-based features."""
        school_tiers = self.config.school_tiers

        def get_school_tier(school: str) -> str:
            for tier, schools in school_tiers.items():
                if school in schools:
                    return tier
            return "g5"

        df["school_tier"] = df["school"].apply(get_school_tier)

        # Tier numeric encoding
        tier_values = {
            "blue_blood": 6, "elite": 5, "power_brand": 4,
            "p4_mid": 3, "g5_strong": 2, "g5": 1,
        }
        df["school_tier_value"] = df["school_tier"].map(tier_values)

        # Market size estimate (placeholder)
        df["market_size"] = df["school_tier_value"] * 1.5

        return df

    def _add_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add performance-based features."""
        # Normalize stats by position
        if "yards" in df.columns:
            df["yards_percentile"] = df.groupby("position")["yards"].rank(pct=True)

        if "touchdowns" in df.columns:
            df["td_percentile"] = df.groupby("position")["touchdowns"].rank(pct=True)

        # Playing time features
        if "snaps" in df.columns:
            df["snap_share"] = df["snaps"] / df["snaps"].max()

        # Production per game
        if "games" in df.columns and "yards" in df.columns:
            df["yards_per_game"] = df["yards"] / df["games"].replace(0, 1)

        return df

    def _add_social_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add social media-based features."""
        if "social_followers" in df.columns:
            # Log transform for better distribution
            df["log_followers"] = np.log1p(df["social_followers"])

            # Follower tier
            df["follower_tier"] = pd.cut(
                df["social_followers"],
                bins=[0, 10000, 50000, 200000, 1000000, float("inf")],
                labels=["micro", "small", "medium", "large", "mega"],
            )

        if "engagement_rate" in df.columns:
            df["high_engagement"] = (df["engagement_rate"] > 3.0).astype(int)

        return df

    def _add_recruiting_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add recruiting-based features."""
        if "stars" in df.columns:
            df["elite_recruit"] = (df["stars"] >= 4).astype(int)
            df["blue_chip"] = (df["stars"] >= 4).astype(int)

        if "ranking_national" in df.columns:
            df["top_100"] = (df["ranking_national"] <= 100).astype(int)
            df["top_300"] = (df["ranking_national"] <= 300).astype(int)

        return df

    def calculate_nil_tier(self, valuation: float) -> str:
        """
        Determine NIL tier based on valuation.

        Args:
            valuation: Estimated NIL value

        Returns:
            NIL tier name
        """
        for tier, threshold in sorted(
            self.nil_tiers.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            if valuation >= threshold:
                return tier
        return "entry"

    def get_feature_importance_columns(self) -> List[str]:
        """
        Get list of feature columns for modeling.

        Returns:
            List of feature column names
        """
        return [
            "position_value_tier",
            "position_scarcity",
            "school_tier_value",
            "market_size",
            "yards_percentile",
            "td_percentile",
            "log_followers",
            "high_engagement",
            "elite_recruit",
            "top_100",
        ]
