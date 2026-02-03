"""
College Football Data API Client

Direct REST API client for collegefootballdata.com
Uses requests instead of the outdated cfbd package.
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

import pandas as pd
import requests
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CFBDataAPI:
    """
    Direct REST API client for College Football Data.

    Endpoints:
    - /teams/fbs - FBS teams
    - /roster - Team rosters
    - /stats/player/season - Player season stats
    - /games - Game results
    - /rankings - Team rankings
    - /talent - Team talent composite
    """

    BASE_URL = "https://api.collegefootballdata.com"
    RATE_LIMIT_SECONDS = 0.3

    def __init__(self, api_key: Optional[str] = None, data_dir: Optional[str] = None):
        """Initialize the API client."""
        load_dotenv()

        self.api_key = api_key or os.getenv("CFBD_API_KEY")
        if not self.api_key:
            raise ValueError("CFBD_API_KEY not found. Set it in .env or pass directly.")

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

        # Data directories
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent.parent.parent.parent / "data"

        self.cache_dir = self.data_dir / "cache"
        self.processed_dir = self.data_dir / "processed"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"CFBDataAPI initialized. Data dir: {self.data_dir}")

    def _request(self, endpoint: str, params: Dict = None) -> Optional[List[Dict]]:
        """Make a rate-limited API request."""
        time.sleep(self.RATE_LIMIT_SECONDS)

        url = f"{self.BASE_URL}{endpoint}"

        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=30)

            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 401:
                logger.error("Unauthorized - check your API key")
                return None
            elif resp.status_code == 429:
                logger.warning("Rate limited - waiting 60s")
                time.sleep(60)
                return self._request(endpoint, params)
            else:
                logger.error(f"API error {resp.status_code}: {resp.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {endpoint}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    def get_fbs_teams(self, year: int = 2024) -> pd.DataFrame:
        """Get list of FBS teams for a year."""
        logger.info(f"Fetching FBS teams for {year}...")

        data = self._request("/teams/fbs", {"year": year})

        if not data:
            return pd.DataFrame()

        teams = []
        for team in data:
            teams.append({
                "team_id": team.get("id"),
                "school": team.get("school"),
                "mascot": team.get("mascot"),
                "abbreviation": team.get("abbreviation"),
                "conference": team.get("conference"),
                "division": team.get("division"),
                "color": team.get("color"),
                "logo": team.get("logos", [None])[0] if team.get("logos") else None,
            })

        df = pd.DataFrame(teams)
        logger.info(f"Got {len(df)} FBS teams")
        return df

    def get_roster(self, team: str, year: int = 2024) -> pd.DataFrame:
        """Get roster for a specific team."""
        data = self._request("/roster", {"team": team, "year": year})

        if not data:
            return pd.DataFrame()

        players = []
        for player in data:
            first = player.get("firstName", "")
            last = player.get("lastName", "")
            players.append({
                "player_id": player.get("id"),
                "first_name": first,
                "last_name": last,
                "player_name": f"{first} {last}".strip(),
                "team": team,
                "position": player.get("position"),
                "height": player.get("height"),
                "weight": player.get("weight"),
                "year": player.get("year"),
                "jersey": player.get("jersey"),
                "home_city": player.get("homeCity"),
                "home_state": player.get("homeState"),
                "home_country": player.get("homeCountry"),
                "recruit_school": player.get("recruitSchool"),
                "season": year,
            })

        return pd.DataFrame(players)

    def get_all_rosters(self, year: int = 2024) -> pd.DataFrame:
        """Get rosters for all FBS teams."""
        logger.info(f"Fetching all FBS rosters for {year}...")

        teams_df = self.get_fbs_teams(year)
        if teams_df.empty:
            return pd.DataFrame()

        all_rosters = []
        total = len(teams_df)

        for idx, row in teams_df.iterrows():
            team = row["school"]
            logger.info(f"  [{idx+1}/{total}] {team}")

            roster = self.get_roster(team, year)
            if not roster.empty:
                roster["conference"] = row["conference"]
                all_rosters.append(roster)

        if not all_rosters:
            return pd.DataFrame()

        df = pd.concat(all_rosters, ignore_index=True)
        logger.info(f"Got {len(df)} total players across {total} teams")
        return df

    def get_player_stats(self, year: int = 2024, category: str = "passing") -> pd.DataFrame:
        """Get player season stats for a category (passing, rushing, receiving, defense)."""
        logger.info(f"Fetching {category} stats for {year}...")

        data = self._request("/stats/player/season", {
            "year": year,
            "category": category,
        })

        if not data:
            return pd.DataFrame()

        stats = []
        for player in data:
            stat_dict = {
                "player_id": player.get("playerId"),
                "player_name": player.get("player"),
                "team": player.get("team"),
                "conference": player.get("conference"),
                "season": year,
                "category": category,
                "stat_type": player.get("statType"),
                "stat_value": player.get("stat"),
            }
            stats.append(stat_dict)

        df = pd.DataFrame(stats)
        logger.info(f"Got {len(df)} {category} stat entries")
        return df

    def get_all_player_stats(self, year: int = 2024) -> pd.DataFrame:
        """Get all player stats (passing, rushing, receiving) and pivot to wide format."""
        categories = ["passing", "rushing", "receiving"]

        all_stats = []
        for cat in categories:
            stats = self.get_player_stats(year, cat)
            if not stats.empty:
                all_stats.append(stats)

        if not all_stats:
            return pd.DataFrame()

        df = pd.concat(all_stats, ignore_index=True)

        # Pivot to wide format
        df["stat_col"] = df["category"] + "_" + df["stat_type"].astype(str)

        pivot = df.pivot_table(
            index=["player_id", "player_name", "team", "conference", "season"],
            columns="stat_col",
            values="stat_value",
            aggfunc="first"
        ).reset_index()

        logger.info(f"Got stats for {len(pivot)} unique players")
        return pivot

    def get_team_talent(self, year: int = 2024) -> pd.DataFrame:
        """Get team talent composite rankings."""
        logger.info(f"Fetching team talent for {year}...")

        data = self._request("/talent", {"year": year})

        if not data:
            return pd.DataFrame()

        teams = []
        for team in data:
            teams.append({
                "school": team.get("school"),
                "talent": team.get("talent"),
                "year": year,
            })

        df = pd.DataFrame(teams)
        logger.info(f"Got talent data for {len(df)} teams")
        return df

    def get_team_records(self, year: int = 2024) -> pd.DataFrame:
        """Get team win/loss records."""
        logger.info(f"Fetching team records for {year}...")

        data = self._request("/records", {"year": year})

        if not data:
            return pd.DataFrame()

        records = []
        for team in data:
            total = team.get("total", {})
            conf = team.get("conferenceGames", {})

            records.append({
                "school": team.get("team"),
                "conference": team.get("conference"),
                "year": year,
                "total_wins": total.get("wins", 0),
                "total_losses": total.get("losses", 0),
                "conf_wins": conf.get("wins", 0) if conf else 0,
                "conf_losses": conf.get("losses", 0) if conf else 0,
            })

        df = pd.DataFrame(records)
        logger.info(f"Got records for {len(df)} teams")
        return df

    def get_sp_ratings(self, year: int = 2024) -> pd.DataFrame:
        """Get SP+ ratings for teams."""
        logger.info(f"Fetching SP+ ratings for {year}...")

        data = self._request("/ratings/sp", {"year": year})

        if not data:
            return pd.DataFrame()

        ratings = []
        for team in data:
            offense = team.get("offense", {})
            defense = team.get("defense", {})

            ratings.append({
                "school": team.get("team"),
                "conference": team.get("conference"),
                "year": year,
                "sp_overall": team.get("rating"),
                "sp_offense": offense.get("rating") if offense else None,
                "sp_defense": defense.get("rating") if defense else None,
            })

        df = pd.DataFrame(ratings)
        logger.info(f"Got SP+ ratings for {len(df)} teams")
        return df

    def collect_all(self, years: List[int] = [2024]) -> Dict[str, pd.DataFrame]:
        """Collect all data for specified years."""
        logger.info("=" * 60)
        logger.info(f"COLLECTING CFBD DATA FOR YEARS: {years}")
        logger.info("=" * 60)

        results = {
            "rosters": [],
            "player_stats": [],
            "team_talent": [],
            "team_records": [],
            "sp_ratings": [],
        }

        for year in years:
            logger.info(f"\n--- Year {year} ---")

            # Rosters
            rosters = self.get_all_rosters(year)
            if not rosters.empty:
                results["rosters"].append(rosters)

            # Player stats
            stats = self.get_all_player_stats(year)
            if not stats.empty:
                results["player_stats"].append(stats)

            # Team data
            talent = self.get_team_talent(year)
            if not talent.empty:
                results["team_talent"].append(talent)

            records = self.get_team_records(year)
            if not records.empty:
                results["team_records"].append(records)

            sp = self.get_sp_ratings(year)
            if not sp.empty:
                results["sp_ratings"].append(sp)

        # Combine all years
        combined = {}
        for key, dfs in results.items():
            if dfs:
                combined[key] = pd.concat(dfs, ignore_index=True)
                logger.info(f"{key}: {len(combined[key])} rows")
            else:
                combined[key] = pd.DataFrame()
                logger.warning(f"{key}: No data collected")

        return combined

    def save_data(self, data: Dict[str, pd.DataFrame], prefix: str = "cfbd") -> None:
        """Save collected data to processed directory."""
        timestamp = datetime.now().strftime("%Y%m%d")

        for name, df in data.items():
            if df.empty:
                continue

            path = self.processed_dir / f"{prefix}_{name}_{timestamp}.csv"
            df.to_csv(path, index=False)
            logger.info(f"Saved {name} to {path}")

        # Also save latest versions without timestamp
        for name, df in data.items():
            if df.empty:
                continue

            path = self.processed_dir / f"{prefix}_{name}.csv"
            df.to_csv(path, index=False)


if __name__ == "__main__":
    print("CFBD API Test")
    print("=" * 50)

    api = CFBDataAPI()

    # Quick test
    teams = api.get_fbs_teams(2024)
    print(f"\nFBS Teams: {len(teams)}")
    print(teams.head())

    # Get one roster
    roster = api.get_roster("Alabama", 2024)
    print(f"\nAlabama Roster: {len(roster)} players")
    print(roster.head())
