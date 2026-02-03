"""
Transfer Portal Data Collector

Collects transfer portal entries, commitments, and player movement data.
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import cfbd
from cfbd.rest import ApiException

from ..utils.config import Config


class PortalDataCollector:
    """Collects transfer portal data and player movement information."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the portal data collector.

        Args:
            config: Configuration object with API keys and settings
        """
        self.config = config or Config()
        self._setup_api()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Portal-IQ/1.0 (Research)"
        })

    def _setup_api(self) -> None:
        """Configure the CFBD API client."""
        configuration = cfbd.Configuration()
        configuration.api_key["Authorization"] = self.config.cfbd_api_key
        configuration.api_key_prefix["Authorization"] = "Bearer"
        self.api_client = cfbd.ApiClient(configuration)

    def get_portal_entries(
        self,
        season: int,
        position: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get transfer portal entries for a given season.

        Args:
            season: The season year
            position: Optional position filter

        Returns:
            DataFrame with portal entries
        """
        api = cfbd.PlayersApi(self.api_client)
        try:
            transfers = api.get_transfer_portal(year=season)
            df = pd.DataFrame([t.to_dict() for t in transfers])

            if position and not df.empty:
                df = df[df["position"] == position]

            return df
        except ApiException as e:
            print(f"Error fetching portal data: {e}")
            return pd.DataFrame()

    def get_portal_commitments(self, season: int) -> pd.DataFrame:
        """
        Get portal players who have committed to new schools.

        Args:
            season: The season year

        Returns:
            DataFrame with portal commitments
        """
        df = self.get_portal_entries(season)
        if df.empty:
            return df

        # Filter to only committed players
        return df[df["destination"].notna()]

    def get_active_portal_players(self, season: int) -> pd.DataFrame:
        """
        Get players currently in the portal without a commitment.

        Args:
            season: The season year

        Returns:
            DataFrame with active portal players
        """
        df = self.get_portal_entries(season)
        if df.empty:
            return df

        # Filter to uncommitted players
        return df[df["destination"].isna()]

    def get_player_transfer_history(self, player_name: str) -> List[Dict[str, Any]]:
        """
        Get transfer history for a specific player.

        Args:
            player_name: Player name

        Returns:
            List of transfer records
        """
        history = []

        for season in range(
            self.config.seasons_range[0],
            self.config.seasons_range[1] + 1
        ):
            df = self.get_portal_entries(season)
            if df.empty:
                continue

            player_data = df[
                df["first_name"].str.lower().str.contains(
                    player_name.split()[0].lower(), na=False
                ) &
                df["last_name"].str.lower().str.contains(
                    player_name.split()[-1].lower(), na=False
                )
            ]

            for _, row in player_data.iterrows():
                history.append({
                    "season": season,
                    "origin": row.get("origin"),
                    "destination": row.get("destination"),
                    "transfer_date": row.get("transfer_date"),
                })

        return history

    def analyze_portal_trends(self, season: int) -> Dict[str, Any]:
        """
        Analyze transfer portal trends for a season.

        Args:
            season: The season year

        Returns:
            Dictionary with trend analysis
        """
        df = self.get_portal_entries(season)
        if df.empty:
            return {}

        return {
            "total_entries": len(df),
            "committed": len(df[df["destination"].notna()]),
            "uncommitted": len(df[df["destination"].isna()]),
            "by_position": df["position"].value_counts().to_dict(),
            "top_origins": df["origin"].value_counts().head(10).to_dict(),
            "top_destinations": df["destination"].value_counts().head(10).to_dict(),
        }

    def get_team_portal_activity(
        self,
        team: str,
        season: int,
    ) -> Dict[str, pd.DataFrame]:
        """
        Get portal activity for a specific team.

        Args:
            team: Team name
            season: The season year

        Returns:
            Dictionary with incoming and outgoing transfers
        """
        df = self.get_portal_entries(season)
        if df.empty:
            return {"incoming": pd.DataFrame(), "outgoing": pd.DataFrame()}

        incoming = df[df["destination"] == team]
        outgoing = df[df["origin"] == team]

        return {
            "incoming": incoming,
            "outgoing": outgoing,
        }
