"""NIL Value Estimation Utilities.

Provides functions to estimate NIL values for players without known valuations
using our proprietary algorithm based on position, school tier, and recruiting profile.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Tuple, Optional

# Position value factors (same as training algorithm)
POSITION_VALUES = {
    "QB": 1.0, "WR": 0.8, "RB": 0.6, "TE": 0.55,
    "OT": 0.7, "OG": 0.5, "C": 0.5, "OL": 0.55, "IOL": 0.55,
    "DE": 0.75, "DT": 0.65, "LB": 0.55, "CB": 0.7, "S": 0.6,
    "EDGE": 0.8, "DL": 0.65, "DB": 0.65,
    "K": 0.2, "P": 0.15, "ATH": 0.5,
}

# School tier mappings (will be populated from data)
SCHOOL_TIERS = {}

# Base NIL values by tier (median values from training data)
TIER_BASE_VALUES = {
    6: 450000,   # Top 15 portal classes
    5: 280000,   # 16-35
    4: 150000,   # 36-65
    3: 75000,    # 66-100
    2: 35000,    # Below 100
    1: 15000,    # Unknown/FCS
}

# Confidence margins by level
CONFIDENCE_RANGES = {
    "high": 0.25,      # +/- 25% for high confidence
    "medium": 0.40,    # +/- 40% for medium confidence
    "low": 0.60,       # +/- 60% for low confidence
    "actual": 0.10,    # +/- 10% for actual On3 values (market variance)
}


def load_school_tiers() -> Dict[str, int]:
    """Load school tier mappings from team rankings data."""
    global SCHOOL_TIERS

    if SCHOOL_TIERS:
        return SCHOOL_TIERS

    # Try to load from team rankings
    possible_paths = [
        Path(__file__).parent.parent.parent / "ml-engine" / "data" / "processed" / "on3_team_portal_rankings.csv",
        Path("/app/ml-engine/data/processed/on3_team_portal_rankings.csv"),
    ]

    for path in possible_paths:
        if path.exists():
            df = pd.read_csv(path)
            if "year" in df.columns:
                df = df[df["year"] == df["year"].max()]
            if "overall_score" in df.columns:
                df = df.sort_values("overall_score", ascending=False)

            for idx, row in df.iterrows():
                team = row.get("team", "")
                rank = len(SCHOOL_TIERS) + 1
                if rank <= 15:
                    tier = 6
                elif rank <= 35:
                    tier = 5
                elif rank <= 65:
                    tier = 4
                elif rank <= 100:
                    tier = 3
                else:
                    tier = 2
                SCHOOL_TIERS[team.lower()] = tier
            break

    return SCHOOL_TIERS


def get_school_tier(school_name: str) -> int:
    """Get tier for a school (1-6, 6 being highest)."""
    if not school_name or pd.isna(school_name):
        return 2

    school_tiers = load_school_tiers()
    school_lower = str(school_name).lower().strip()

    # Direct match
    if school_lower in school_tiers:
        return school_tiers[school_lower]

    # Partial match
    for key, tier in school_tiers.items():
        if key in school_lower or school_lower in key:
            return tier

    # Check for known P5/blue blood keywords
    blue_bloods = ["alabama", "ohio state", "georgia", "michigan", "texas", "lsu", "usc", "notre dame"]
    p5_keywords = ["sec", "big ten", "big 12", "acc", "pac-12"]

    for bb in blue_bloods:
        if bb in school_lower:
            return 6

    return 3  # Default to mid-tier


def estimate_nil_value(
    position: str,
    school: str = None,
    stars: float = None,
    rating: float = None,
    national_rank: float = None,
    on3_value: float = None,
) -> Dict:
    """Estimate NIL value for a player using our algorithm.

    Args:
        position: Player position (QB, WR, etc.)
        school: Current/destination school name
        stars: Recruiting star rating (2-5)
        rating: Recruiting rating (0-100 or 0-1)
        national_rank: National recruiting rank
        on3_value: Known On3 valuation (if any)

    Returns:
        Dict with:
            - predicted_value: Our estimate
            - on3_value: The On3 value (if known)
            - value_range: (low, high) tuple
            - confidence: "actual", "high", "medium", or "low"
            - factors: Dict explaining value breakdown
    """
    # If On3 has a real value, use it as primary with our range
    if on3_value and on3_value > 0:
        margin = CONFIDENCE_RANGES["actual"]
        return {
            "predicted_value": on3_value,
            "on3_value": on3_value,
            "portaliq_estimate": estimate_without_on3(position, school, stars, rating, national_rank),
            "value_range": (on3_value * (1 - margin), on3_value * (1 + margin)),
            "confidence": "actual",
            "factors": {
                "source": "On3 Valuation",
                "note": "Based on On3's public NIL database"
            }
        }

    # Calculate our estimate
    predicted = estimate_without_on3(position, school, stars, rating, national_rank)

    # Determine confidence
    has_stars = stars is not None and not pd.isna(stars) and stars > 0
    has_rating = rating is not None and not pd.isna(rating) and rating > 0
    school_tier = get_school_tier(school)

    if has_stars and stars >= 4 and school_tier >= 4:
        confidence = "high"
    elif has_stars and stars >= 3 or has_rating:
        confidence = "medium"
    else:
        confidence = "low"

    margin = CONFIDENCE_RANGES[confidence]

    return {
        "predicted_value": predicted,
        "on3_value": None,
        "portaliq_estimate": predicted,
        "value_range": (predicted * (1 - margin), predicted * (1 + margin)),
        "confidence": confidence,
        "factors": calculate_factors(position, school, stars, rating, national_rank)
    }


def estimate_without_on3(
    position: str,
    school: str = None,
    stars: float = None,
    rating: float = None,
    national_rank: float = None,
) -> float:
    """Calculate NIL estimate using our algorithm (no On3 data)."""

    # Get base value from school tier
    school_tier = get_school_tier(school)
    base_value = TIER_BASE_VALUES.get(school_tier, TIER_BASE_VALUES[3])

    # Position multiplier
    pos_upper = str(position).upper() if position else "ATH"
    position_mult = POSITION_VALUES.get(pos_upper, 0.5)

    # Star multiplier
    if stars and not pd.isna(stars) and stars > 0:
        star_mult = {5: 2.5, 4: 1.5, 3: 1.0, 2: 0.6}.get(int(stars), 1.0)
    else:
        star_mult = 0.8  # Unknown stars penalty

    # Rating bonus (normalized to 0-1)
    if rating and not pd.isna(rating):
        if rating > 1:
            rating = rating / 100  # Convert 0-100 to 0-1
        rating_bonus = 1 + (rating - 0.8) * 2  # Bonus for high ratings
    else:
        rating_bonus = 1.0

    # National rank bonus
    if national_rank and not pd.isna(national_rank) and national_rank > 0:
        if national_rank <= 50:
            rank_mult = 2.0
        elif national_rank <= 100:
            rank_mult = 1.5
        elif national_rank <= 250:
            rank_mult = 1.2
        elif national_rank <= 500:
            rank_mult = 1.0
        else:
            rank_mult = 0.9
    else:
        rank_mult = 1.0

    # Calculate final value
    estimated = base_value * position_mult * star_mult * rating_bonus * rank_mult

    # QB premium
    if pos_upper == "QB":
        estimated *= 1.5

    return round(estimated, 2)


def calculate_factors(
    position: str,
    school: str,
    stars: float,
    rating: float,
    national_rank: float,
) -> Dict:
    """Calculate factor breakdown for explanation."""
    school_tier = get_school_tier(school)
    pos_value = POSITION_VALUES.get(str(position).upper(), 0.5)

    factors = {
        "school_tier": {
            "value": school_tier,
            "label": f"Tier {school_tier}",
            "description": {
                6: "Elite program (Top 15)",
                5: "Top program (16-35)",
                4: "Strong program (36-65)",
                3: "Mid-tier program (66-100)",
                2: "Lower-tier program",
                1: "Unknown/FCS",
            }.get(school_tier, "Unknown")
        },
        "position_value": {
            "value": pos_value,
            "label": str(position).upper(),
            "description": "High demand" if pos_value >= 0.7 else "Moderate demand" if pos_value >= 0.5 else "Lower demand"
        },
    }

    if stars and not pd.isna(stars) and stars > 0:
        factors["recruiting_stars"] = {
            "value": int(stars),
            "label": f"{int(stars)}-Star",
            "description": "Elite recruit" if stars >= 5 else "Blue-chip" if stars >= 4 else "Quality recruit" if stars >= 3 else "Developmental"
        }

    if rating and not pd.isna(rating) and rating > 0:
        factors["recruiting_rating"] = {
            "value": rating if rating <= 1 else rating / 100,
            "label": f"{rating:.2f}" if rating <= 1 else f"{rating:.1f}",
            "description": "Top-tier rating" if (rating > 0.9 or rating > 90) else "Strong rating"
        }

    if national_rank and not pd.isna(national_rank) and national_rank > 0:
        factors["national_rank"] = {
            "value": int(national_rank),
            "label": f"#{int(national_rank)}",
            "description": "Elite national ranking" if national_rank <= 100 else "Strong ranking" if national_rank <= 300 else "Solid ranking"
        }

    return factors


def enrich_portal_data(portal_df: pd.DataFrame, valuations_df: pd.DataFrame = None) -> pd.DataFrame:
    """Enrich portal DataFrame with NIL estimates.

    Args:
        portal_df: DataFrame with portal players
        valuations_df: Optional DataFrame with existing valuations

    Returns:
        DataFrame with added NIL estimate columns
    """
    if portal_df.empty:
        return portal_df

    # Create working copy
    enriched = portal_df.copy()

    # Create name lookup from valuations if provided
    valuation_lookup = {}
    if valuations_df is not None and not valuations_df.empty:
        for _, row in valuations_df.iterrows():
            name_key = str(row.get("name", "")).lower().strip()
            valuation_lookup[name_key] = {
                "nil_value": row.get("nil_value_predicted", row.get("nil_value", 0)),
                "confidence": row.get("confidence", "medium"),
                "is_predicted": row.get("is_predicted", True),
                "tier": row.get("nil_tier", "unknown"),
            }

    # Process each player
    estimates = []
    for _, row in enriched.iterrows():
        name_key = str(row.get("name", "")).lower().strip()

        # Check if we have a valuation
        existing = valuation_lookup.get(name_key)

        # Get On3 value from portal data
        on3_value = row.get("nil_valuation", row.get("nil_value", 0))
        if pd.isna(on3_value):
            on3_value = 0

        # Get school (destination if available, else origin)
        school = row.get("to_school", row.get("destination_school", row.get("from_school", row.get("origin_school", ""))))

        if existing and existing["nil_value"] > 0:
            # Use existing valuation
            est = {
                "portaliq_value": existing["nil_value"],
                "on3_value": on3_value if on3_value > 0 else None,
                "confidence": existing["confidence"] if existing["is_predicted"] else "actual",
                "nil_tier": existing["tier"],
                "is_predicted": existing["is_predicted"],
            }
        else:
            # Generate new estimate
            result = estimate_nil_value(
                position=row.get("position"),
                school=school,
                stars=row.get("stars"),
                rating=row.get("rating", row.get("overall_rating")),
                national_rank=row.get("national_rank"),
                on3_value=on3_value,
            )
            est = {
                "portaliq_value": result["predicted_value"],
                "on3_value": result["on3_value"],
                "confidence": result["confidence"],
                "nil_tier": get_tier_from_value(result["predicted_value"]),
                "is_predicted": result["confidence"] != "actual",
            }

        # Calculate range
        margin = CONFIDENCE_RANGES.get(est["confidence"], 0.4)
        est["value_low"] = est["portaliq_value"] * (1 - margin)
        est["value_high"] = est["portaliq_value"] * (1 + margin)

        estimates.append(est)

    # Add estimate columns to DataFrame
    est_df = pd.DataFrame(estimates)
    for col in est_df.columns:
        enriched[col] = est_df[col].values

    return enriched


def get_tier_from_value(value: float) -> str:
    """Get tier name from NIL value."""
    if pd.isna(value) or value == 0:
        return "unknown"
    if value >= 1_000_000:
        return "mega"
    if value >= 500_000:
        return "premium"
    if value >= 100_000:
        return "solid"
    if value >= 25_000:
        return "moderate"
    return "entry"


def format_value_range(low: float, high: float) -> str:
    """Format value range for display."""
    def fmt(v):
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"${v/1_000:.0f}K"
        return f"${v:.0f}"

    return f"{fmt(low)} - {fmt(high)}"
