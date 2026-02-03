"""
Draft Feature Engineering

Creates features for NFL draft projection models.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List

from ..utils.config import Config


class DraftFeatureEngineer:
    """Engineers features for draft projection models."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the draft feature engineer.

        Args:
            config: Configuration object with settings
        """
        self.config = config or Config()

    def create_features(
        self,
        player_data: pd.DataFrame,
        combine_data: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Create all draft-related features.

        Args:
            player_data: DataFrame with player information
            combine_data: Optional DataFrame with combine results

        Returns:
            DataFrame with engineered features
        """
        df = player_data.copy()

        # Physical attributes
        df = self._add_physical_features(df)

        # Production features
        df = self._add_production_features(df)

        # Combine/athletic features
        if combine_data is not None:
            df = self._add_athletic_features(df, combine_data)

        # Pedigree features
        df = self._add_pedigree_features(df)

        # Age features
        df = self._add_age_features(df)

        return df

    def _add_physical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add physical attribute features."""
        if "height" in df.columns and "weight" in df.columns:
            # BMI-like measure
            df["size_score"] = df["weight"] / (df["height"] ** 2) * 703

            # Position-specific size grades
            ideal_size = {
                "QB": (74, 220), "RB": (70, 210), "WR": (73, 200),
                "TE": (77, 250), "OT": (78, 310), "OG": (76, 315),
                "C": (75, 305), "DE": (77, 270), "DT": (75, 305),
                "LB": (74, 240), "CB": (71, 190), "S": (73, 205),
            }

            def size_grade(row):
                if row["position"] not in ideal_size:
                    return 0.5
                ideal_h, ideal_w = ideal_size[row["position"]]
                h_diff = abs(row["height"] - ideal_h)
                w_diff = abs(row["weight"] - ideal_w)
                return max(0, 1 - (h_diff * 0.05 + w_diff * 0.005))

            df["position_size_grade"] = df.apply(size_grade, axis=1)

        return df

    def _add_production_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add college production features."""
        # Career production
        if "career_yards" in df.columns and "career_games" in df.columns:
            df["career_yards_per_game"] = (
                df["career_yards"] / df["career_games"].replace(0, 1)
            )

        # Breakout age
        if "breakout_season" in df.columns and "birth_year" in df.columns:
            df["breakout_age"] = df["breakout_season"] - df["birth_year"]

        # Dominator rating (for skill positions)
        if "team_yards" in df.columns and "player_yards" in df.columns:
            df["dominator_rating"] = df["player_yards"] / df["team_yards"].replace(0, 1)

        # Production trend
        if "yards_yr1" in df.columns and "yards_yr2" in df.columns:
            df["production_trend"] = df["yards_yr2"] - df["yards_yr1"]
            df["production_improved"] = (df["production_trend"] > 0).astype(int)

        # Games started percentage
        if "games_started" in df.columns and "games_played" in df.columns:
            df["start_rate"] = (
                df["games_started"] / df["games_played"].replace(0, 1)
            )

        return df

    def _add_athletic_features(
        self,
        df: pd.DataFrame,
        combine_data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Add athletic testing features."""
        # Merge combine data
        if "player_id" in df.columns and "player_id" in combine_data.columns:
            combine_cols = [
                "player_id", "forty", "vertical", "broad_jump",
                "three_cone", "shuttle", "bench",
            ]
            available_cols = [c for c in combine_cols if c in combine_data.columns]
            df = df.merge(
                combine_data[available_cols],
                on="player_id",
                how="left"
            )

        # Create composite athletic scores
        if "forty" in df.columns:
            df["elite_speed"] = (df["forty"] < 4.45).astype(int)

        if "vertical" in df.columns and "broad_jump" in df.columns:
            df["explosiveness"] = (
                df["vertical"] * 0.5 + df["broad_jump"] * 0.01
            )

        # Relative Athletic Score placeholder
        df["ras_score"] = 5.0  # Would be calculated from all combine metrics

        return df

    def _add_pedigree_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add recruiting and school pedigree features."""
        if "recruiting_stars" in df.columns:
            df["five_star"] = (df["recruiting_stars"] == 5).astype(int)
            df["blue_chip"] = (df["recruiting_stars"] >= 4).astype(int)

        if "school" in df.columns:
            # Draft factory schools
            draft_factories = [
                "Alabama", "Ohio State", "LSU", "Georgia", "Clemson",
                "Michigan", "Penn State", "Notre Dame", "Florida", "Oklahoma"
            ]
            df["draft_factory"] = df["school"].isin(draft_factories).astype(int)

        if "conference" in df.columns:
            top_conferences = ["SEC", "Big Ten"]
            df["top_conference"] = df["conference"].isin(top_conferences).astype(int)

        return df

    def _add_age_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add age-related features."""
        if "age_at_draft" in df.columns:
            # Ideal age ranges by position
            df["optimal_age"] = df["age_at_draft"].between(21, 23).astype(int)
            df["young_prospect"] = (df["age_at_draft"] < 22).astype(int)
            df["older_prospect"] = (df["age_at_draft"] > 24).astype(int)

        if "years_in_college" in df.columns:
            df["early_declare"] = (df["years_in_college"] < 4).astype(int)

        return df

    def calculate_draft_grade(self, features: Dict[str, Any]) -> float:
        """
        Calculate overall draft grade from features.

        Args:
            features: Dictionary of feature values

        Returns:
            Draft grade 0-100
        """
        weights = {
            "production": 0.25,
            "athleticism": 0.25,
            "size": 0.15,
            "pedigree": 0.15,
            "age": 0.10,
            "intangibles": 0.10,
        }

        grade = 50  # Base grade

        # Adjust based on features
        if features.get("blue_chip"):
            grade += 10
        if features.get("elite_speed"):
            grade += 8
        if features.get("draft_factory"):
            grade += 5
        if features.get("dominator_rating", 0) > 0.3:
            grade += 10
        if features.get("older_prospect"):
            grade -= 5

        return min(100, max(0, grade))

    def get_feature_columns(self) -> List[str]:
        """
        Get list of feature columns for modeling.

        Returns:
            List of feature column names
        """
        return [
            "position_size_grade",
            "career_yards_per_game",
            "dominator_rating",
            "production_improved",
            "start_rate",
            "elite_speed",
            "explosiveness",
            "ras_score",
            "blue_chip",
            "draft_factory",
            "top_conference",
            "optimal_age",
        ]
