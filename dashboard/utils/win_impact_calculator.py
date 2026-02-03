"""Portal IQ Win Impact Calculator - Proprietary Algorithms.

Advanced win impact analysis using multiple data sources:
- NIL valuations (actual + predicted)
- Transfer portal data
- Team records and rankings
- Player measurables from CFBD
- Recruiting ratings

This creates Portal IQ's proprietary WAR (Wins Above Replacement) and
team impact scoring that goes beyond basic portal rankings.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple


# =============================================================================
# POSITION VALUE WEIGHTS
# =============================================================================

# Base position WAR values (expected wins above replacement for elite player)
POSITION_BASE_WAR = {
    # Offense - Premium positions
    "QB": 3.0,      # Quarterbacks have highest single-player impact
    "WR": 1.2,      # Top receivers create big plays
    "RB": 0.9,      # Running backs still valuable but committee approach
    "TE": 0.8,      # Receiving TEs more valuable

    # Offensive Line
    "OT": 1.0,      # Tackles protect blind side
    "OG": 0.7,      # Guards important for run game
    "C": 0.6,       # Center controls line
    "IOL": 0.7,     # Generic interior line

    # Defense - Premium positions
    "EDGE": 1.5,    # Pass rushers change games
    "CB": 1.2,      # Corners lock down receivers
    "S": 0.9,       # Safeties cover deep
    "LB": 1.0,      # Linebackers versatile
    "DT": 0.8,      # Interior disruption
    "DL": 0.9,      # Generic defensive line

    # Special Teams
    "K": 0.4,       # Kickers can swing close games
    "P": 0.3,       # Punters flip field position

    # Default
    "ATH": 0.8,     # Athletes can play anywhere
}

# Position scarcity multiplier (harder to find quality = higher value)
POSITION_SCARCITY = {
    "QB": 1.4,      # Elite QBs are rare
    "EDGE": 1.3,    # Pass rushers always in demand
    "OT": 1.2,      # Good tackles hard to find
    "CB": 1.2,      # Lockdown corners scarce
    "WR": 1.0,      # More available
    "RB": 0.8,      # Running backs replaceable
}


# =============================================================================
# STAR RATING MULTIPLIERS
# =============================================================================

# How much recruiting stars multiply base WAR
STAR_MULTIPLIERS = {
    5: 2.0,    # 5-star = proven elite talent
    4: 1.5,    # 4-star = high upside
    3: 1.0,    # 3-star = baseline
    2: 0.6,    # 2-star = developmental
    1: 0.3,    # Walk-on level
}

# Additional bonus for high recruiting rating within star tier
def get_rating_bonus(rating: float, stars: int) -> float:
    """Bonus for being at top of star tier (e.g., high 4-star vs low 4-star)."""
    if pd.isna(rating) or rating <= 0:
        return 0

    # Normalize rating to 0-1 scale if needed
    if rating > 1:
        rating = rating / 100

    # Top of tier gets bonus
    tier_thresholds = {5: 0.99, 4: 0.95, 3: 0.88, 2: 0.80}
    threshold = tier_thresholds.get(stars, 0.85)

    if rating >= threshold:
        return 0.15  # 15% bonus for top of tier
    return 0


# =============================================================================
# SCHOOL TIER FACTORS
# =============================================================================

SCHOOL_TIERS = {
    "elite": {
        "schools": ["Alabama", "Georgia", "Ohio State", "Michigan", "Texas",
                   "Oregon", "Penn State", "Notre Dame", "USC", "Clemson"],
        "multiplier": 1.3,      # Elite programs maximize player value
        "development": 1.2,     # Better development = higher ceiling
    },
    "power": {
        "schools": ["LSU", "Oklahoma", "Florida", "Miami", "Tennessee", "Auburn",
                   "Texas A&M", "Wisconsin", "UCLA", "Washington", "Utah", "Ole Miss",
                   "Missouri", "Florida State", "Louisville", "Kentucky", "Arkansas"],
        "multiplier": 1.15,
        "development": 1.1,
    },
    "rising": {
        "schools": ["Colorado", "Indiana", "Illinois", "Iowa State", "Kansas State",
                   "Arizona", "NC State", "Virginia Tech", "Baylor", "Pittsburgh",
                   "SMU", "Syracuse", "Duke", "Cal", "Nebraska"],
        "multiplier": 1.0,
        "development": 1.0,
    },
    "developmental": {
        "schools": [],  # Default tier
        "multiplier": 0.85,
        "development": 0.9,
    }
}


def get_school_tier(school: str) -> Tuple[str, Dict]:
    """Get school tier and associated multipliers."""
    if not school or pd.isna(school):
        return "developmental", SCHOOL_TIERS["developmental"]

    school_lower = str(school).lower()

    for tier_name, tier_data in SCHOOL_TIERS.items():
        if tier_name == "developmental":
            continue
        for s in tier_data["schools"]:
            if s.lower() in school_lower or school_lower in s.lower():
                return tier_name, tier_data

    return "developmental", SCHOOL_TIERS["developmental"]


# =============================================================================
# MEASURABLES SCORING
# =============================================================================

# Ideal measurables by position (height in inches, weight in lbs)
IDEAL_MEASURABLES = {
    "QB": {"height": 75, "weight": 220, "height_range": (72, 80), "weight_range": (200, 250)},
    "WR": {"height": 73, "weight": 195, "height_range": (69, 78), "weight_range": (175, 220)},
    "RB": {"height": 70, "weight": 210, "height_range": (66, 74), "weight_range": (190, 235)},
    "TE": {"height": 77, "weight": 255, "height_range": (75, 80), "weight_range": (240, 275)},
    "OT": {"height": 78, "weight": 315, "height_range": (76, 82), "weight_range": (295, 340)},
    "OG": {"height": 76, "weight": 315, "height_range": (74, 79), "weight_range": (300, 335)},
    "C": {"height": 75, "weight": 305, "height_range": (73, 77), "weight_range": (290, 320)},
    "EDGE": {"height": 76, "weight": 265, "height_range": (74, 79), "weight_range": (245, 285)},
    "DT": {"height": 75, "weight": 310, "height_range": (73, 78), "weight_range": (285, 340)},
    "LB": {"height": 74, "weight": 235, "height_range": (72, 76), "weight_range": (220, 255)},
    "CB": {"height": 71, "weight": 190, "height_range": (69, 75), "weight_range": (175, 210)},
    "S": {"height": 73, "weight": 205, "height_range": (70, 76), "weight_range": (190, 220)},
}


def calculate_measurables_score(position: str, height: float, weight: float) -> float:
    """
    Calculate how well a player's measurables fit their position.
    Returns multiplier from 0.8 to 1.2.
    """
    if not position or position not in IDEAL_MEASURABLES:
        return 1.0

    ideal = IDEAL_MEASURABLES[position]
    score = 1.0

    # Height score
    if pd.notna(height) and height > 0:
        h_min, h_max = ideal["height_range"]
        if h_min <= height <= h_max:
            # Within range - bonus for being close to ideal
            diff = abs(height - ideal["height"]) / (h_max - h_min)
            score += 0.05 * (1 - diff)  # Up to 5% bonus
        elif height < h_min:
            score -= 0.05  # Undersized penalty
        else:
            score += 0.02  # Slightly oversized can be ok

    # Weight score
    if pd.notna(weight) and weight > 0:
        w_min, w_max = ideal["weight_range"]
        if w_min <= weight <= w_max:
            diff = abs(weight - ideal["weight"]) / (w_max - w_min)
            score += 0.05 * (1 - diff)
        elif weight < w_min:
            score -= 0.08  # Underweight bigger penalty
        # Overweight is position-dependent, not penalized here

    return max(0.8, min(1.2, score))


# =============================================================================
# EXPERIENCE FACTOR
# =============================================================================

EXPERIENCE_MULTIPLIERS = {
    "Freshman": 0.7,     # Raw, needs development
    "RS Freshman": 0.8,  # Year in system
    "Sophomore": 0.9,    # Growing
    "RS Sophomore": 1.0, # Baseline
    "Junior": 1.1,       # Prime years
    "RS Junior": 1.15,   # Experienced
    "Senior": 1.1,       # Experienced but one year left
    "RS Senior": 1.05,   # Very experienced, limited upside window
    "Graduate": 1.0,     # Immediate contributor
}


def get_experience_multiplier(year: str) -> float:
    """Get multiplier based on eligibility year."""
    if not year or pd.isna(year):
        return 1.0

    year_str = str(year).strip()

    # Try direct match first
    if year_str in EXPERIENCE_MULTIPLIERS:
        return EXPERIENCE_MULTIPLIERS[year_str]

    # Try partial matching
    year_lower = year_str.lower()
    if "fresh" in year_lower:
        return 0.75
    elif "soph" in year_lower:
        return 0.95
    elif "junior" in year_lower:
        return 1.1
    elif "senior" in year_lower:
        return 1.05
    elif "grad" in year_lower:
        return 1.0

    return 1.0


# =============================================================================
# NIL MARKET SIGNAL
# =============================================================================

def get_nil_market_signal(nil_value: float, position: str) -> float:
    """
    NIL value as a market signal - the market often knows something.
    High NIL = market believes in player value.
    Returns bonus from 0 to 0.5 WAR.
    """
    if not nil_value or pd.isna(nil_value) or nil_value <= 0:
        return 0

    # Position-adjusted thresholds (QBs naturally get more NIL)
    position_nil_baseline = {
        "QB": 500000,
        "WR": 200000,
        "RB": 150000,
        "EDGE": 150000,
        "CB": 120000,
    }

    baseline = position_nil_baseline.get(position, 100000)

    # Calculate bonus based on how much above baseline
    ratio = nil_value / baseline

    if ratio >= 10:  # 10x baseline = superstar
        return 0.5
    elif ratio >= 5:  # 5x = premium player
        return 0.35
    elif ratio >= 2:  # 2x = above average
        return 0.2
    elif ratio >= 1:  # At baseline
        return 0.1
    else:
        return 0


# =============================================================================
# MAIN WAR CALCULATION
# =============================================================================

def calculate_player_war(
    position: str,
    stars: float = None,
    rating: float = None,
    nil_value: float = None,
    destination_school: str = None,
    height: float = None,
    weight: float = None,
    year: str = None,
    is_predicted_nil: bool = True
) -> Dict[str, Any]:
    """
    Calculate Portal IQ's proprietary WAR (Wins Above Replacement) for a player.

    This comprehensive algorithm considers:
    - Position value and scarcity
    - Recruiting profile (stars + rating)
    - NIL market signal (actual or predicted)
    - Destination school quality
    - Physical measurables
    - Experience/eligibility

    Returns detailed breakdown of WAR calculation.
    """
    # Normalize inputs
    position = str(position).upper() if position else "ATH"
    stars = int(stars) if pd.notna(stars) and stars else 3

    # 1. Base WAR from position
    base_war = POSITION_BASE_WAR.get(position, 0.8)
    scarcity = POSITION_SCARCITY.get(position, 1.0)

    # 2. Star rating multiplier
    star_mult = STAR_MULTIPLIERS.get(stars, 1.0)
    rating_bonus = get_rating_bonus(rating, stars)

    # 3. School tier factor
    tier_name, tier_data = get_school_tier(destination_school)
    school_mult = tier_data["multiplier"]

    # 4. Measurables score
    measurables_mult = calculate_measurables_score(position, height, weight)

    # 5. Experience factor
    experience_mult = get_experience_multiplier(year)

    # 6. NIL market signal (bonus, not multiplier)
    nil_bonus = get_nil_market_signal(nil_value, position)
    # Reduce confidence in predicted NIL
    if is_predicted_nil:
        nil_bonus *= 0.7

    # Calculate final WAR
    raw_war = base_war * scarcity
    adjusted_war = raw_war * star_mult * (1 + rating_bonus)
    school_adjusted = adjusted_war * school_mult
    measurables_adjusted = school_adjusted * measurables_mult
    experience_adjusted = measurables_adjusted * experience_mult
    final_war = experience_adjusted + nil_bonus

    # Round to 2 decimals
    final_war = round(final_war, 2)

    # Confidence level based on data completeness
    confidence_score = 0
    if pd.notna(stars) and stars > 0:
        confidence_score += 30
    if pd.notna(nil_value) and nil_value > 0:
        confidence_score += 25 if not is_predicted_nil else 15
    if pd.notna(height) and pd.notna(weight):
        confidence_score += 20
    if destination_school and tier_name != "developmental":
        confidence_score += 15
    if year:
        confidence_score += 10

    if confidence_score >= 80:
        confidence = "high"
    elif confidence_score >= 50:
        confidence = "medium"
    else:
        confidence = "low"

    return {
        "war": final_war,
        "war_low": round(final_war * 0.7, 2),
        "war_high": round(final_war * 1.3, 2),
        "confidence": confidence,
        "breakdown": {
            "base_war": round(base_war, 2),
            "position_scarcity": round(scarcity, 2),
            "star_multiplier": round(star_mult, 2),
            "rating_bonus": round(rating_bonus, 2),
            "school_tier": tier_name,
            "school_multiplier": round(school_mult, 2),
            "measurables_factor": round(measurables_mult, 2),
            "experience_factor": round(experience_mult, 2),
            "nil_bonus": round(nil_bonus, 2),
        }
    }


# =============================================================================
# TEAM PORTAL IMPACT SCORING
# =============================================================================

def calculate_team_portal_score(
    incoming_players: pd.DataFrame,
    outgoing_players: pd.DataFrame = None,
    team_name: str = None
) -> Dict[str, Any]:
    """
    Calculate Portal IQ's proprietary team portal impact score.

    Considers:
    - Sum of incoming player WAR
    - Net WAR change (incoming - outgoing)
    - Positional balance (filling needs vs redundancy)
    - Star quality distribution
    - NIL investment efficiency

    Returns comprehensive team portal analysis.
    """
    if incoming_players.empty:
        return {
            "portal_score": 0,
            "war_added": 0,
            "net_war": 0,
            "efficiency": 0,
            "grade": "N/A",
            "breakdown": {}
        }

    # Calculate WAR for each incoming player
    incoming_wars = []
    total_nil = 0
    position_counts = {}
    star_counts = {5: 0, 4: 0, 3: 0, 2: 0}

    for _, player in incoming_players.iterrows():
        war_result = calculate_player_war(
            position=player.get("position"),
            stars=player.get("stars"),
            rating=player.get("overall_rating"),
            nil_value=player.get("portaliq_value") or player.get("nil_value", 0),
            destination_school=team_name,
            height=player.get("height_inches"),
            weight=player.get("weight"),
            year=player.get("year"),
            is_predicted_nil=player.get("is_predicted", True)
        )
        incoming_wars.append(war_result["war"])

        # Track position distribution
        pos = player.get("position", "ATH")
        position_counts[pos] = position_counts.get(pos, 0) + 1

        # Track star distribution
        stars = int(player.get("stars", 3)) if pd.notna(player.get("stars")) else 3
        if stars in star_counts:
            star_counts[stars] += 1

        # Track NIL investment
        nil_val = player.get("portaliq_value") or player.get("nil_value", 0) or 0
        total_nil += nil_val

    total_war_in = sum(incoming_wars)
    avg_war_in = np.mean(incoming_wars) if incoming_wars else 0

    # Calculate outgoing WAR if provided
    total_war_out = 0
    if outgoing_players is not None and not outgoing_players.empty:
        for _, player in outgoing_players.iterrows():
            war_result = calculate_player_war(
                position=player.get("position"),
                stars=player.get("stars"),
                rating=player.get("overall_rating"),
                nil_value=player.get("nil_value", 0),
                is_predicted_nil=True
            )
            total_war_out += war_result["war"]

    net_war = total_war_in - total_war_out

    # Position balance score (diversification is good)
    num_positions = len(position_counts)
    max_position_count = max(position_counts.values()) if position_counts else 0
    position_balance = min(1.0, num_positions / 8) * (1 - (max_position_count / len(incoming_players) * 0.3))

    # Star quality score
    star_quality = (
        star_counts.get(5, 0) * 1.0 +
        star_counts.get(4, 0) * 0.6 +
        star_counts.get(3, 0) * 0.3 +
        star_counts.get(2, 0) * 0.1
    ) / max(1, len(incoming_players))

    # NIL efficiency (WAR per dollar spent)
    nil_efficiency = (total_war_in / (total_nil / 100000)) if total_nil > 0 else 0

    # Calculate composite score (0-100 scale)
    raw_score = (
        total_war_in * 8 +          # WAR is main driver
        net_war * 5 +               # Net improvement bonus
        position_balance * 15 +     # Balanced roster
        star_quality * 20 +         # Quality of players
        min(nil_efficiency * 5, 15) # Efficient spending
    )

    portal_score = min(100, max(0, raw_score))

    # Grade assignment
    if portal_score >= 85:
        grade = "A+"
    elif portal_score >= 75:
        grade = "A"
    elif portal_score >= 65:
        grade = "B+"
    elif portal_score >= 55:
        grade = "B"
    elif portal_score >= 45:
        grade = "C+"
    elif portal_score >= 35:
        grade = "C"
    else:
        grade = "D"

    return {
        "portal_score": round(portal_score, 1),
        "war_added": round(total_war_in, 2),
        "war_lost": round(total_war_out, 2),
        "net_war": round(net_war, 2),
        "avg_war_per_transfer": round(avg_war_in, 2),
        "total_nil_invested": total_nil,
        "nil_efficiency": round(nil_efficiency, 3),
        "grade": grade,
        "breakdown": {
            "transfers_in": len(incoming_players),
            "position_balance": round(position_balance, 2),
            "star_quality": round(star_quality, 2),
            "star_distribution": star_counts,
            "position_distribution": position_counts,
        }
    }


# =============================================================================
# TRANSFER VALUE ANALYSIS
# =============================================================================

def analyze_transfer_value(
    player_war: float,
    nil_value: float,
    position: str
) -> Dict[str, Any]:
    """
    Analyze the value proposition of a transfer.

    Returns:
    - Cost per WAR
    - Value rating (overpay, fair, bargain)
    - ROI projection
    """
    if not nil_value or nil_value <= 0 or not player_war or player_war <= 0:
        return {
            "cost_per_war": 0,
            "value_rating": "unknown",
            "roi_projection": "N/A",
            "market_comparison": "insufficient data"
        }

    cost_per_war = nil_value / player_war

    # Position-adjusted fair value per WAR
    position_fair_value = {
        "QB": 800000,
        "WR": 400000,
        "RB": 350000,
        "EDGE": 450000,
        "CB": 380000,
        "OT": 350000,
        "LB": 320000,
        "S": 300000,
        "TE": 320000,
        "DT": 300000,
    }

    fair_value = position_fair_value.get(position, 300000)

    # Determine value rating
    ratio = cost_per_war / fair_value

    if ratio <= 0.6:
        value_rating = "exceptional_value"
        roi_projection = "High ROI - significantly undervalued"
    elif ratio <= 0.85:
        value_rating = "good_value"
        roi_projection = "Positive ROI - below market rate"
    elif ratio <= 1.15:
        value_rating = "fair_value"
        roi_projection = "Market rate - standard ROI expected"
    elif ratio <= 1.4:
        value_rating = "slight_overpay"
        roi_projection = "Marginal ROI - slightly above market"
    else:
        value_rating = "significant_overpay"
        roi_projection = "Negative ROI - premium price for talent"

    return {
        "cost_per_war": round(cost_per_war, 0),
        "fair_value_per_war": fair_value,
        "value_ratio": round(ratio, 2),
        "value_rating": value_rating,
        "roi_projection": roi_projection,
        "market_comparison": f"{'Below' if ratio < 1 else 'Above'} market by {abs(1-ratio)*100:.0f}%"
    }


# =============================================================================
# IMPACT PROJECTION
# =============================================================================

def project_team_improvement(
    player_war: float,
    current_wins: float = None,
    team_tier: str = "rising"
) -> Dict[str, Any]:
    """
    Project how a player addition impacts team performance.

    Considers diminishing returns for already-good teams.
    """
    # Tier-based win expectations
    tier_baseline_wins = {
        "elite": 10,
        "power": 8,
        "rising": 6,
        "developmental": 4,
    }

    baseline = tier_baseline_wins.get(team_tier, 6)
    current = current_wins if current_wins else baseline

    # Diminishing returns for good teams
    # A 10-win team adding 2 WAR doesn't get +2 wins (ceiling effect)
    if current >= 10:
        diminishing_factor = 0.6
    elif current >= 8:
        diminishing_factor = 0.8
    else:
        diminishing_factor = 1.0

    projected_improvement = player_war * diminishing_factor

    return {
        "current_baseline": current,
        "projected_wins_added": round(projected_improvement, 1),
        "new_projected_wins": round(min(13, current + projected_improvement), 1),
        "diminishing_factor": diminishing_factor,
        "playoff_impact": "Significant" if projected_improvement >= 1.5 else "Moderate" if projected_improvement >= 0.8 else "Marginal"
    }


# =============================================================================
# HELPER FOR ENRICHING DATAFRAMES
# =============================================================================

def enrich_with_war(df: pd.DataFrame, school_col: str = "destination_school") -> pd.DataFrame:
    """
    Add Portal IQ WAR calculations to a DataFrame of players.
    """
    if df.empty:
        return df

    war_data = []
    for _, row in df.iterrows():
        result = calculate_player_war(
            position=row.get("position"),
            stars=row.get("stars"),
            rating=row.get("overall_rating"),
            nil_value=row.get("portaliq_value") or row.get("nil_value", 0),
            destination_school=row.get(school_col),
            height=row.get("height_inches"),
            weight=row.get("weight"),
            year=row.get("year"),
            is_predicted_nil=row.get("is_predicted", True)
        )
        war_data.append(result)

    df = df.copy()
    df["portaliq_war"] = [w["war"] for w in war_data]
    df["portaliq_war_low"] = [w["war_low"] for w in war_data]
    df["portaliq_war_high"] = [w["war_high"] for w in war_data]
    df["war_confidence"] = [w["confidence"] for w in war_data]

    return df
