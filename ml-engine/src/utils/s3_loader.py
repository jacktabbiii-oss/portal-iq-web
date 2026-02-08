"""S3/R2 Data Loader for ML Engine.

Handles loading data from Cloudflare R2 (S3-compatible) storage.
Falls back to local files during development.
"""

import os
import io
import logging
from pathlib import Path
from typing import Optional, Dict
from functools import lru_cache

import pandas as pd

logger = logging.getLogger(__name__)

# Try to import boto3
try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed - S3/R2 storage disabled")


# =============================================================================
# Configuration
# =============================================================================

def get_s3_config() -> dict:
    """Get S3/R2 configuration from environment."""
    return {
        "endpoint_url": os.getenv("R2_ENDPOINT_URL"),
        "access_key_id": os.getenv("R2_ACCESS_KEY_ID"),
        "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY"),
        "bucket_name": os.getenv("R2_BUCKET_NAME", "portal-iq-data"),
        "region": os.getenv("R2_REGION", "auto"),
    }


def is_s3_configured() -> bool:
    """Check if S3/R2 is properly configured."""
    if not BOTO3_AVAILABLE:
        return False
    config = get_s3_config()
    required = ["endpoint_url", "access_key_id", "secret_access_key"]
    return all(config.get(key) for key in required)


# =============================================================================
# S3 Client
# =============================================================================

class S3DataLoader:
    """Load data from S3/R2 storage."""

    _instance = None
    _client = None
    _data_cache: Dict[str, pd.DataFrame] = {}

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self):
        """Lazy-load S3 client."""
        if self._client is None and BOTO3_AVAILABLE and is_s3_configured():
            try:
                config = get_s3_config()
                self._client = boto3.client(
                    "s3",
                    endpoint_url=config["endpoint_url"],
                    aws_access_key_id=config["access_key_id"],
                    aws_secret_access_key=config["secret_access_key"],
                    region_name=config["region"],
                    config=Config(
                        signature_version="s3v4",
                        retries={"max_attempts": 3, "mode": "adaptive"},
                    ),
                )
                logger.info("S3/R2 client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self._client = None
        return self._client

    @property
    def bucket(self) -> str:
        return get_s3_config()["bucket_name"]

    def read_csv(self, key: str, use_cache: bool = True) -> pd.DataFrame:
        """Read CSV from S3/R2.

        Args:
            key: S3 object key (e.g., "processed/portal_nil_valuations.csv")
            use_cache: Use in-memory cache

        Returns:
            DataFrame
        """
        # Check cache
        if use_cache and key in self._data_cache:
            logger.debug(f"Using cached data for {key}")
            return self._data_cache[key]

        if not self.client:
            logger.debug(f"S3 not available for {key}")
            return pd.DataFrame()

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            df = pd.read_csv(io.BytesIO(response["Body"].read()))
            logger.info(f"Loaded {len(df)} rows from S3: {key}")

            if use_cache:
                self._data_cache[key] = df

            return df

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code in ("404", "NoSuchKey"):
                logger.warning(f"S3 file not found: {key}")
            else:
                logger.error(f"S3 error for {key}: {e}")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to read S3 CSV {key}: {e}")
            return pd.DataFrame()

    def clear_cache(self):
        """Clear the data cache."""
        self._data_cache.clear()
        logger.info("S3 data cache cleared")


# =============================================================================
# Data Loading Functions
# =============================================================================

# Base path for local data files (ml-engine/data)
LOCAL_DATA_BASE = Path(__file__).parent.parent.parent / "data"

# Data path mappings - S3 key and local fallback
DATA_PATHS = {
    # Core data files
    "nil_valuations": {
        "s3_key": "processed/portal_nil_valuations.csv",
        "local": "processed/portal_nil_valuations.csv",
    },
    "nil_rankings": {
        "s3_key": "processed/on3_all_nil_rankings.csv",
        "local": "processed/on3_all_nil_rankings.csv",
    },
    "transfer_portal": {
        "s3_key": "processed/on3_transfer_portal.csv",
        "local": "processed/on3_transfer_portal.csv",
    },
    "transfer_portal_current": {
        "s3_key": "processed/on3_transfer_portal_current.csv",
        "local": "processed/on3_transfer_portal_current.csv",
    },
    "team_portal_rankings": {
        "s3_key": "processed/on3_team_portal_rankings.csv",
        "local": "processed/on3_team_portal_rankings.csv",
    },
    "cfbd_rosters": {
        "s3_key": "processed/cfbd_rosters.csv",
        "local": "processed/cfbd_rosters.csv",
    },
    "cfbd_player_stats": {
        "s3_key": "processed/cfbd_player_stats.csv",
        "local": "processed/cfbd_player_stats.csv",
    },
    "cfbd_sp_ratings": {
        "s3_key": "processed/cfbd_sp_ratings.csv",
        "local": "processed/cfbd_sp_ratings.csv",
    },
    "cfbd_team_talent": {
        "s3_key": "processed/cfbd_team_talent.csv",
        "local": "processed/cfbd_team_talent.csv",
    },
    "espn_rosters": {
        "s3_key": "processed/espn_rosters.csv",
        "local": "processed/espn_rosters.csv",
    },
    "pff_grades": {
        "s3_key": "processed/pff_player_grades.csv",
        "local": "processed/pff_player_grades.csv",
    },
}

# PFF detailed stat categories (82 files in pff/ folder)
PFF_STAT_CATEGORIES = {
    "passing": ["passing_summary", "passing_pressure_blitz", "passing_pressure"],
    "rushing": ["rushing_summary", "elusive_summary", "breakaway_summary"],
    "receiving": ["receiving_summary", "receiving_scheme", "drop_summary", "slot_coverage"],
    "defense": ["defense_summary", "defense_coverage_summary", "defense_coverage_scheme", "run_defense_summary", "run_defense_percentage"],
    "pass_rush": ["pass_rush_summary", "pass_rush_productivity"],
    "blocking": ["offense_blocking", "offense_pass_blocking", "offense_run_blocking", "offense_blocking_efficiency", "line_pass_blocking_efficiency"],
    "special": ["special_teams_summary", "field_goal_summary", "kickoff_summary", "punting_summary", "return_summary"],
}


def get_s3_loader() -> S3DataLoader:
    """Get singleton S3 loader instance."""
    return S3DataLoader()


def load_csv_with_fallback(data_key: str) -> pd.DataFrame:
    """Load CSV from R2/S3, falling back to local file if needed.

    Args:
        data_key: Key from DATA_PATHS (e.g., "nil_valuations")

    Returns:
        DataFrame
    """
    paths = DATA_PATHS.get(data_key)
    if not paths:
        logger.error(f"Unknown data key: {data_key}")
        return pd.DataFrame()

    # Try R2/S3 first
    if is_s3_configured():
        loader = get_s3_loader()
        df = loader.read_csv(paths["s3_key"])
        if not df.empty:
            logger.info(f"Loaded {data_key} from R2: {len(df)} rows")
            return df
        else:
            logger.warning(f"R2 load failed for {data_key}, trying local fallback")

    # Fallback to local file
    local_path = LOCAL_DATA_BASE / paths["local"]
    if local_path.exists():
        try:
            df = pd.read_csv(local_path)
            logger.info(f"Loaded {data_key} from local: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to read {local_path}: {e}")
            return pd.DataFrame()

    logger.warning(f"Data not found in R2 or local: {data_key}")
    return pd.DataFrame()


def load_nil_data() -> pd.DataFrame:
    """Load NIL valuation data.

    Returns:
        DataFrame with columns: name, position, school, nil_value, etc.
    """
    # Try portal NIL valuations first (most comprehensive)
    df = load_csv_with_fallback("nil_valuations")
    if not df.empty:
        return df

    # Fallback to NIL rankings
    df = load_csv_with_fallback("nil_rankings")
    if not df.empty:
        return df

    logger.warning("No NIL data available from any source")
    return pd.DataFrame()


def load_portal_data(current_cycle_only: bool = True) -> pd.DataFrame:
    """Load transfer portal data.

    Args:
        current_cycle_only: If True, load only current 2025-2026 cycle.
                           If False, load all historical data.

    Returns:
        DataFrame with portal player information
    """
    if current_cycle_only:
        df = load_csv_with_fallback("transfer_portal_current")
        if not df.empty:
            return df
        logger.warning("Current portal data not found, falling back to full portal")

    return load_csv_with_fallback("transfer_portal")


def load_pff_grades() -> pd.DataFrame:
    """Load PFF player grades.

    Returns:
        DataFrame with PFF grades
    """
    return load_csv_with_fallback("pff_grades")


def load_rosters() -> pd.DataFrame:
    """Load CFBD roster data.

    Returns:
        DataFrame with roster information
    """
    return load_csv_with_fallback("cfbd_rosters")


def load_pff_stat(category: str, stat_type: str, season: int = 2025) -> pd.DataFrame:
    """Load a specific PFF stat file from S3.

    Args:
        category: Category folder (passing, rushing, receiving, defense, pass_rush, blocking, special)
        stat_type: Stat file name without year prefix (e.g., "passing_summary")
        season: Year to load (2023, 2024, or 2025)

    Returns:
        DataFrame with the stats
    """
    s3_key = f"pff/{category}/{season}_{stat_type}.csv"

    if is_s3_configured():
        loader = get_s3_loader()
        df = loader.read_csv(s3_key)
        if not df.empty:
            df["season"] = season
            logger.info(f"Loaded PFF {category}/{stat_type} ({season}): {len(df)} rows")
            return df

    logger.warning(f"PFF stat not found: {s3_key}")
    return pd.DataFrame()


def load_espn_rosters() -> pd.DataFrame:
    """Load ESPN roster data with headshots."""
    return load_csv_with_fallback("espn_rosters")


def load_cfbd_stats() -> pd.DataFrame:
    """Load CFBD player stats."""
    df = load_csv_with_fallback("cfbd_player_stats")
    if df.empty:
        return df

    # Rename columns to standard format
    column_renames = {
        "passing_YDS": "passing_yards",
        "passing_TD": "passing_tds",
        "passing_INT": "interceptions",
        "passing_ATT": "passing_attempts",
        "passing_COMPLETIONS": "completions",
        "passing_PCT": "completion_pct",
        "rushing_YDS": "rushing_yards",
        "rushing_TD": "rushing_tds",
        "rushing_CAR": "rushing_attempts",
        "rushing_YPC": "yards_per_carry",
        "receiving_YDS": "receiving_yards",
        "receiving_TD": "receiving_tds",
        "receiving_REC": "receptions",
        "receiving_YPR": "yards_per_reception",
        "defensive_TOT": "tackles",
        "defensive_SOLO": "solo_tackles",
        "defensive_TFL": "tackles_for_loss",
        "defensive_SACKS": "sacks",
        "defensive_QB HUR": "qb_hurries",
        "defensive_PD": "passes_defended",
        "interceptions_INT": "interceptions_def",
    }
    df = df.rename(columns=column_renames)
    return df


def merge_headshots(df: pd.DataFrame) -> pd.DataFrame:
    """Merge headshot_url from multiple sources.

    Priority:
        1. on3_transfer_portal.csv (94%+ coverage for portal players)
        2. on3_all_nil_rankings.csv (backup On3 data)
        3. espn_rosters.csv (fills remaining gaps)
    """
    if "name" not in df.columns and "player_name" not in df.columns:
        return df

    name_col = "player_name" if "player_name" in df.columns else "name"

    # Skip if already has headshots
    if "headshot_url" in df.columns and df["headshot_url"].notna().any():
        return df

    # Remove existing empty headshot_url column
    if "headshot_url" in df.columns:
        df = df.drop(columns=["headshot_url"])

    # Collect headshots from multiple sources
    all_headshots = {}

    # Source 1: On3 Transfer Portal
    try:
        portal_df = load_csv_with_fallback("transfer_portal")
        if not portal_df.empty and "headshot_url" in portal_df.columns and "name" in portal_df.columns:
            for _, row in portal_df.iterrows():
                name = row.get("name")
                url = row.get("headshot_url")
                if name and pd.notna(url) and str(url).startswith("http"):
                    all_headshots[name] = url
        logger.info(f"Headshots from portal: {len(all_headshots)}")
    except Exception as e:
        logger.warning(f"Failed to load portal headshots: {e}")

    # Source 2: On3 NIL Rankings
    try:
        nil_df = load_csv_with_fallback("nil_rankings")
        if not nil_df.empty and "headshot_url" in nil_df.columns and "name" in nil_df.columns:
            for _, row in nil_df.iterrows():
                name = row.get("name")
                url = row.get("headshot_url")
                if name and name not in all_headshots and pd.notna(url) and str(url).startswith("http"):
                    all_headshots[name] = url
        logger.info(f"Headshots after NIL: {len(all_headshots)}")
    except Exception as e:
        logger.warning(f"Failed to load NIL headshots: {e}")

    # Source 3: ESPN Rosters
    try:
        espn_df = load_csv_with_fallback("espn_rosters")
        if not espn_df.empty and "headshot_url" in espn_df.columns and "name" in espn_df.columns:
            for _, row in espn_df.iterrows():
                name = row.get("name")
                url = row.get("headshot_url")
                if name and name not in all_headshots and pd.notna(url) and str(url).startswith("http"):
                    all_headshots[name] = url
        logger.info(f"Headshots after ESPN: {len(all_headshots)}")
    except Exception as e:
        logger.warning(f"Failed to load ESPN headshots: {e}")

    # Create headshot lookup DataFrame and merge
    if all_headshots:
        headshot_df = pd.DataFrame([
            {"_name": name, "headshot_url": url}
            for name, url in all_headshots.items()
        ])
        df = df.merge(headshot_df, left_on=name_col, right_on="_name", how="left")
        if "_name" in df.columns:
            df = df.drop(columns=["_name"])

    return df


def merge_measurables(df: pd.DataFrame) -> pd.DataFrame:
    """Merge height/weight from CFBD rosters and ESPN rosters."""
    if "name" not in df.columns and "player_name" not in df.columns:
        return df

    name_col = "player_name" if "player_name" in df.columns else "name"

    # Skip if already has measurables
    if "height" in df.columns and "weight" in df.columns:
        if df["height"].notna().any() and df["weight"].notna().any():
            return df

    all_measurables = {}

    # Source 1: CFBD Rosters
    try:
        cfbd_df = load_csv_with_fallback("cfbd_rosters")
        if not cfbd_df.empty:
            cfbd_name_col = "player_name" if "player_name" in cfbd_df.columns else "name" if "name" in cfbd_df.columns else None
            if cfbd_name_col and "height" in cfbd_df.columns and "weight" in cfbd_df.columns:
                cfbd_df = cfbd_df.drop_duplicates(subset=[cfbd_name_col], keep="first")
                for _, row in cfbd_df.iterrows():
                    name = row.get(cfbd_name_col)
                    height = row.get("height")
                    weight = row.get("weight")
                    if name and pd.notna(height) and pd.notna(weight):
                        try:
                            all_measurables[name] = {"height": float(height), "weight": float(weight)}
                        except (ValueError, TypeError):
                            pass
        logger.info(f"Measurables from CFBD: {len(all_measurables)}")
    except Exception as e:
        logger.warning(f"Failed to load CFBD measurables: {e}")

    # Source 2: ESPN Rosters
    try:
        espn_df = load_csv_with_fallback("espn_rosters")
        if not espn_df.empty and "name" in espn_df.columns:
            for _, row in espn_df.iterrows():
                name = row.get("name")
                if name and name not in all_measurables:
                    height = row.get("height")
                    weight = row.get("weight")
                    # ESPN height is like "6' 2\"" - convert to inches
                    if pd.notna(height) and isinstance(height, str) and "'" in height:
                        try:
                            parts = height.replace('"', '').split("'")
                            feet = int(parts[0].strip())
                            inches = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                            height = feet * 12 + inches
                        except (ValueError, IndexError):
                            height = None
                    if pd.notna(height) and pd.notna(weight):
                        all_measurables[name] = {"height": height, "weight": weight}
        logger.info(f"Measurables after ESPN: {len(all_measurables)}")
    except Exception as e:
        logger.warning(f"Failed to load ESPN measurables: {e}")

    # Merge measurables
    if all_measurables:
        measurables_df = pd.DataFrame([
            {"_name": name, "height": data["height"], "weight": data["weight"]}
            for name, data in all_measurables.items()
        ])
        df = df.merge(measurables_df, left_on=name_col, right_on="_name", how="left", suffixes=("", "_meas"))
        if "_name" in df.columns:
            df = df.drop(columns=["_name"])
        # Use merged values if original was empty
        if "height_meas" in df.columns:
            if "height" not in df.columns:
                df["height"] = df["height_meas"]
            else:
                df["height"] = df["height"].fillna(df["height_meas"])
            df = df.drop(columns=["height_meas"])
        if "weight_meas" in df.columns:
            if "weight" not in df.columns:
                df["weight"] = df["weight_meas"]
            else:
                df["weight"] = df["weight"].fillna(df["weight_meas"])
            df = df.drop(columns=["weight_meas"])

    return df


def merge_pff_grades(df: pd.DataFrame, season: int = 2025) -> pd.DataFrame:
    """Merge PFF grades into player DataFrame.

    Includes 170+ columns covering all position-specific metrics:
    - QB: accuracy, pressure handling, big-time throws
    - RB: elusive rating, breakaway, yards after contact
    - WR/TE: yards per route, drops, contested catches
    - OL: pass block efficiency, pressures allowed
    - DL/EDGE: pass rush productivity, win rate, stops
    - LB/DB: coverage grade, passer rating allowed
    """
    if "name" not in df.columns and "player_name" not in df.columns:
        return df

    name_col = "player_name" if "player_name" in df.columns else "name"

    pff_df = load_pff_grades()
    if pff_df.empty:
        return df

    # Standardize name column in PFF data
    if "player_name" in pff_df.columns and "name" not in pff_df.columns:
        pff_df = pff_df.rename(columns={"player_name": "name"})

    pff_name_col = "name" if "name" in pff_df.columns else None
    if not pff_name_col:
        return df

    # Select ALL relevant PFF columns - comprehensive metrics for elite valuations
    pff_cols = [
        # ===========================================
        # IDENTITY & CORE
        # ===========================================
        pff_name_col, "pff_id", "team", "position", "season", "games_played",
        "pff_overall", "pff_offense", "pff_defense",

        # ===========================================
        # QUARTERBACK - Complete Arsenal
        # ===========================================
        "pff_passing",
        # Accuracy & efficiency
        "adjusted_completion_pct", "completion_pct", "passer_rating",
        "avg_depth_of_target", "avg_time_to_throw",
        # Playmaking
        "big_time_throws", "big_time_throw_pct",
        # Decision making (negatives)
        "turnover_worthy_plays", "turnover_worthy_play_pct",
        # Under pressure performance
        "pressure_completion_percent", "pressure_qb_rating", "pressure_yards",
        "pressure_big_time_throws", "pressure_btt_rate",
        "pressure_turnover_worthy_plays", "pressure_twp_rate",
        "pressure_sack_percent", "pressure_dropbacks",
        # Clean pocket performance
        "no_pressure_completion_percent", "no_pressure_qb_rating",
        "no_pressure_big_time_throws", "no_pressure_btt_rate",
        "no_pressure_turnover_worthy_plays", "no_pressure_twp_rate",
        # Blitz handling
        "blitz_completion_percent", "blitz_qb_rating", "blitz_big_time_throws",
        "blitz_turnover_worthy_plays", "blitz_twp_rate", "blitz_sack_percent",
        # Raw stats
        "attempts", "completions", "yards", "touchdowns", "dropbacks",
        "sacks", "scrambles", "scramble_yards", "hit_as_threw",

        # ===========================================
        # RUNNING BACK - Complete Arsenal
        # ===========================================
        "pff_rushing", "pff_receiving",
        # Elusiveness & contact
        "elusive_rating", "yards_after_contact", "yaco_per_attempt",
        "missed_tackles_forced", "elu_rush_mtf", "elu_recv_mtf",
        # Explosiveness
        "breakaway_pct", "breakaway_yards", "breakaway_attempts", "explosive",
        # Efficiency
        "ypa", "first_downs", "run_plays",
        # Ball security
        "fumbles", "grades_hands_fumble",
        # Pass game contribution
        "receptions", "rec_yards", "targets", "routes_run",
        "yards_after_catch", "catch_rate",

        # ===========================================
        # WIDE RECEIVER / TIGHT END - Complete Arsenal
        # ===========================================
        # Route running
        "yards_per_route_run", "route_rate",
        # Hands
        "drops", "drop_rate", "grades_hands_drop",
        # Contested catches
        "contested_catch_rate", "contested_receptions", "contested_targets",
        # YAC ability
        "yards_after_catch_per_reception",
        # Alignment splits
        "slot_rate", "slot_snaps", "wide_rate", "wide_snaps",
        "inline_rate", "inline_snaps",
        # Man vs Zone performance
        "man_yards", "man_yards_per_reception", "man_yprr", "man_catch_rate",
        "man_contested_catch_rate", "man_touchdowns",
        "zone_yards", "zone_yards_per_reception", "zone_yprr", "zone_catch_rate",
        "zone_contested_catch_rate", "zone_touchdowns",
        # QB rating when targeted
        "targeted_qb_rating",

        # ===========================================
        # OFFENSIVE LINE - Complete Arsenal
        # ===========================================
        "pff_pass_block", "pff_run_block",
        # Pass protection efficiency
        "pass_blocking_efficiency", "pass_block_percent",
        "pressures_allowed", "sacks_allowed", "hurries_allowed", "hits_allowed",
        # True pass sets (dropback protection)
        "true_pass_set_pbe", "true_pass_set_pressures_allowed",
        "true_pass_set_sacks_allowed", "true_pass_set_hurries_allowed",
        # Run blocking
        "run_block_percent",
        "gap_grades_run_block", "gap_run_block_percent",
        "zone_grades_run_block", "zone_run_block_percent",
        # Snap counts by position
        "snap_counts_lt", "snap_counts_lg", "snap_counts_ce",
        "snap_counts_rg", "snap_counts_rt", "snap_counts_te",
        "snap_counts_pass_block", "snap_counts_run_block",
        "offensive_snaps",
        # Penalties
        "penalties", "grades_offense_penalty",

        # ===========================================
        # EDGE RUSHER / INTERIOR DL - Complete Arsenal
        # ===========================================
        "pff_pass_rush", "pff_run_defense",
        # Pass rush production
        "pass_rushing_productivity", "pass_rush_win_rate", "pass_rush_wins",
        "pressures", "hits", "hurries", "batted_passes",
        "pass_rush_snaps", "pass_rush_percent",
        # True pass rush (not play action)
        "true_pass_set_prp", "true_pass_set_pass_rush_win_rate",
        "true_pass_set_total_pressures", "true_pass_set_sacks",
        # Run defense
        "stops", "run_stop_opp", "stop_percent",
        "tackles", "tackles_for_loss", "assists",
        # Alignment splits
        "snap_counts_dl", "snap_counts_dl_a_gap", "snap_counts_dl_b_gap",
        "snap_counts_dl_outside_t", "snap_counts_dl_over_t",
        # Left vs Right production
        "lhs_pressures", "lhs_sacks", "lhs_prp",
        "rhs_pressures", "rhs_sacks", "rhs_prp",
        "defensive_snaps",

        # ===========================================
        # LINEBACKER - Complete Arsenal
        # ===========================================
        "pff_tackling", "pff_coverage",
        # Run defense
        "snap_counts_run_defense", "snap_counts_box",
        # Coverage
        "snap_counts_coverage", "coverage_snaps",
        "passer_rating_allowed", "yards_per_coverage_snap",
        "forced_incompletes", "forced_incompletion_rate",
        "coverage_snaps_per_target", "coverage_snaps_per_reception",
        # Tackling reliability
        "missed_tackles", "missed_tackle_rate", "avg_depth_of_tackle",

        # ===========================================
        # CORNERBACK / SAFETY - Complete Arsenal
        # ===========================================
        # Coverage grades
        "man_grades_coverage_defense", "zone_grades_coverage_defense",
        # Man coverage performance
        "man_qb_rating_against", "man_yards_per_coverage_snap",
        "man_forced_incompletes", "man_forced_incompletion_rate",
        "man_coverage_snaps_per_target", "man_pass_break_ups",
        "man_snap_counts_coverage", "man_coverage_percent",
        # Zone coverage performance
        "zone_qb_rating_against", "zone_yards_per_coverage_snap",
        "zone_forced_incompletes", "zone_forced_incompletion_rate",
        "zone_coverage_snaps_per_target", "zone_pass_break_ups",
        "zone_snap_counts_coverage", "zone_coverage_percent",
        # Alignment
        "snap_counts_slot", "snap_counts_corner", "snap_counts_fs",
        # Ball skills
        "ints", "pbus", "dropped_ints", "interception_touchdowns",
        # Tackling
        "man_missed_tackles", "man_missed_tackle_rate",
        "zone_missed_tackles", "zone_missed_tackle_rate",
        # Turnovers forced
        "forced_fumbles", "fumble_recoveries",

        # ===========================================
        # SPECIAL TEAMS
        # ===========================================
        "grades_punt_return", "grades_kick_return", "grades_return",
        "punt_yards", "punt_touchdowns", "kickoff_yards", "kickoff_touchdowns",

        # ===========================================
        # KICKER / PUNTER
        # ===========================================
        "grades_fgep_kicker", "grades_punter", "grades_kickoff_kicker",
        "total_made", "total_percent", "pat_percent",
        "fifty_percent", "forty_percent", "thirty_percent",
        "average_hangtime", "average_net_yards", "inside_twenties",
    ]

    # Only keep columns that exist
    available_cols = [c for c in pff_cols if c in pff_df.columns]
    pff_subset = pff_df[available_cols].copy()

    # Drop duplicates by name (keep highest overall grade)
    if "pff_overall" in pff_subset.columns:
        pff_subset = pff_subset.sort_values("pff_overall", ascending=False)
    pff_subset = pff_subset.drop_duplicates(subset=[pff_name_col], keep="first")

    # Merge on player name - LEFT join preserves all existing data
    df = df.merge(pff_subset, left_on=name_col, right_on=pff_name_col, how="left", suffixes=("", "_pff"))

    # Clean up duplicate name column
    if f"{pff_name_col}_pff" in df.columns:
        df = df.drop(columns=[f"{pff_name_col}_pff"])

    return df


def merge_cfbd_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Merge CFBD player stats into DataFrame."""
    if "name" not in df.columns and "player_name" not in df.columns:
        return df

    name_col = "player_name" if "player_name" in df.columns else "name"

    stats_df = load_cfbd_stats()
    if stats_df.empty:
        return df

    stats_name_col = "player_name" if "player_name" in stats_df.columns else "name" if "name" in stats_df.columns else None
    if not stats_name_col:
        return df

    # Get most recent season for each player
    if "season" in stats_df.columns:
        stats_df = stats_df.sort_values("season", ascending=False)
        stats_df = stats_df.drop_duplicates(subset=[stats_name_col], keep="first")

    # Select key stat columns
    stat_cols = [
        stats_name_col,
        "passing_yards", "passing_tds", "interceptions", "completion_pct",
        "rushing_yards", "rushing_tds", "yards_per_carry",
        "receiving_yards", "receiving_tds", "receptions",
        "tackles", "solo_tackles", "tackles_for_loss", "sacks", "passes_defended",
    ]

    available_cols = [c for c in stat_cols if c in stats_df.columns]
    if len(available_cols) <= 1:
        return df

    stats_subset = stats_df[available_cols].copy()

    # Merge
    df = df.merge(stats_subset, left_on=name_col, right_on=stats_name_col, how="left", suffixes=("", "_stats"))

    # Clean up
    if f"{stats_name_col}_stats" in df.columns:
        df = df.drop(columns=[f"{stats_name_col}_stats"])

    return df


def load_nil_data_enriched() -> pd.DataFrame:
    """Load NIL data with headshots, measurables, PFF grades, and CFBD stats merged.

    This is the full-featured version matching Streamlit's data loading.
    """
    df = load_nil_data()
    if df.empty:
        return df

    logger.info(f"Enriching NIL data: {len(df)} rows")

    # Standardize column names
    if "nil_value_predicted" in df.columns:
        df = df.rename(columns={"nil_value_predicted": "nil_value"})
    if "recruiting_stars" in df.columns and "stars" not in df.columns:
        df = df.rename(columns={"recruiting_stars": "stars"})

    # Merge all enrichments
    df = merge_headshots(df)
    df = merge_measurables(df)
    df = merge_pff_grades(df)
    df = merge_cfbd_stats(df)

    logger.info(f"NIL data enriched: {len(df)} rows, {len(df.columns)} columns")
    return df


def load_portal_data_enriched() -> pd.DataFrame:
    """Load portal data with headshots, measurables, PFF grades, and CFBD stats merged.

    This is the full-featured version matching Streamlit's data loading.
    """
    df = load_portal_data()
    if df.empty:
        return df

    logger.info(f"Enriching portal data: {len(df)} rows")

    # Standardize column names
    df = df.rename(columns={
        "nil_valuation": "nil_value",
        "from_school": "origin_school",
        "to_school": "destination_school",
        "rating": "overall_rating",
    })

    # Merge all enrichments
    df = merge_headshots(df)
    df = merge_measurables(df)
    df = merge_pff_grades(df)
    df = merge_cfbd_stats(df)

    logger.info(f"Portal data enriched: {len(df)} rows, {len(df.columns)} columns")
    return df


def get_s3_diagnostics() -> dict:
    """Get S3 connection diagnostics for debugging."""
    config = get_s3_config()

    result = {
        "boto3_available": BOTO3_AVAILABLE,
        "s3_configured": is_s3_configured(),
        "local_data_base": str(LOCAL_DATA_BASE),
        "local_data_exists": LOCAL_DATA_BASE.exists(),
        "config": {
            "endpoint_url": config["endpoint_url"][:50] + "..." if config["endpoint_url"] else None,
            "bucket_name": config["bucket_name"],
            "access_key_set": bool(config["access_key_id"]),
            "secret_key_set": bool(config["secret_access_key"]),
        },
        "s3_files": [],
        "local_files": [],
        "error": None,
    }

    # Check local files first
    for name, paths in DATA_PATHS.items():
        local_path = LOCAL_DATA_BASE / paths["local"]
        if local_path.exists():
            try:
                size = local_path.stat().st_size
                result["local_files"].append(f"✓ {name}: {size / 1024:.1f} KB")
            except Exception:
                result["local_files"].append(f"? {name}: exists but can't read size")
        else:
            result["local_files"].append(f"✗ {name}: not found at {local_path}")

    # Check S3
    if not BOTO3_AVAILABLE:
        result["error"] = "boto3 not installed - using local files only"
        return result

    if not is_s3_configured():
        result["error"] = "S3 not configured - using local files only"
        return result

    loader = get_s3_loader()

    if not loader.client:
        result["error"] = "Failed to create S3 client - using local files only"
        return result

    # Try to list S3 files
    try:
        response = loader.client.list_objects_v2(
            Bucket=loader.bucket,
            Prefix="processed/",
            MaxKeys=20
        )
        files = [obj["Key"] for obj in response.get("Contents", [])]
        result["s3_files"] = files
        result["s3_total_files"] = response.get("KeyCount", 0)
    except Exception as e:
        result["error"] = f"S3 list failed: {str(e)[:100]}"

    return result
