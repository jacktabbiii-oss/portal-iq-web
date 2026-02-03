"""
CFB Stats Data Collector

Collects college football statistics from CFBD API.
Uses the cfbd Python package for API access.
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import pandas as pd
from dotenv import load_dotenv
import cfbd
from cfbd.rest import ApiException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CFBStatsCollector:
    """Collects college football statistics from CFBD API."""

    # Rate limiting: seconds between API calls
    RATE_LIMIT_SECONDS = 0.5

    # Cache validity: hours before cache expires
    CACHE_HOURS = 24

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the CFB stats collector.

        Args:
            data_dir: Base data directory (defaults to project data folder)
        """
        # Load environment variables
        load_dotenv()

        # Set up data directories
        if data_dir is None:
            # Find project root (look for config.yaml or go up from src)
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "config.yaml").exists():
                    data_dir = str(current / "data")
                    break
                current = current.parent
            else:
                data_dir = "data"

        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.cache_dir = self.data_dir / "cache"

        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Configure CFBD API
        self._setup_api()

        logger.info(f"CFBStatsCollector initialized. Data dir: {self.data_dir}")

    def _setup_api(self) -> None:
        """Configure the CFBD API client with API key from environment."""
        api_key = os.getenv("CFBD_API_KEY")

        if not api_key:
            logger.warning(
                "CFBD_API_KEY not found in environment. "
                "API calls will fail. Set it in .env file."
            )
            api_key = ""

        self.configuration = cfbd.Configuration()
        self.configuration.api_key["Authorization"] = api_key
        self.configuration.api_key_prefix["Authorization"] = "Bearer"
        self.api_client = cfbd.ApiClient(self.configuration)

    def _rate_limit(self) -> None:
        """Sleep to respect API rate limits."""
        time.sleep(self.RATE_LIMIT_SECONDS)

    def _get_cache_path(self, name: str) -> Path:
        """Get cache file path for a dataset."""
        return self.cache_dir / f"{name}_cache.csv"

    def _get_cache_meta_path(self, name: str) -> Path:
        """Get cache metadata file path."""
        return self.cache_dir / f"{name}_cache_meta.txt"

    def _is_cache_valid(self, name: str) -> bool:
        """
        Check if cached data exists and is still valid.

        Args:
            name: Dataset name

        Returns:
            True if cache is valid, False otherwise
        """
        cache_path = self._get_cache_path(name)
        meta_path = self._get_cache_meta_path(name)

        if not cache_path.exists() or not meta_path.exists():
            return False

        try:
            with open(meta_path, "r") as f:
                cache_time = datetime.fromisoformat(f.read().strip())

            age = datetime.now() - cache_time
            if age < timedelta(hours=self.CACHE_HOURS):
                logger.info(f"Valid cache found for {name} (age: {age})")
                return True
            else:
                logger.info(f"Cache expired for {name} (age: {age})")
                return False
        except Exception as e:
            logger.warning(f"Error checking cache for {name}: {e}")
            return False

    def _load_from_cache(self, name: str) -> Optional[pd.DataFrame]:
        """
        Load data from cache if valid.

        Args:
            name: Dataset name

        Returns:
            DataFrame if cache is valid, None otherwise
        """
        if self._is_cache_valid(name):
            try:
                cache_path = self._get_cache_path(name)
                df = pd.read_csv(cache_path)
                logger.info(f"Loaded {len(df)} rows from cache: {name}")
                return df
            except Exception as e:
                logger.warning(f"Error loading cache for {name}: {e}")
        return None

    def _save_to_cache(self, df: pd.DataFrame, name: str) -> None:
        """
        Save data to cache with timestamp.

        Args:
            df: DataFrame to cache
            name: Dataset name
        """
        try:
            cache_path = self._get_cache_path(name)
            meta_path = self._get_cache_meta_path(name)

            df.to_csv(cache_path, index=False)

            with open(meta_path, "w") as f:
                f.write(datetime.now().isoformat())

            logger.info(f"Saved {len(df)} rows to cache: {name}")
        except Exception as e:
            logger.warning(f"Error saving cache for {name}: {e}")

    def _save_to_raw(self, df: pd.DataFrame, name: str) -> Path:
        """
        Save data to raw directory with timestamp.

        Args:
            df: DataFrame to save
            name: Dataset name

        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.csv"
        filepath = self.raw_dir / filename

        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(df)} rows to {filepath}")

        return filepath

    def collect_player_stats(
        self,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """
        Collect player season statistics for passing, rushing, receiving.

        Args:
            start_year: First season to collect
            end_year: Last season to collect (inclusive)

        Returns:
            DataFrame with player statistics including:
            - player name, team, conference, season, games played
            - all stat columns for passing, rushing, receiving
        """
        cache_name = f"player_stats_{start_year}_{end_year}"

        # Check cache first
        cached = self._load_from_cache(cache_name)
        if cached is not None:
            return cached

        logger.info(f"Collecting player stats for {start_year}-{end_year}")

        players_api = cfbd.PlayersApi(self.api_client)
        all_stats = []

        stat_categories = ["passing", "rushing", "receiving"]

        for year in range(start_year, end_year + 1):
            logger.info(f"Fetching player stats for {year}...")

            for category in stat_categories:
                try:
                    self._rate_limit()

                    stats = players_api.get_player_season_stats(
                        year=year,
                        category=category,
                    )

                    for player_stat in stats:
                        # Convert to dictionary
                        stat_dict = {
                            "player_id": getattr(player_stat, "player_id", None),
                            "player": getattr(player_stat, "player", None),
                            "team": getattr(player_stat, "team", None),
                            "conference": getattr(player_stat, "conference", None),
                            "season": year,
                            "category": category,
                        }

                        # Add all stat type values
                        if hasattr(player_stat, "stat_type") and hasattr(player_stat, "stat"):
                            stat_dict["stat_type"] = player_stat.stat_type
                            stat_dict["stat_value"] = player_stat.stat

                        all_stats.append(stat_dict)

                    logger.info(
                        f"  {year} {category}: {len(stats)} player stat entries"
                    )

                except ApiException as e:
                    logger.error(f"API error for {year} {category}: {e}")
                except Exception as e:
                    logger.error(f"Error fetching {year} {category}: {e}")

        if not all_stats:
            logger.warning("No player stats collected!")
            return pd.DataFrame()

        # Create DataFrame and pivot to get stats as columns
        df = pd.DataFrame(all_stats)

        # Pivot to get one row per player per season with stats as columns
        if "stat_type" in df.columns and not df.empty:
            try:
                df_pivot = df.pivot_table(
                    index=["player_id", "player", "team", "conference", "season", "category"],
                    columns="stat_type",
                    values="stat_value",
                    aggfunc="first"
                ).reset_index()
                df = df_pivot
            except Exception as e:
                logger.warning(f"Could not pivot stats: {e}")

        logger.info(f"Collected {len(df)} player stat rows total")

        # Save to cache
        self._save_to_cache(df, cache_name)

        return df

    def collect_player_info(
        self,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """
        Collect player roster information for each team.

        Args:
            start_year: First season to collect
            end_year: Last season to collect (inclusive)

        Returns:
            DataFrame with player roster information including:
            - player name, team, position, height, weight
            - year (FR/SO/JR/SR), hometown, jersey number
        """
        cache_name = f"player_info_{start_year}_{end_year}"

        # Check cache first
        cached = self._load_from_cache(cache_name)
        if cached is not None:
            return cached

        logger.info(f"Collecting player info for {start_year}-{end_year}")

        teams_api = cfbd.TeamsApi(self.api_client)
        players_api = cfbd.PlayersApi(self.api_client)

        all_players = []

        for year in range(start_year, end_year + 1):
            logger.info(f"Fetching rosters for {year}...")

            try:
                # First get list of FBS teams
                self._rate_limit()
                teams = teams_api.get_fbs_teams(year=year)
                team_names = [t.school for t in teams]

                logger.info(f"  Found {len(team_names)} FBS teams for {year}")

                # Get roster for each team
                for team in team_names:
                    try:
                        self._rate_limit()
                        roster = players_api.get_roster(team=team, year=year)

                        for player in roster:
                            player_dict = {
                                "player_id": getattr(player, "id", None),
                                "player_name": f"{getattr(player, 'first_name', '')} {getattr(player, 'last_name', '')}".strip(),
                                "first_name": getattr(player, "first_name", None),
                                "last_name": getattr(player, "last_name", None),
                                "team": team,
                                "position": getattr(player, "position", None),
                                "height": getattr(player, "height", None),
                                "weight": getattr(player, "weight", None),
                                "year": getattr(player, "year", None),
                                "jersey": getattr(player, "jersey", None),
                                "home_city": getattr(player, "home_city", None),
                                "home_state": getattr(player, "home_state", None),
                                "home_country": getattr(player, "home_country", None),
                                "season": year,
                            }
                            all_players.append(player_dict)

                    except ApiException as e:
                        logger.warning(f"API error for {team} {year} roster: {e}")
                    except Exception as e:
                        logger.warning(f"Error fetching {team} {year} roster: {e}")

                year_count = len([p for p in all_players if p["season"] == year])
                logger.info(f"  {year}: collected {year_count} players")

            except ApiException as e:
                logger.error(f"API error getting teams for {year}: {e}")
            except Exception as e:
                logger.error(f"Error getting teams for {year}: {e}")

        if not all_players:
            logger.warning("No player info collected!")
            return pd.DataFrame()

        df = pd.DataFrame(all_players)
        logger.info(f"Collected {len(df)} player roster rows total")

        # Save to cache
        self._save_to_cache(df, cache_name)

        return df

    def collect_team_data(
        self,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """
        Collect team data including records, SP+ ratings, and recruiting.

        Args:
            start_year: First season to collect
            end_year: Last season to collect (inclusive)

        Returns:
            DataFrame with team data including:
            - wins, losses per season
            - SP+ ratings (overall, offense, defense)
            - talent composite rankings
            - recruiting class rankings per year
        """
        cache_name = f"team_data_{start_year}_{end_year}"

        # Check cache first
        cached = self._load_from_cache(cache_name)
        if cached is not None:
            return cached

        logger.info(f"Collecting team data for {start_year}-{end_year}")

        games_api = cfbd.GamesApi(self.api_client)
        stats_api = cfbd.StatsApi(self.api_client)
        recruiting_api = cfbd.RecruitingApi(self.api_client)
        teams_api = cfbd.TeamsApi(self.api_client)

        all_team_data = []

        for year in range(start_year, end_year + 1):
            logger.info(f"Fetching team data for {year}...")

            team_records = {}
            team_sp = {}
            team_talent = {}
            team_recruiting = {}

            # Get team records (wins/losses)
            try:
                self._rate_limit()
                records = games_api.get_team_records(year=year)

                for record in records:
                    team_name = getattr(record, "team", None)
                    if team_name:
                        total = getattr(record, "total", None)
                        conf = getattr(record, "conference_games", None)
                        team_records[team_name] = {
                            "wins": getattr(total, "wins", 0) if total else 0,
                            "losses": getattr(total, "losses", 0) if total else 0,
                            "conference_wins": getattr(conf, "wins", 0) if conf else 0,
                            "conference_losses": getattr(conf, "losses", 0) if conf else 0,
                        }

                logger.info(f"  {year}: {len(team_records)} team records")
            except ApiException as e:
                logger.warning(f"API error getting records for {year}: {e}")
            except Exception as e:
                logger.warning(f"Error getting records for {year}: {e}")

            # Get SP+ ratings
            try:
                self._rate_limit()
                sp_ratings = stats_api.get_sp_ratings(year=year)

                for sp in sp_ratings:
                    team_name = getattr(sp, "team", None)
                    if team_name:
                        offense = getattr(sp, "offense", None)
                        defense = getattr(sp, "defense", None)
                        team_sp[team_name] = {
                            "sp_overall": getattr(sp, "rating", None),
                            "sp_offense": getattr(offense, "rating", None) if offense else None,
                            "sp_defense": getattr(defense, "rating", None) if defense else None,
                        }

                logger.info(f"  {year}: {len(team_sp)} SP+ ratings")
            except ApiException as e:
                logger.warning(f"API error getting SP+ for {year}: {e}")
            except Exception as e:
                logger.warning(f"Error getting SP+ for {year}: {e}")

            # Get talent composite
            try:
                self._rate_limit()
                talent = teams_api.get_talent(year=year)

                for t in talent:
                    team_name = getattr(t, "school", None)
                    if team_name:
                        team_talent[team_name] = {
                            "talent_rating": getattr(t, "talent", None),
                        }

                logger.info(f"  {year}: {len(team_talent)} talent ratings")
            except ApiException as e:
                logger.warning(f"API error getting talent for {year}: {e}")
            except Exception as e:
                logger.warning(f"Error getting talent for {year}: {e}")

            # Get recruiting rankings
            try:
                self._rate_limit()
                recruiting = recruiting_api.get_recruiting_teams(year=year)

                for r in recruiting:
                    team_name = getattr(r, "team", None)
                    if team_name:
                        team_recruiting[team_name] = {
                            "recruiting_rank": getattr(r, "rank", None),
                            "recruiting_points": getattr(r, "points", None),
                        }

                logger.info(f"  {year}: {len(team_recruiting)} recruiting rankings")
            except ApiException as e:
                logger.warning(f"API error getting recruiting for {year}: {e}")
            except Exception as e:
                logger.warning(f"Error getting recruiting for {year}: {e}")

            # Combine all team data
            all_teams = (
                set(team_records.keys()) |
                set(team_sp.keys()) |
                set(team_talent.keys()) |
                set(team_recruiting.keys())
            )

            for team in all_teams:
                team_data = {
                    "team": team,
                    "season": year,
                }

                # Add record data
                if team in team_records:
                    team_data.update(team_records[team])

                # Add SP+ data
                if team in team_sp:
                    team_data.update(team_sp[team])

                # Add talent data
                if team in team_talent:
                    team_data.update(team_talent[team])

                # Add recruiting data
                if team in team_recruiting:
                    team_data.update(team_recruiting[team])

                all_team_data.append(team_data)

        if not all_team_data:
            logger.warning("No team data collected!")
            return pd.DataFrame()

        df = pd.DataFrame(all_team_data)
        logger.info(f"Collected {len(df)} team data rows total")

        # Save to cache
        self._save_to_cache(df, cache_name)

        return df

    def collect_game_results(
        self,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame:
        """
        Collect game-by-game results for all teams.

        Args:
            start_year: First season to collect
            end_year: Last season to collect (inclusive)

        Returns:
            DataFrame with game results including:
            - teams (home/away), scores
            - conference game flag, home/away indicator
            - week, season type
            - useful for strength of schedule calculations
        """
        cache_name = f"game_results_{start_year}_{end_year}"

        # Check cache first
        cached = self._load_from_cache(cache_name)
        if cached is not None:
            return cached

        logger.info(f"Collecting game results for {start_year}-{end_year}")

        games_api = cfbd.GamesApi(self.api_client)
        all_games = []

        for year in range(start_year, end_year + 1):
            logger.info(f"Fetching games for {year}...")

            # Get regular season games
            try:
                self._rate_limit()

                games = games_api.get_games(
                    year=year,
                    season_type="regular",
                    division="fbs",
                )

                for game in games:
                    game_dict = {
                        "game_id": getattr(game, "id", None),
                        "season": year,
                        "week": getattr(game, "week", None),
                        "season_type": "regular",
                        "start_date": getattr(game, "start_date", None),
                        "neutral_site": getattr(game, "neutral_site", False),
                        "conference_game": getattr(game, "conference_game", False),
                        "home_team": getattr(game, "home_team", None),
                        "home_conference": getattr(game, "home_conference", None),
                        "home_points": getattr(game, "home_points", None),
                        "away_team": getattr(game, "away_team", None),
                        "away_conference": getattr(game, "away_conference", None),
                        "away_points": getattr(game, "away_points", None),
                        "venue": getattr(game, "venue", None),
                    }

                    # Calculate winner
                    home_pts = game_dict["home_points"]
                    away_pts = game_dict["away_points"]
                    if home_pts is not None and away_pts is not None:
                        if home_pts > away_pts:
                            game_dict["winner"] = game_dict["home_team"]
                        elif away_pts > home_pts:
                            game_dict["winner"] = game_dict["away_team"]
                        else:
                            game_dict["winner"] = None  # Tie

                    all_games.append(game_dict)

                regular_count = len([
                    g for g in all_games
                    if g["season"] == year and g["season_type"] == "regular"
                ])
                logger.info(f"  {year} regular: {regular_count} games")

            except ApiException as e:
                logger.error(f"API error getting regular games for {year}: {e}")
            except Exception as e:
                logger.error(f"Error getting regular games for {year}: {e}")

            # Get postseason games
            try:
                self._rate_limit()
                postseason = games_api.get_games(
                    year=year,
                    season_type="postseason",
                    division="fbs",
                )

                for game in postseason:
                    game_dict = {
                        "game_id": getattr(game, "id", None),
                        "season": year,
                        "week": getattr(game, "week", None),
                        "season_type": "postseason",
                        "start_date": getattr(game, "start_date", None),
                        "neutral_site": getattr(game, "neutral_site", True),
                        "conference_game": False,
                        "home_team": getattr(game, "home_team", None),
                        "home_conference": getattr(game, "home_conference", None),
                        "home_points": getattr(game, "home_points", None),
                        "away_team": getattr(game, "away_team", None),
                        "away_conference": getattr(game, "away_conference", None),
                        "away_points": getattr(game, "away_points", None),
                        "venue": getattr(game, "venue", None),
                    }

                    home_pts = game_dict["home_points"]
                    away_pts = game_dict["away_points"]
                    if home_pts is not None and away_pts is not None:
                        if home_pts > away_pts:
                            game_dict["winner"] = game_dict["home_team"]
                        elif away_pts > home_pts:
                            game_dict["winner"] = game_dict["away_team"]
                        else:
                            game_dict["winner"] = None

                    all_games.append(game_dict)

                post_count = len([
                    g for g in all_games
                    if g["season"] == year and g["season_type"] == "postseason"
                ])
                logger.info(f"  {year} postseason: {post_count} games")

            except ApiException as e:
                logger.error(f"API error getting postseason for {year}: {e}")
            except Exception as e:
                logger.error(f"Error getting postseason for {year}: {e}")

        if not all_games:
            logger.warning("No game results collected!")
            return pd.DataFrame()

        df = pd.DataFrame(all_games)
        logger.info(f"Collected {len(df)} game results total")

        # Save to cache
        self._save_to_cache(df, cache_name)

        return df

    def collect_all(
        self,
        start_year: int = 2020,
        end_year: int = 2025,
    ) -> Dict[str, pd.DataFrame]:
        """
        Run all collection methods and save results.

        Args:
            start_year: First season to collect
            end_year: Last season to collect (inclusive)

        Returns:
            Dictionary of all collected DataFrames:
            - player_stats: Player season statistics
            - player_info: Player roster information
            - team_data: Team records, ratings, recruiting
            - game_results: Game-by-game results
        """
        logger.info("=" * 60)
        logger.info(f"Starting full data collection: {start_year}-{end_year}")
        logger.info("=" * 60)

        start_time = datetime.now()
        results = {}
        warnings = []

        # Collect player stats
        logger.info("\n[1/4] Collecting player stats...")
        try:
            results["player_stats"] = self.collect_player_stats(start_year, end_year)
            if results["player_stats"].empty:
                warnings.append("Player stats: No data collected")
        except Exception as e:
            logger.error(f"Failed to collect player stats: {e}")
            results["player_stats"] = pd.DataFrame()
            warnings.append(f"Player stats: Collection failed - {e}")

        # Collect player info
        logger.info("\n[2/4] Collecting player info...")
        try:
            results["player_info"] = self.collect_player_info(start_year, end_year)
            if results["player_info"].empty:
                warnings.append("Player info: No data collected")
        except Exception as e:
            logger.error(f"Failed to collect player info: {e}")
            results["player_info"] = pd.DataFrame()
            warnings.append(f"Player info: Collection failed - {e}")

        # Collect team data
        logger.info("\n[3/4] Collecting team data...")
        try:
            results["team_data"] = self.collect_team_data(start_year, end_year)
            if results["team_data"].empty:
                warnings.append("Team data: No data collected")
        except Exception as e:
            logger.error(f"Failed to collect team data: {e}")
            results["team_data"] = pd.DataFrame()
            warnings.append(f"Team data: Collection failed - {e}")

        # Collect game results
        logger.info("\n[4/4] Collecting game results...")
        try:
            results["game_results"] = self.collect_game_results(start_year, end_year)
            if results["game_results"].empty:
                warnings.append("Game results: No data collected")
        except Exception as e:
            logger.error(f"Failed to collect game results: {e}")
            results["game_results"] = pd.DataFrame()
            warnings.append(f"Game results: Collection failed - {e}")

        # Save all to raw directory with timestamps
        logger.info("\n" + "=" * 60)
        logger.info("Saving datasets to raw directory...")

        for name, df in results.items():
            if not df.empty:
                filepath = self._save_to_raw(df, name)
                logger.info(f"  Saved {name}: {filepath}")

        # Print summary
        elapsed = datetime.now() - start_time

        logger.info("\n" + "=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Date Range: {start_year} - {end_year}")
        logger.info(f"Elapsed Time: {elapsed}")
        logger.info("")
        logger.info("Rows Collected:")
        for name, df in results.items():
            logger.info(f"  {name}: {len(df):,} rows")

        if warnings:
            logger.info("")
            logger.info("WARNINGS:")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        logger.info("=" * 60)

        return results


if __name__ == "__main__":
    # Run standalone collection
    print("Portal IQ - CFB Stats Collector")
    print("-" * 40)

    collector = CFBStatsCollector()

    # Collect all data for default date range
    data = collector.collect_all()

    print("\nCollection complete!")
    print(f"Datasets collected: {list(data.keys())}")
