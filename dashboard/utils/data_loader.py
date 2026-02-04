"""Data loading utilities for Portal IQ Dashboard.

Loads real data from On3 scraped files and CFBD stats.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

# Data directory paths - try multiple possible locations
def _find_data_dir():
    """Find the data directory, trying multiple paths."""
    possible_roots = [
        Path(__file__).parent.parent.parent / "ml-engine",  # dashboard/utils/ -> ml-engine/
        Path(__file__).parent.parent.parent.parent / "ml-engine",  # one more level up
        Path.cwd() / "ml-engine",  # from current working directory
        Path.cwd().parent / "ml-engine",  # one up from cwd
        Path("/app/ml-engine"),  # Railway/Docker common path
    ]

    for root in possible_roots:
        data_path = root / "data" / "processed"
        if data_path.exists() and (data_path / "portal_nil_valuations.csv").exists():
            return root, data_path

    # Fallback to original
    root = Path(__file__).parent.parent.parent / "ml-engine"
    return root, root / "data" / "processed"

PROJECT_ROOT, DATA_DIR = _find_data_dir()
RAW_DIR = PROJECT_ROOT / "data" / "raw"


def _get_data_path(filename: str) -> Path:
    """Get full path to data file."""
    return DATA_DIR / filename


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_database_stats() -> Dict[str, Any]:
    """Get real database statistics from loaded data.

    Returns:
        Dict with database stats
    """
    stats = {
        "total_players": 0,
        "portal_players": 0,
        "new_portal_today": 0,
        "nil_valuations": 0,
        "schools": 0,
        "models_updated": "Feb 3, 2026",
        "last_updated": datetime.now().strftime("%b %d, %Y %H:%M"),
        "data_version": "3.1.0",
    }

    # Load NIL valuations (proprietary model predictions + actual values)
    valuations_path = _get_data_path("portal_nil_valuations.csv")
    if valuations_path.exists():
        df = pd.read_csv(valuations_path)
        stats["nil_valuations"] = len(df)
        stats["total_players"] = len(df["name"].unique())
        # Count actual vs predicted
        actual_count = (~df["is_predicted"]).sum() if "is_predicted" in df.columns else 0
        stats["actual_nil_values"] = int(actual_count)
        stats["predicted_nil_values"] = len(df) - int(actual_count)
    else:
        # Fallback to On3 NIL rankings
        nil_path = _get_data_path("on3_all_nil_rankings.csv")
        if nil_path.exists():
            df = pd.read_csv(nil_path)
            stats["nil_valuations"] = len(df)
            stats["total_players"] = len(df["name"].unique())

    # Load portal data
    portal_path = _get_data_path("on3_transfer_portal.csv")
    if portal_path.exists():
        df = pd.read_csv(portal_path)
        stats["portal_players"] = len(df)
        # Count entries in last 24 hours (approximate)
        if "commit_date" in df.columns:
            today = datetime.now().strftime("%Y-%m-%d")
            stats["new_portal_today"] = len(df[df["commit_date"].str.startswith(today, na=False)])

    # Count unique schools
    team_path = _get_data_path("on3_team_portal_rankings.csv")
    if team_path.exists():
        df = pd.read_csv(team_path)
        stats["schools"] = len(df["team"].unique())

    return stats


@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_sample_data(data_type: str) -> pd.DataFrame:
    """Load real data for dashboard.

    Args:
        data_type: Type of data to load

    Returns:
        DataFrame with data
    """
    if data_type == "players":
        return get_nil_players()
    elif data_type == "portal_players":
        return get_portal_players()
    elif data_type == "schools":
        return get_team_rankings()
    else:
        return pd.DataFrame()


@st.cache_data(ttl=600)
def get_nil_players() -> pd.DataFrame:
    """Get NIL player data with proprietary valuations AND performance stats."""
    # Try proprietary valuations first
    valuations_path = _get_data_path("portal_nil_valuations.csv")

    if valuations_path.exists():
        df = pd.read_csv(valuations_path)

        # Standardize column names for compatibility
        df = df.rename(columns={
            "nil_value_predicted": "nil_value",
            "recruiting_stars": "stars",
            "nil_tier": "tier",
        })

        # Add overall_rating based on stars
        df["overall_rating"] = df["stars"] / 5

        # Add source indicator
        df["valuation_source"] = df["is_predicted"].apply(
            lambda x: "Predicted" if x else "On3 Actual"
        )
    else:
        # Fallback to On3 NIL rankings
        nil_path = _get_data_path("on3_all_nil_rankings.csv")

        if not nil_path.exists():
            st.warning("NIL data not found. Run the valuation model first.")
            return pd.DataFrame()

        df = pd.read_csv(nil_path)

        # Standardize column names
        df = df.rename(columns={
            "nil_valuation": "nil_value",
            "recruiting_stars": "stars",
            "recruiting_rating": "overall_rating",
        })

        # Add tier based on value
        def get_tier(value):
            if pd.isna(value) or value == 0:
                return "unknown"
            if value >= 1000000:
                return "mega"
            if value >= 500000:
                return "premium"
            if value >= 200000:
                return "established"
            if value >= 50000:
                return "emerging"
            return "developing"

        df["tier"] = df["nil_value"].apply(get_tier)

        # Normalize rating to 0-1 scale if needed
        if "overall_rating" in df.columns:
            max_rating = df["overall_rating"].max()
            if max_rating > 1:
                df["overall_rating"] = df["overall_rating"] / 100

        df["valuation_source"] = "On3 Actual"

    # MERGE WITH CFBD STATS - Critical for accurate valuations
    try:
        stats_df = get_cfbd_player_stats()
        if not stats_df.empty and "name" in df.columns:
            # Get most recent season stats
            if "season" in stats_df.columns:
                stats_df = stats_df.sort_values("season", ascending=False)
                stats_df = stats_df.drop_duplicates(subset=["player_name"], keep="first")

            # Merge on name
            df = df.merge(
                stats_df,
                left_on="name",
                right_on="player_name",
                how="left",
                suffixes=("", "_stats")
            )
    except Exception:
        pass  # Continue without stats if merge fails

    # MERGE WITH MANUAL/PFF STATS (metrics that can't be auto-pulled)
    try:
        manual_stats = get_manual_player_stats()
        if not manual_stats.empty and "name" in df.columns:
            df = df.merge(
                manual_stats,
                left_on="name",
                right_on="player_name",
                how="left",
                suffixes=("", "_pff")
            )
    except Exception:
        pass  # Continue without manual stats if merge fails

    return df


def get_manual_player_stats() -> pd.DataFrame:
    """Load manually entered stats (PFF grades, pressures, etc.)."""
    manual_path = DATA_DIR / "manual_player_stats.csv"

    if not manual_path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(manual_path)
        return df
    except Exception:
        return pd.DataFrame()


def get_pff_grades(season: int = None, most_recent: bool = True) -> pd.DataFrame:
    """Load PFF player grades from merged data.

    Args:
        season: Optional filter for specific season (2023, 2024, 2025)
        most_recent: If True and no season specified, get most recent season per player

    Returns:
        DataFrame with PFF grades
    """
    pff_path = DATA_DIR / "pff_player_grades.csv"

    if not pff_path.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(pff_path)

        # Standardize column names for merging
        if "player_name" in df.columns:
            df = df.rename(columns={"player_name": "name"})

        # Filter by season if specified
        if season and "season" in df.columns:
            df = df[df["season"] == season]
        elif most_recent and "season" in df.columns:
            # Get most recent season per player
            df = df.sort_values("season", ascending=False)
            df = df.drop_duplicates(subset=["pff_id"], keep="first")

        return df
    except Exception:
        return pd.DataFrame()


def merge_pff_grades(df: pd.DataFrame, season: int = 2025) -> pd.DataFrame:
    """Merge PFF grades into player DataFrame.

    Args:
        df: DataFrame with player data (must have 'name' column)
        season: Season to use for PFF grades (default: 2025)

    Returns:
        DataFrame with PFF grades merged in
    """
    pff_df = get_pff_grades(season=season, most_recent=True)
    if pff_df.empty:
        return df

    # Select relevant PFF columns - including all advanced metrics from merged file
    pff_cols = [
        # Identity
        "name", "pff_id", "team", "position", "season", "games_played",
        # Core grades
        "pff_overall", "pff_offense", "pff_defense",
        # OL grades
        "pff_pass_block", "pff_run_block", "pass_blocking_efficiency",
        "pressures_allowed", "sacks_allowed", "hurries_allowed", "hits_allowed",
        # Skill position grades
        "pff_receiving", "pff_rushing", "pff_passing",
        # Defensive grades
        "pff_pass_rush", "pff_run_defense", "pff_coverage", "pff_tackling",
        "pff_slot_coverage", "pff_zone_coverage", "pff_man_coverage",
        # QB advanced
        "adjusted_completion_pct", "big_time_throws", "big_time_throw_pct",
        "turnover_worthy_plays", "turnover_worthy_play_pct",
        "pff_under_pressure", "pff_clean_pocket", "pff_deep_passing",
        "completion_pct", "passer_rating", "avg_depth_of_target", "time_to_throw",
        # RB advanced
        "elusive_rating", "yards_after_contact", "yaco_per_attempt",
        "missed_tackles_forced", "breakaway_pct", "breakaway_yards",
        # WR/TE advanced
        "yards_per_route_run", "drop_rate", "drops",
        "contested_catch_rate", "contested_catches", "yards_after_catch",
        "routes_run", "catch_rate", "yac_per_reception",
        # Pass rush advanced
        "pass_rushing_productivity", "pressure_rate", "pass_rush_win_rate",
        "pressures", "hurries", "hits", "sacks", "batted_passes",
        # Run defense advanced
        "run_stop_pct", "run_stops", "tackles", "tackles_for_loss",
        # Coverage advanced
        "passer_rating_allowed", "yards_per_coverage_snap",
        "targets_allowed", "completions_allowed", "yards_allowed", "tds_allowed",
        "forced_incompletes", "forced_incompletion_rate",
        # Snap counts
        "defensive_snaps", "offensive_snaps", "coverage_snaps", "pass_rush_snaps",
        # Tackling
        "missed_tackles", "missed_tackle_pct",
        # Turnovers
        "ints", "pbus", "forced_fumbles",
    ]

    # Only keep columns that exist
    available_cols = [c for c in pff_cols if c in pff_df.columns]
    pff_subset = pff_df[available_cols].copy()

    # Drop duplicates by name (keep highest overall grade)
    if "pff_overall" in pff_subset.columns:
        pff_subset = pff_subset.sort_values("pff_overall", ascending=False)
    pff_subset = pff_subset.drop_duplicates(subset=["name"], keep="first")

    # Merge on player name - LEFT join preserves all existing data
    if "name" in df.columns:
        df = df.merge(pff_subset, on="name", how="left", suffixes=("", "_pff"))

    return df


@st.cache_data(ttl=600)
def get_portal_players(year: int = 2026, status: str = None, enrich_nil: bool = True, include_all_valuations: bool = False) -> pd.DataFrame:
    """Get transfer portal player data from On3 with NIL estimates.

    Args:
        year: Filter by year (2024, 2025, 2026)
        status: Filter by status (Committed, Entered, etc.)
        enrich_nil: Whether to add Portal IQ NIL estimates
        include_all_valuations: If True, include all players from valuations file (17,500+)

    Returns:
        DataFrame with portal players and NIL estimates
    """
    portal_path = _get_data_path("on3_transfer_portal.csv")
    valuations_path = _get_data_path("portal_nil_valuations.csv")

    if not portal_path.exists():
        st.warning("Portal data not found. Run the On3 scraper first.")
        return pd.DataFrame()

    df = pd.read_csv(portal_path)

    # DEDUPLICATE: Remove duplicate players (keep first occurrence, prioritize committed)
    # Sort so committed players come first, then by name
    if "status" in df.columns:
        status_order = {"Committed": 0, "Entered": 1, "Withdrawn": 2, "Expected": 3}
        df["_status_order"] = df["status"].map(status_order).fillna(99)
        df = df.sort_values(["_status_order", "name"])
        df = df.drop(columns=["_status_order"])

    # Remove exact duplicates (same name + same origin school)
    if "name" in df.columns and "from_school" in df.columns:
        df = df.drop_duplicates(subset=["name", "from_school"], keep="first")
    elif "name" in df.columns:
        # Fallback: just dedupe by name
        df = df.drop_duplicates(subset=["name"], keep="first")

    # Keep original On3 valuation before renaming
    df["on3_nil_value"] = df["nil_valuation"].copy()

    # Standardize column names
    df = df.rename(columns={
        "nil_valuation": "nil_value",
        "from_school": "origin_school",
        "to_school": "destination_school",
        "rating": "overall_rating",
    })

    # Mark stars from On3 transfer portal as portal ratings (based on college performance)
    # These are different from HS recruiting stars
    if "stars" in df.columns:
        df["transfer_stars"] = df["stars"]  # Preserve as explicit transfer portal stars
        df["star_source"] = "portal"  # Mark source for calculations

    # Extract year from source column (e.g., "portal_industry_football_2025" -> 2025)
    if "source" in df.columns:
        df["portal_year"] = df["source"].str.extract(r"(\d{4})")[0].fillna("2026").astype(int)

    # Filter by year if specified
    if year and "portal_year" in df.columns:
        df = df[df["portal_year"] == year]

    # Filter by status if specified
    if status and "status" in df.columns:
        df = df[df["status"] == status]

    # Normalize rating
    if "overall_rating" in df.columns:
        max_rating = df["overall_rating"].max()
        if pd.notna(max_rating) and max_rating > 1:
            df["overall_rating"] = df["overall_rating"] / 100

    # Enrich with Portal IQ NIL estimates
    if enrich_nil and not df.empty:
        try:
            from utils.nil_estimator import enrich_portal_data

            # Load existing valuations for lookup
            valuations_df = pd.read_csv(valuations_path) if valuations_path.exists() else None

            df = enrich_portal_data(df, valuations_df)

            # Optionally merge in players from valuations that aren't in portal
            if include_all_valuations and valuations_df is not None:
                df = _merge_valuations_players(df, valuations_df)

        except Exception as e:
            # Fallback: generate basic estimates
            df["portaliq_value"] = df.apply(
                lambda r: _basic_nil_estimate(r.get("position"), r.get("stars"), r.get("destination_school")),
                axis=1
            )
            df["confidence"] = "low"
            df["is_predicted"] = True

    # Merge PFF grades if available
    try:
        df = merge_pff_grades(df)
    except Exception:
        pass  # Continue without PFF grades if merge fails

    return df


def _merge_valuations_players(portal_df: pd.DataFrame, valuations_df: pd.DataFrame) -> pd.DataFrame:
    """Merge players from valuations file that aren't in portal data.

    This adds the ~3,000 additional players who have NIL valuations but
    aren't in the current portal file.
    """
    if valuations_df is None or valuations_df.empty:
        return portal_df

    # Get names already in portal
    portal_names = set(portal_df["name"].str.lower().str.strip())

    # Find players in valuations not in portal
    valuations_df = valuations_df.copy()
    valuations_df["name_lower"] = valuations_df["name"].str.lower().str.strip()
    new_players = valuations_df[~valuations_df["name_lower"].isin(portal_names)].copy()

    if new_players.empty:
        return portal_df

    # Standardize columns to match portal format
    new_players = new_players.rename(columns={
        "nil_value_predicted": "portaliq_value",
        "recruiting_stars": "stars",
        "nil_tier": "nil_tier",
    })

    # Add missing columns with defaults
    new_players["on3_nil_value"] = 0
    new_players["status"] = "Valuation Only"
    new_players["portal_year"] = 2026
    new_players["headshot_url"] = None
    new_players["overall_rating"] = new_players["stars"] / 5 if "stars" in new_players.columns else 0.6
    new_players["value_low"] = new_players["portaliq_value"] * 0.6
    new_players["value_high"] = new_players["portaliq_value"] * 1.4
    new_players["is_predicted"] = new_players.get("is_predicted", True)

    # Keep only columns that exist in portal_df
    common_cols = [c for c in portal_df.columns if c in new_players.columns]
    new_players = new_players[common_cols]

    # Combine
    combined = pd.concat([portal_df, new_players], ignore_index=True)

    return combined


def get_effective_stars(player: dict) -> Tuple[float, str]:
    """Get the most relevant star rating for a player.

    Transfer portal stars (based on college performance) take precedence over
    high school recruiting stars, as they better reflect actual ability.

    Args:
        player: Player dict with star ratings

    Returns:
        Tuple of (stars, source) where source is "portal" or "recruiting"
    """
    # Check for transfer portal rating first (more relevant for portal players)
    transfer_stars = player.get("transfer_stars") or player.get("portal_stars")
    if transfer_stars and not pd.isna(transfer_stars) and transfer_stars > 0:
        return float(transfer_stars), "portal"

    # Fall back to main stars field (could be portal or recruiting depending on source)
    stars = player.get("stars")
    if stars and not pd.isna(stars) and stars > 0:
        # Check if this is from transfer portal data vs recruiting
        source = player.get("star_source", "unknown")
        if source == "portal":
            return float(stars), "portal"
        return float(stars), "recruiting"

    # Finally check HS recruiting stars
    hs_stars = player.get("hs_stars") or player.get("recruiting_stars")
    if hs_stars and not pd.isna(hs_stars) and hs_stars > 0:
        return float(hs_stars), "recruiting"

    # Default to 3 stars (average)
    return 3.0, "default"


def _basic_nil_estimate(position: str, stars: float, school: str) -> float:
    """Basic NIL estimate fallback if estimator fails."""
    base = 50000

    # Position multiplier
    pos_mult = {"QB": 2.5, "WR": 1.5, "RB": 1.2, "EDGE": 1.4, "CB": 1.3}.get(str(position).upper(), 1.0)

    # Star multiplier
    if stars and not pd.isna(stars):
        star_mult = {5: 3.0, 4: 1.8, 3: 1.0, 2: 0.5}.get(int(stars), 1.0)
    else:
        star_mult = 0.8

    # School boost for known programs
    school_mult = 1.0
    if school:
        school_lower = str(school).lower()
        if any(s in school_lower for s in ["alabama", "ohio state", "georgia", "texas", "michigan"]):
            school_mult = 2.0
        elif any(s in school_lower for s in ["lsu", "usc", "oregon", "oklahoma", "florida"]):
            school_mult = 1.5

    return round(base * pos_mult * star_mult * school_mult, 2)


@st.cache_data(ttl=600)
def get_team_rankings(year: int = 2026) -> pd.DataFrame:
    """Get team portal rankings from On3.

    Args:
        year: Filter by year
    """
    team_path = _get_data_path("on3_team_portal_rankings.csv")

    if not team_path.exists():
        st.warning("Team rankings not found. Run the On3 scraper first.")
        return pd.DataFrame()

    df = pd.read_csv(team_path)

    # Filter by year if specified
    if year and "year" in df.columns:
        df = df[df["year"] == year]

    # Standardize column names
    df = df.rename(columns={
        "team": "name",
        "team_full": "full_name",
    })

    return df


@st.cache_data(ttl=600)
def get_roster_for_school(school: str) -> pd.DataFrame:
    """Get portal players going to a specific school.

    Args:
        school: School name

    Returns:
        DataFrame with incoming/outgoing portal players
    """
    df = get_portal_players()

    if df.empty:
        return pd.DataFrame()

    # Get players coming to this school
    incoming = df[df["destination_school"].str.contains(school, case=False, na=False)].copy()
    incoming["direction"] = "incoming"

    # Get players leaving this school
    outgoing = df[df["origin_school"].str.contains(school, case=False, na=False)].copy()
    outgoing["direction"] = "outgoing"

    return pd.concat([incoming, outgoing], ignore_index=True)


def search_players(query: str, data_type: str = "all") -> pd.DataFrame:
    """Search for players by name across datasets.

    Args:
        query: Search query
        data_type: "nil", "portal", or "all"

    Returns:
        DataFrame with matching players
    """
    results = []

    if data_type in ("nil", "all"):
        nil_df = get_nil_players()
        if not nil_df.empty:
            matches = nil_df[nil_df["name"].str.contains(query, case=False, na=False)]
            matches = matches.copy()
            matches["data_source"] = "nil_rankings"
            results.append(matches)

    if data_type in ("portal", "all"):
        portal_df = get_portal_players()
        if not portal_df.empty:
            matches = portal_df[portal_df["name"].str.contains(query, case=False, na=False)]
            matches = matches.copy()
            matches["data_source"] = "transfer_portal"
            results.append(matches)

    if results:
        return pd.concat(results, ignore_index=True)
    return pd.DataFrame()


def get_positions() -> List[str]:
    """Get list of football positions."""
    return [
        "QB", "RB", "WR", "TE", "OT", "OG", "C", "IOL",
        "EDGE", "DT", "DL", "LB", "CB", "S", "K", "P", "ATH"
    ]


def get_conferences() -> List[str]:
    """Get list of conferences."""
    return [
        "SEC", "Big Ten", "Big 12", "ACC", "Pac-12",
        "Mountain West", "AAC", "Sun Belt", "MAC", "C-USA"
    ]


def get_school_list() -> List[str]:
    """Get list of all schools from portal and rankings data."""
    schools = set()

    # Get schools from team rankings
    team_df = get_team_rankings()
    if not team_df.empty and "name" in team_df.columns:
        schools.update(team_df["name"].dropna().unique())

    # Get schools from portal data (origin and destination)
    portal_df = get_portal_players()
    if not portal_df.empty:
        if "origin_school" in portal_df.columns:
            schools.update(portal_df["origin_school"].dropna().unique())
        if "destination_school" in portal_df.columns:
            schools.update(portal_df["destination_school"].dropna().unique())

    # If we found schools from data, return sorted list
    if schools:
        return sorted([s for s in schools if s and str(s) != 'nan' and len(str(s)) > 1])

    # Fallback to common FBS schools
    return [
        "Alabama", "Arizona", "Arizona State", "Arkansas", "Auburn",
        "Ball State", "Baylor", "Boise State", "Boston College", "BYU",
        "Cal", "Central Michigan", "Charlotte", "Cincinnati", "Clemson", "Colorado",
        "Duke", "East Carolina", "Eastern Michigan", "Florida", "Florida State",
        "Fresno State", "Georgia", "Georgia Southern", "Georgia State", "Georgia Tech",
        "Hawaii", "Houston", "Illinois", "Indiana", "Iowa", "Iowa State",
        "Kansas", "Kansas State", "Kent State", "Kentucky", "Liberty",
        "Louisiana", "Louisville", "LSU", "Marshall", "Maryland", "Memphis", "Miami",
        "Miami (OH)", "Michigan", "Michigan State", "Middle Tennessee", "Minnesota",
        "Mississippi State", "Missouri", "NC State", "Nebraska", "Nevada", "New Mexico",
        "North Carolina", "North Texas", "Northern Illinois", "Northwestern", "Notre Dame",
        "Ohio", "Ohio State", "Oklahoma", "Oklahoma State", "Old Dominion", "Ole Miss",
        "Oregon", "Oregon State", "Penn State", "Pitt", "Purdue", "Rice", "Rutgers",
        "San Diego State", "San Jose State", "SMU", "South Alabama", "South Carolina",
        "Southern Miss", "Stanford", "Syracuse", "TCU", "Temple", "Tennessee", "Texas",
        "Texas A&M", "Texas State", "Texas Tech", "Toledo", "Troy", "Tulane", "Tulsa",
        "UAB", "UCF", "UCLA", "UNLV", "USC", "USF", "Utah", "Utah State", "UTEP", "UTSA",
        "Vanderbilt", "Virginia", "Virginia Tech", "Wake Forest", "Washington",
        "Washington State", "West Virginia", "Western Kentucky", "Western Michigan", "Wisconsin", "Wyoming"
    ]


def get_class_years() -> List[str]:
    """Get list of class years."""
    return ["Freshman", "Sophomore", "Junior", "Senior", "Graduate"]


def get_tiers() -> List[str]:
    """Get list of NIL value tiers."""
    return ["mega", "premium", "established", "emerging", "developing", "unknown"]


def get_portal_statuses() -> List[str]:
    """Get list of portal statuses."""
    return ["Committed", "Entered", "Withdrawn", "Expected"]


# =============================================================================
# Measurables Data
# =============================================================================

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cfbd_rosters() -> pd.DataFrame:
    """Load CFBD roster data with measurables (height, weight)."""
    roster_path = _get_data_path("cfbd_rosters.csv")

    if not roster_path.exists():
        # Try dated version
        import glob
        pattern = str(DATA_DIR / "cfbd_rosters_*.csv")
        files = glob.glob(pattern)
        if files:
            roster_path = Path(sorted(files)[-1])  # Most recent

    if not roster_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(roster_path)

    # Ensure height/weight are numeric
    if "height" in df.columns:
        df["height"] = pd.to_numeric(df["height"], errors="coerce")
    if "weight" in df.columns:
        df["weight"] = pd.to_numeric(df["weight"], errors="coerce")

    return df


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cfbd_player_stats() -> pd.DataFrame:
    """Load CFBD player stats data."""
    stats_path = _get_data_path("cfbd_player_stats.csv")

    if not stats_path.exists():
        # Try dated version
        import glob
        pattern = str(DATA_DIR / "cfbd_player_stats_*.csv")
        files = glob.glob(pattern)
        if files:
            stats_path = Path(sorted(files)[-1])  # Most recent

    if not stats_path.exists():
        return pd.DataFrame()

    df = pd.read_csv(stats_path)

    # Rename columns to match expected format in nil_valuator
    column_renames = {
        # Offensive stats
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
        # Defensive stats
        "defensive_TOT": "tackles",
        "defensive_SOLO": "solo_tackles",
        "defensive_TFL": "tackles_for_loss",
        "defensive_SACKS": "sacks",
        "defensive_QB HUR": "qb_hurries",
        "defensive_PD": "passes_defended",
        "interceptions_INT": "interceptions_def",
        "interceptions_YDS": "int_return_yards",
        "interceptions_TD": "int_return_tds",
        "fumbles_FUM": "fumbles",
        "fumbles_REC": "fumbles_recovered",
        "fumbles_LOST": "fumbles_lost",
        # Kicking stats
        "kicking_FGM": "fg_made",
        "kicking_FGA": "fg_attempted",
        "kicking_XPM": "xp_made",
        "kicking_XPA": "xp_attempted",
        "kicking_PTS": "kicking_points",
        # Punting stats
        "punting_NO": "punts",
        "punting_YDS": "punt_yards",
        "punting_AVG": "punt_avg",
        "punting_TB": "touchbacks",
        "punting_In 20": "punts_inside_20",
        # Return stats
        "kickReturns_NO": "kick_returns",
        "kickReturns_YDS": "kick_return_yards",
        "kickReturns_TD": "kick_return_tds",
        "puntReturns_NO": "punt_returns",
        "puntReturns_YDS": "punt_return_yards",
        "puntReturns_TD": "punt_return_tds",
    }
    df = df.rename(columns=column_renames)

    return df


def get_player_stats(player_name: str, team: str = None) -> Dict[str, Any]:
    """Look up stats for a player from CFBD player stats data.

    Args:
        player_name: Player name to search
        team: Optional team to narrow search

    Returns:
        Dict with passing_yards, rushing_yards, etc.
    """
    stats_df = get_cfbd_player_stats()

    if stats_df.empty:
        return {}

    # Standardize name for matching
    name_lower = str(player_name).lower().strip()

    # Try exact match first
    matches = stats_df[stats_df["player_name"].str.lower() == name_lower]

    # If team provided, filter further
    if not matches.empty and team:
        team_lower = str(team).lower()
        team_matches = matches[matches["team"].str.lower().str.contains(team_lower, na=False)]
        if not team_matches.empty:
            matches = team_matches

    if matches.empty:
        # Try fuzzy match on first/last name
        name_parts = name_lower.split()
        if len(name_parts) >= 2:
            first, last = name_parts[0], name_parts[-1]
            matches = stats_df[
                stats_df["player_name"].str.lower().str.contains(first, na=False) &
                stats_df["player_name"].str.lower().str.contains(last, na=False)
            ]

    if matches.empty:
        return {}

    # Get the most recent season's stats
    if "season" in matches.columns:
        matches = matches.sort_values("season", ascending=False)

    player = matches.iloc[0]

    # Return ALL stats as dict
    stats_cols = [
        # Offensive
        "passing_yards", "passing_tds", "interceptions", "passing_attempts",
        "completions", "completion_pct", "rushing_yards", "rushing_tds",
        "rushing_attempts", "yards_per_carry", "receiving_yards", "receiving_tds",
        "receptions", "yards_per_reception",
        # Defensive
        "tackles", "solo_tackles", "tackles_for_loss", "sacks", "qb_hurries",
        "passes_defended", "interceptions_def", "int_return_yards", "fumbles_recovered",
        # Kicking
        "fg_made", "fg_attempted", "xp_made", "kicking_points",
        # Punting
        "punts", "punt_avg", "punts_inside_20",
        # Returns
        "kick_return_yards", "kick_return_tds", "punt_return_yards", "punt_return_tds",
    ]

    result = {}
    for col in stats_cols:
        if col in player.index and pd.notna(player[col]):
            result[col] = player[col]

    return result


def get_player_measurables(player_name: str, team: str = None) -> Dict[str, Any]:
    """Look up measurables for a player from CFBD roster data.

    Args:
        player_name: Player name to search
        team: Optional team to narrow search

    Returns:
        Dict with height, weight, height_display, etc.
    """
    rosters = get_cfbd_rosters()

    if rosters.empty:
        return {}

    # Standardize name for matching
    name_lower = str(player_name).lower().strip()

    # Try exact match first
    matches = rosters[rosters["player_name"].str.lower() == name_lower]

    # If team specified, filter
    if team and not matches.empty:
        team_matches = matches[matches["team"].str.lower().str.contains(str(team).lower(), na=False)]
        if not team_matches.empty:
            matches = team_matches

    # If no exact match, try partial
    if matches.empty:
        name_parts = name_lower.split()
        if len(name_parts) >= 2:
            matches = rosters[
                rosters["player_name"].str.lower().str.contains(name_parts[-1], na=False) &
                rosters["player_name"].str.lower().str.contains(name_parts[0], na=False)
            ]

    if matches.empty:
        return {}

    # Get most recent season
    player = matches.sort_values("season", ascending=False).iloc[0]

    height_inches = player.get("height")
    weight = player.get("weight")

    return {
        "height_inches": height_inches,
        "height_display": format_height(height_inches) if pd.notna(height_inches) else None,
        "weight": int(weight) if pd.notna(weight) else None,
        "year": player.get("year"),
        "jersey": player.get("jersey"),
        "home_city": player.get("home_city"),
        "home_state": player.get("home_state"),
        "team": player.get("team"),
        "position": player.get("position"),
    }


def format_height(inches: float) -> str:
    """Convert height in inches to feet-inches format."""
    if pd.isna(inches) or inches <= 0:
        return None
    feet = int(inches // 12)
    remaining_inches = int(inches % 12)
    return f"{feet}'{remaining_inches}\""


def parse_height_to_inches(height_str: str) -> Optional[float]:
    """Parse height string (e.g., '6-2' or '6\\'2\"') to inches."""
    if not height_str or pd.isna(height_str):
        return None

    import re
    # Match patterns like 6-2, 6'2", 6'2, 6-02, etc.
    match = re.match(r"(\d+)['\-](\d+)", str(height_str).strip())
    if match:
        feet = int(match.group(1))
        inches = int(match.group(2))
        return feet * 12 + inches

    return None


@st.cache_data(ttl=600)
def get_portal_players_with_measurables(year: int = 2026, status: str = None) -> pd.DataFrame:
    """Get portal players enriched with measurables AND stats from CFBD.

    This adds height, weight, formatted displays, AND performance stats for each player.
    Stats are critical for accurate NIL valuations and WAR calculations.
    """
    # Get portal players with NIL enrichment
    portal_df = get_portal_players(year=year, status=status, enrich_nil=True)

    if portal_df.empty:
        return portal_df

    # Load CFBD rosters for measurables lookup
    rosters = get_cfbd_rosters()

    # Load CFBD player stats
    stats_df = get_cfbd_player_stats()

    # Initialize columns if no data
    if rosters.empty:
        portal_df["height_inches"] = None
        portal_df["height_display"] = None
        portal_df["weight"] = None

    # Create lookup dict from rosters (name -> measurables)
    roster_lookup = {}
    if not rosters.empty:
        for _, row in rosters.iterrows():
            name_key = str(row.get("player_name", "")).lower().strip()
            if name_key and name_key not in roster_lookup:
                roster_lookup[name_key] = {
                    "height_inches": row.get("height"),
                    "weight": row.get("weight"),
                    "year": row.get("year"),
                    "jersey": row.get("jersey"),
                }

    # Create lookup dict from stats (name -> stats) - ALL stat types
    stats_lookup = {}
    if not stats_df.empty:
        # Get most recent season for each player
        if "season" in stats_df.columns:
            stats_df = stats_df.sort_values("season", ascending=False)
        for _, row in stats_df.iterrows():
            name_key = str(row.get("player_name", "")).lower().strip()
            if name_key and name_key not in stats_lookup:
                stats_lookup[name_key] = {
                    # Offensive stats
                    "passing_yards": row.get("passing_yards"),
                    "passing_tds": row.get("passing_tds"),
                    "interceptions": row.get("interceptions"),
                    "completion_pct": row.get("completion_pct"),
                    "rushing_yards": row.get("rushing_yards"),
                    "rushing_tds": row.get("rushing_tds"),
                    "yards_per_carry": row.get("yards_per_carry"),
                    "receiving_yards": row.get("receiving_yards"),
                    "receiving_tds": row.get("receiving_tds"),
                    "receptions": row.get("receptions"),
                    "yards_per_reception": row.get("yards_per_reception"),
                    # Defensive stats
                    "tackles": row.get("tackles"),
                    "solo_tackles": row.get("solo_tackles"),
                    "tackles_for_loss": row.get("tackles_for_loss"),
                    "sacks": row.get("sacks"),
                    "qb_hurries": row.get("qb_hurries"),
                    "passes_defended": row.get("passes_defended"),
                    "interceptions_def": row.get("interceptions_def"),
                    "int_return_yards": row.get("int_return_yards"),
                    "fumbles_recovered": row.get("fumbles_recovered"),
                    # Kicking stats
                    "fg_made": row.get("fg_made"),
                    "fg_attempted": row.get("fg_attempted"),
                    "xp_made": row.get("xp_made"),
                    "kicking_points": row.get("kicking_points"),
                    # Punting stats
                    "punts": row.get("punts"),
                    "punt_avg": row.get("punt_avg"),
                    "punts_inside_20": row.get("punts_inside_20"),
                    # Return stats
                    "kick_return_yards": row.get("kick_return_yards"),
                    "kick_return_tds": row.get("kick_return_tds"),
                    "punt_return_yards": row.get("punt_return_yards"),
                    "punt_return_tds": row.get("punt_return_tds"),
                }

    # All stat columns to add
    stat_columns = [
        # Offensive
        "passing_yards", "passing_tds", "interceptions", "completion_pct",
        "rushing_yards", "rushing_tds", "yards_per_carry",
        "receiving_yards", "receiving_tds", "receptions", "yards_per_reception",
        # Defensive
        "tackles", "solo_tackles", "tackles_for_loss", "sacks", "qb_hurries",
        "passes_defended", "interceptions_def", "int_return_yards", "fumbles_recovered",
        # Kicking
        "fg_made", "fg_attempted", "xp_made", "kicking_points",
        # Punting
        "punts", "punt_avg", "punts_inside_20",
        # Returns
        "kick_return_yards", "kick_return_tds", "punt_return_yards", "punt_return_tds",
    ]

    # Initialize stat lists
    stat_lists = {col: [] for col in stat_columns}

    # Enrich portal players with measurables AND stats
    heights = []
    weights = []

    for _, row in portal_df.iterrows():
        name_key = str(row.get("name", "")).lower().strip()

        # Measurables
        measurables = roster_lookup.get(name_key, {})
        heights.append(measurables.get("height_inches"))
        weights.append(measurables.get("weight"))

        # Stats - all columns
        stats = stats_lookup.get(name_key, {})
        for col in stat_columns:
            stat_lists[col].append(stats.get(col))

    # Add measurables columns
    portal_df["height_inches"] = heights
    portal_df["weight"] = weights
    portal_df["height_display"] = portal_df["height_inches"].apply(
        lambda x: format_height(x) if pd.notna(x) else None
    )

    # Add all stats columns
    for col in stat_columns:
        portal_df[col] = stat_lists[col]

    return portal_df


def filter_by_measurables(
    df: pd.DataFrame,
    min_height: float = None,
    max_height: float = None,
    min_weight: float = None,
    max_weight: float = None,
) -> pd.DataFrame:
    """Filter DataFrame by measurables.

    Args:
        df: DataFrame with height_inches and weight columns
        min_height: Minimum height in inches (e.g., 72 for 6'0")
        max_height: Maximum height in inches
        min_weight: Minimum weight in pounds
        max_weight: Maximum weight in pounds

    Returns:
        Filtered DataFrame
    """
    result = df.copy()

    if min_height is not None and "height_inches" in result.columns:
        result = result[result["height_inches"].fillna(0) >= min_height]

    if max_height is not None and "height_inches" in result.columns:
        result = result[(result["height_inches"].fillna(999) <= max_height) | (result["height_inches"].isna())]

    if min_weight is not None and "weight" in result.columns:
        result = result[result["weight"].fillna(0) >= min_weight]

    if max_weight is not None and "weight" in result.columns:
        result = result[(result["weight"].fillna(999) <= max_weight) | (result["weight"].isna())]

    return result


# Height presets for common position requirements
HEIGHT_PRESETS = {
    "QB": {"min": 72, "ideal_min": 74, "label": "6'0\"+ (ideal 6'2\"+)"},
    "WR": {"min": 69, "tall": 75, "label": "5'9\"+ (tall: 6'3\"+)"},
    "RB": {"min": 66, "max": 74, "label": "5'6\" - 6'2\""},
    "TE": {"min": 75, "ideal_min": 77, "label": "6'3\"+ (ideal 6'5\"+)"},
    "OT": {"min": 76, "ideal_min": 78, "label": "6'4\"+ (ideal 6'6\"+)"},
    "OG": {"min": 74, "ideal_min": 76, "label": "6'2\"+ (ideal 6'4\"+)"},
    "C": {"min": 73, "ideal_min": 75, "label": "6'1\"+ (ideal 6'3\"+)"},
    "EDGE": {"min": 74, "ideal_min": 76, "label": "6'2\"+ (ideal 6'4\"+)"},
    "DT": {"min": 74, "ideal_min": 76, "label": "6'2\"+ (ideal 6'4\"+)"},
    "LB": {"min": 72, "ideal_min": 74, "label": "6'0\"+ (ideal 6'2\"+)"},
    "CB": {"min": 69, "max": 75, "label": "5'9\" - 6'3\""},
    "S": {"min": 70, "ideal_min": 73, "label": "5'10\"+ (ideal 6'1\"+)"},
}

WEIGHT_PRESETS = {
    "QB": {"min": 200, "ideal_min": 215, "label": "200+ lbs (ideal 215+)"},
    "WR": {"min": 170, "max": 220, "label": "170-220 lbs"},
    "RB": {"min": 190, "max": 230, "label": "190-230 lbs"},
    "TE": {"min": 240, "ideal_min": 250, "label": "240+ lbs (ideal 250+)"},
    "OT": {"min": 300, "ideal_min": 315, "label": "300+ lbs (ideal 315+)"},
    "OG": {"min": 300, "ideal_min": 315, "label": "300+ lbs (ideal 315+)"},
    "C": {"min": 290, "ideal_min": 305, "label": "290+ lbs (ideal 305+)"},
    "EDGE": {"min": 240, "ideal_min": 260, "label": "240+ lbs (ideal 260+)"},
    "DT": {"min": 280, "ideal_min": 300, "label": "280+ lbs (ideal 300+)"},
    "LB": {"min": 220, "ideal_min": 235, "label": "220+ lbs (ideal 235+)"},
    "CB": {"min": 175, "max": 210, "label": "175-210 lbs"},
    "S": {"min": 190, "ideal_min": 205, "label": "190+ lbs (ideal 205+)"},
}
