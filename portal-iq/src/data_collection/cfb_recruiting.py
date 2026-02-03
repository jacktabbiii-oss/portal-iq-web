"""
Recruiting Data Collector

Collects recruiting rankings and player data from various sources.
"""

import pandas as pd
from typing import Optional, List
import cfbd
from cfbd.rest import ApiException

from ..utils.config import Config


class RecruitingDataCollector:
    """Collects recruiting rankings and prospect data."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the recruiting data collector.

        Args:
            config: Configuration object with API keys and settings
        """
        self.config = config or Config()
        self._setup_api()

    def _setup_api(self) -> None:
        """Configure the CFBD API client."""
        configuration = cfbd.Configuration()
        configuration.api_key["Authorization"] = self.config.cfbd_api_key
        configuration.api_key_prefix["Authorization"] = "Bearer"
        self.api_client = cfbd.ApiClient(configuration)

    def get_recruiting_rankings(
        self,
        year: int,
        position: Optional[str] = None,
        state: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get recruiting rankings for a given year.

        Args:
            year: Recruiting class year
            position: Optional position filter
            state: Optional state filter

        Returns:
            DataFrame with recruiting rankings
        """
        api = cfbd.RecruitingApi(self.api_client)
        try:
            recruits = api.get_recruiting_players(
                year=year,
                position=position,
                state=state,
            )
            return pd.DataFrame([r.to_dict() for r in recruits])
        except ApiException as e:
            print(f"Error fetching recruiting data: {e}")
            return pd.DataFrame()

    def get_team_recruiting_rankings(self, year: int) -> pd.DataFrame:
        """
        Get team recruiting class rankings.

        Args:
            year: Recruiting class year

        Returns:
            DataFrame with team recruiting rankings
        """
        api = cfbd.RecruitingApi(self.api_client)
        try:
            rankings = api.get_recruiting_teams(year=year)
            return pd.DataFrame([r.to_dict() for r in rankings])
        except ApiException as e:
            print(f"Error fetching team recruiting rankings: {e}")
            return pd.DataFrame()

    def get_player_recruit_profile(self, player_name: str, year: int) -> dict:
        """
        Get detailed recruiting profile for a player.

        Args:
            player_name: Player name
            year: Recruiting class year

        Returns:
            Dictionary with recruiting profile data
        """
        df = self.get_recruiting_rankings(year)
        if df.empty:
            return {}

        # Find player in rankings
        player_data = df[
            df["name"].str.lower().str.contains(player_name.lower(), na=False)
        ]

        if player_data.empty:
            return {}

        return player_data.iloc[0].to_dict()

    def get_transfer_recruit_history(self, player_name: str) -> dict:
        """
        Get original recruiting data for a transfer portal player.

        Args:
            player_name: Player name

        Returns:
            Dictionary with original recruiting data
        """
        # Search multiple years for the player
        for year in range(self.config.seasons_range[1], self.config.seasons_range[0] - 1, -1):
            profile = self.get_player_recruit_profile(player_name, year)
            if profile:
                return profile
        return {}

    def calculate_star_composite(self, rankings: dict) -> float:
        """
        Calculate composite star rating from multiple services.

        Args:
            rankings: Dictionary with rankings from different services

        Returns:
            Composite star rating
        """
        weights = {
            "247": 0.35,
            "rivals": 0.30,
            "espn": 0.25,
            "on3": 0.10,
        }

        total_weight = 0
        weighted_sum = 0

        for service, weight in weights.items():
            if service in rankings and rankings[service] is not None:
                weighted_sum += rankings[service] * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return weighted_sum / total_weight
