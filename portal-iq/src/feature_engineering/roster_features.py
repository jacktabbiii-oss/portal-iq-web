"""
Roster Feature Engineering

Creates features for roster composition and optimization models.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List

from ..utils.config import Config


class RosterFeatureEngineer:
    """Engineers features for roster analysis and optimization."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the roster feature engineer.

        Args:
            config: Configuration object with settings
        """
        self.config = config or Config()

    def create_features(
        self,
        roster_data: pd.DataFrame,
        team_stats: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Create all roster-related features.

        Args:
            roster_data: DataFrame with roster information
            team_stats: Optional DataFrame with team statistics

        Returns:
            DataFrame with engineered features
        """
        df = roster_data.copy()

        # Roster composition features
        df = self._add_composition_features(df)

        # Depth features
        df = self._add_depth_features(df)

        # Experience features
        df = self._add_experience_features(df)

        # Talent features
        df = self._add_talent_features(df)

        return df

    def _add_composition_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add roster composition features."""
        if "position_group" in df.columns:
            # Position group counts
            position_counts = df.groupby("team")["position_group"].value_counts()
            position_counts = position_counts.unstack(fill_value=0)
            position_counts.columns = [f"count_{c}" for c in position_counts.columns]

            df = df.merge(
                position_counts,
                left_on="team",
                right_index=True,
                how="left"
            )

        # Scholarship count
        if "scholarship" in df.columns:
            scholarship_counts = df.groupby("team")["scholarship"].sum()
            df = df.merge(
                scholarship_counts.rename("total_scholarships"),
                left_on="team",
                right_index=True,
                how="left"
            )

        return df

    def _add_depth_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add depth chart features."""
        if "position" in df.columns and "depth" in df.columns:
            # Depth by position
            depth_by_pos = df.groupby(["team", "position"]).size()
            depth_by_pos = depth_by_pos.unstack(fill_value=0)

            # Thin positions (less than 3 scholarship players)
            thin_positions = (depth_by_pos < 3).sum(axis=1)
            df = df.merge(
                thin_positions.rename("thin_position_count"),
                left_on="team",
                right_index=True,
                how="left"
            )

        # Starter quality
        if "starter" in df.columns and "player_rating" in df.columns:
            starter_ratings = df[df["starter"] == True].groupby("team")["player_rating"].mean()
            df = df.merge(
                starter_ratings.rename("avg_starter_rating"),
                left_on="team",
                right_index=True,
                how="left"
            )

        return df

    def _add_experience_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add experience-based features."""
        if "class_year" in df.columns:
            # Class distribution
            class_to_years = {
                "FR": 1, "SO": 2, "JR": 3, "SR": 4, "GR": 5
            }
            df["years_in_program"] = df["class_year"].map(class_to_years)

            # Average experience
            avg_exp = df.groupby("team")["years_in_program"].mean()
            df = df.merge(
                avg_exp.rename("avg_years_experience"),
                left_on="team",
                right_index=True,
                how="left"
            )

            # Seniors count
            senior_count = df[df["class_year"].isin(["SR", "GR"])].groupby("team").size()
            df = df.merge(
                senior_count.rename("senior_count"),
                left_on="team",
                right_index=True,
                how="left"
            )

        # Returning production
        if "returning" in df.columns and "yards" in df.columns:
            returning_prod = df[df["returning"] == True].groupby("team")["yards"].sum()
            df = df.merge(
                returning_prod.rename("returning_yards"),
                left_on="team",
                right_index=True,
                how="left"
            )

        return df

    def _add_talent_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add talent-based features."""
        if "recruiting_stars" in df.columns:
            # Blue chip ratio
            blue_chips = df[df["recruiting_stars"] >= 4].groupby("team").size()
            total = df.groupby("team").size()
            blue_chip_ratio = blue_chips / total

            df = df.merge(
                blue_chip_ratio.rename("blue_chip_ratio"),
                left_on="team",
                right_index=True,
                how="left"
            )

            # Average star rating
            avg_stars = df.groupby("team")["recruiting_stars"].mean()
            df = df.merge(
                avg_stars.rename("avg_star_rating"),
                left_on="team",
                right_index=True,
                how="left"
            )

        # Transfer talent
        if "is_transfer" in df.columns and "recruiting_stars" in df.columns:
            transfer_talent = (
                df[df["is_transfer"] == True]
                .groupby("team")["recruiting_stars"]
                .mean()
            )
            df = df.merge(
                transfer_talent.rename("avg_transfer_stars"),
                left_on="team",
                right_index=True,
                how="left"
            )

        return df

    def calculate_roster_needs(
        self,
        roster: pd.DataFrame,
        ideal_composition: Optional[Dict[str, int]] = None,
    ) -> Dict[str, int]:
        """
        Calculate position needs based on roster composition.

        Args:
            roster: Current roster DataFrame
            ideal_composition: Ideal position counts (optional)

        Returns:
            Dictionary of position needs
        """
        if ideal_composition is None:
            ideal_composition = {
                "QB": 3, "RB": 4, "WR": 8, "TE": 3,
                "OL": 15, "DL": 10, "LB": 8, "DB": 10,
                "K": 1, "P": 1, "LS": 1,
            }

        current = roster["position"].value_counts().to_dict()

        needs = {}
        for position, ideal in ideal_composition.items():
            current_count = current.get(position, 0)
            need = max(0, ideal - current_count)
            needs[position] = need

        return needs

    def get_feature_columns(self) -> List[str]:
        """
        Get list of feature columns for modeling.

        Returns:
            List of feature column names
        """
        return [
            "total_scholarships",
            "thin_position_count",
            "avg_starter_rating",
            "avg_years_experience",
            "senior_count",
            "returning_yards",
            "blue_chip_ratio",
            "avg_star_rating",
            "avg_transfer_stars",
        ]
