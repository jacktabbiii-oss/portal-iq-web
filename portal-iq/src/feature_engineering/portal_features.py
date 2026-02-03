"""
Portal Feature Engineering

Creates features for transfer portal prediction models.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..utils.config import Config


class PortalFeatureEngineer:
    """Engineers features for portal prediction models."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the portal feature engineer.

        Args:
            config: Configuration object with settings
        """
        self.config = config or Config()

    def create_features(
        self,
        player_data: pd.DataFrame,
        team_data: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """
        Create all portal-related features.

        Args:
            player_data: DataFrame with player information
            team_data: Optional DataFrame with team information

        Returns:
            DataFrame with engineered features
        """
        df = player_data.copy()

        # Player situation features
        df = self._add_situation_features(df)

        # Timing features
        df = self._add_timing_features(df)

        # Team fit features
        if team_data is not None:
            df = self._add_team_fit_features(df, team_data)

        # Movement probability features
        df = self._add_movement_features(df)

        return df

    def _add_situation_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add player situation features."""
        # Years remaining
        if "class_year" in df.columns:
            class_to_years = {
                "FR": 4, "SO": 3, "JR": 2, "SR": 1, "GR": 1
            }
            df["years_remaining"] = df["class_year"].map(class_to_years).fillna(2)

        # Depth chart position
        if "depth_chart_rank" in df.columns:
            df["is_starter"] = (df["depth_chart_rank"] == 1).astype(int)
            df["is_backup"] = (df["depth_chart_rank"] == 2).astype(int)

        # Playing time trend
        if "snaps_current" in df.columns and "snaps_previous" in df.columns:
            df["snap_trend"] = df["snaps_current"] - df["snaps_previous"]
            df["snap_decrease"] = (df["snap_trend"] < 0).astype(int)

        return df

    def _add_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add timing-based features."""
        if "portal_entry_date" in df.columns:
            df["portal_entry_date"] = pd.to_datetime(df["portal_entry_date"])

            # Days in portal
            today = datetime.now()
            df["days_in_portal"] = (today - df["portal_entry_date"]).dt.days

            # Portal window (early vs late)
            df["early_entry"] = (df["portal_entry_date"].dt.month == 12).astype(int)

            # Entry day of week
            df["entry_day_of_week"] = df["portal_entry_date"].dt.dayofweek

        return df

    def _add_team_fit_features(
        self,
        df: pd.DataFrame,
        team_data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Add team fit features."""
        # Position need score
        if "position" in df.columns and "position_needs" in team_data.columns:
            need_map = team_data.set_index("team")["position_needs"].to_dict()
            df["position_need_score"] = df.apply(
                lambda x: need_map.get(x.get("target_team", ""), {}).get(
                    x["position"], 0.5
                ),
                axis=1
            )

        # Scheme fit (placeholder)
        df["scheme_fit"] = 0.5

        # Geographic proximity
        if "home_state" in df.columns and "team_state" in df.columns:
            df["in_state"] = (df["home_state"] == df["team_state"]).astype(int)

        return df

    def _add_movement_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features predicting movement likelihood."""
        # Coaching change indicator
        if "coaching_change" in df.columns:
            df["coach_departed"] = df["coaching_change"].astype(int)

        # NIL opportunity gap
        if "current_nil" in df.columns and "potential_nil" in df.columns:
            df["nil_upside"] = df["potential_nil"] - df["current_nil"]
            df["significant_nil_gap"] = (df["nil_upside"] > 100000).astype(int)

        # School tier movement potential
        if "current_school_tier" in df.columns:
            tier_values = {
                "blue_blood": 6, "elite": 5, "power_brand": 4,
                "p4_mid": 3, "g5_strong": 2, "g5": 1,
            }
            df["current_tier_value"] = df["current_school_tier"].map(tier_values)
            df["can_move_up"] = (df["current_tier_value"] < 6).astype(int)

        return df

    def create_destination_features(
        self,
        player: Dict[str, Any],
        schools: List[str],
    ) -> pd.DataFrame:
        """
        Create features for predicting destination school.

        Args:
            player: Player information dictionary
            schools: List of potential destination schools

        Returns:
            DataFrame with school-specific features
        """
        records = []

        for school in schools:
            record = {
                "player_id": player.get("player_id"),
                "school": school,
                "position_need": 0.5,  # Would be filled from team needs
                "nil_potential": 0.5,  # Would be filled from school NIL data
                "scheme_fit": 0.5,  # Would be filled from scheme analysis
                "geographic_fit": 0.5,  # Would be calculated from location
                "tier_change": 0,  # Would compare school tiers
            }
            records.append(record)

        return pd.DataFrame(records)

    def get_feature_columns(self) -> List[str]:
        """
        Get list of feature columns for modeling.

        Returns:
            List of feature column names
        """
        return [
            "years_remaining",
            "is_starter",
            "snap_trend",
            "days_in_portal",
            "early_entry",
            "position_need_score",
            "scheme_fit",
            "in_state",
            "coach_departed",
            "nil_upside",
            "current_tier_value",
        ]
