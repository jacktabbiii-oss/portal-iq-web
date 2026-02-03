"""Data loading utilities for Portal IQ Dashboard.

Loads real data from On3 scraped files and CFBD stats.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    """Get NIL player data with proprietary valuations."""
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

        return df

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

    return df


@st.cache_data(ttl=600)
def get_portal_players(year: int = 2026, status: str = None) -> pd.DataFrame:
    """Get transfer portal player data from On3.

    Args:
        year: Filter by year (2024, 2025, 2026)
        status: Filter by status (Committed, Entered, etc.)
    """
    portal_path = _get_data_path("on3_transfer_portal.csv")

    if not portal_path.exists():
        st.warning("Portal data not found. Run the On3 scraper first.")
        return pd.DataFrame()

    df = pd.read_csv(portal_path)

    # Standardize column names
    df = df.rename(columns={
        "nil_valuation": "nil_value",
        "from_school": "origin_school",
        "to_school": "destination_school",
        "rating": "overall_rating",
    })

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

    return df


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
