"""
Draft History Data Collector

Collects NFL draft history and player career data.
"""

import pandas as pd
from typing import Optional, List, Dict, Any
import nfl_data_py as nfl

from ..utils.config import Config


class DraftHistoryCollector:
    """Collects NFL draft picks and player career data."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the draft history collector.

        Args:
            config: Configuration object with settings
        """
        self.config = config or Config()

    def get_draft_picks(
        self,
        years: Optional[List[int]] = None,
        team: Optional[str] = None,
        position: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get NFL draft picks data.

        Args:
            years: List of draft years
            team: Optional NFL team filter
            position: Optional position filter

        Returns:
            DataFrame with draft picks
        """
        if years is None:
            years = list(range(
                self.config.seasons_range[0],
                self.config.seasons_range[1] + 1
            ))

        try:
            df = nfl.import_draft_picks(years)

            if team:
                df = df[df["team"] == team]

            if position:
                df = df[df["position"] == position]

            return df
        except Exception as e:
            print(f"Error fetching draft data: {e}")
            return pd.DataFrame()

    def get_combine_data(
        self,
        years: Optional[List[int]] = None,
        position: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get NFL combine results.

        Args:
            years: List of combine years
            position: Optional position filter

        Returns:
            DataFrame with combine data
        """
        if years is None:
            years = list(range(
                self.config.seasons_range[0],
                self.config.seasons_range[1] + 1
            ))

        try:
            df = nfl.import_combine_data(years)

            if position:
                df = df[df["position"] == position]

            return df
        except Exception as e:
            print(f"Error fetching combine data: {e}")
            return pd.DataFrame()

    def get_college_to_nfl_mapping(
        self,
        college_name: str,
    ) -> pd.DataFrame:
        """
        Get all NFL players who played at a specific college.

        Args:
            college_name: College/university name

        Returns:
            DataFrame with players drafted from that school
        """
        df = self.get_draft_picks()
        if df.empty:
            return df

        return df[
            df["college"].str.lower().str.contains(
                college_name.lower(), na=False
            )
        ]

    def analyze_draft_by_position(
        self,
        position: str,
        years: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze draft trends for a position.

        Args:
            position: Position to analyze
            years: List of years to include

        Returns:
            Dictionary with position draft analysis
        """
        df = self.get_draft_picks(years=years, position=position)
        if df.empty:
            return {}

        return {
            "total_drafted": len(df),
            "avg_pick": df["pick"].mean(),
            "first_round_count": len(df[df["round"] == 1]),
            "top_10_count": len(df[df["pick"] <= 10]),
            "by_round": df["round"].value_counts().to_dict(),
            "top_colleges": df["college"].value_counts().head(10).to_dict(),
        }

    def get_player_career_stats(
        self,
        player_name: str,
    ) -> Dict[str, Any]:
        """
        Get NFL career statistics for a player.

        Args:
            player_name: Player name

        Returns:
            Dictionary with career statistics
        """
        # Placeholder for detailed career stats
        return {
            "player_name": player_name,
            "years_played": 0,
            "games": 0,
            "starts": 0,
            "pro_bowls": 0,
            "all_pro": 0,
        }

    def calculate_draft_value(
        self,
        pick: int,
    ) -> float:
        """
        Calculate draft pick value using standard trade value chart.

        Args:
            pick: Draft pick number

        Returns:
            Draft pick value
        """
        # Simplified draft value curve
        if pick <= 0:
            return 0

        # Exponential decay value
        return 3000 * (0.95 ** (pick - 1))

    def get_bust_rate_by_position(
        self,
        position: str,
        round_num: int,
    ) -> float:
        """
        Calculate historical bust rate for position/round.

        Args:
            position: Player position
            round_num: Draft round

        Returns:
            Bust rate as percentage
        """
        # Placeholder - would calculate from historical data
        base_bust_rates = {
            1: 0.25,
            2: 0.40,
            3: 0.55,
            4: 0.65,
            5: 0.75,
            6: 0.82,
            7: 0.88,
        }
        return base_bust_rates.get(round_num, 0.90)
