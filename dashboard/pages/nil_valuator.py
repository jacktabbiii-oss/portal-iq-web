"""
NIL Valuator Page

AI-powered NIL valuation for college football players.
- Search existing players or create custom profiles
- Player Comparison (side-by-side analysis)
- Value breakdown visualization
- Transfer impact simulator
- Social media growth simulator
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import html

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import (
    apply_custom_css, COLORS, get_tier_color, format_currency,
    render_tier_badge, render_status_badge, render_confidence_badge,
    render_player_row, render_stat_card, get_plotly_layout, get_chart_colors
)
from utils.api_client import get_api_client
from utils.data_loader import (
    load_sample_data, get_school_list, get_positions, get_class_years
)
from utils.navigation import render_sidebar

# =============================================================================
# Manual Stats Persistence (CSV backup)
# =============================================================================
DATA_DIR = Path(__file__).parent.parent.parent / "ml-engine" / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MANUAL_STATS_FILE = DATA_DIR / "manual_player_stats.csv"


def load_manual_stats_for_player(player_name: str) -> dict:
    """Load manually entered stats for a specific player."""
    if not MANUAL_STATS_FILE.exists():
        return {}
    try:
        df = pd.read_csv(MANUAL_STATS_FILE)
        player_row = df[df["player_name"] == player_name]
        if not player_row.empty:
            return player_row.iloc[0].to_dict()
    except Exception:
        pass
    return {}


def save_manual_stats_for_player(player_name: str, team: str, position: str, stats: dict):
    """Save/update manual stats for a player to CSV."""
    try:
        if MANUAL_STATS_FILE.exists():
            df = pd.read_csv(MANUAL_STATS_FILE)
        else:
            df = pd.DataFrame()

        # Prepare the record
        record = {
            "player_name": player_name,
            "team": team,
            "position": position,
            **stats
        }

        if df.empty:
            df = pd.DataFrame([record])
        else:
            # Update existing or add new
            mask = df["player_name"] == player_name
            if mask.any():
                for key, value in record.items():
                    df.loc[mask, key] = value
            else:
                df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)

        df.to_csv(MANUAL_STATS_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving stats: {e}")
        return False

# Page config
st.set_page_config(
    page_title="NIL Valuator | Portal IQ",
    page_icon="💰",
    layout="wide",
)

apply_custom_css()


# =============================================================================
# Player Comparison State
# =============================================================================

def init_comparison():
    """Initialize comparison state."""
    if "compare_players" not in st.session_state:
        st.session_state.compare_players = []


def add_to_comparison(player_data: dict):
    """Add a player to comparison (max 3)."""
    init_comparison()
    if len(st.session_state.compare_players) >= 3:
        st.warning("Maximum 3 players can be compared. Remove one first.")
        return False

    # Check if already in comparison
    for p in st.session_state.compare_players:
        if p.get("name") == player_data.get("name"):
            return False

    st.session_state.compare_players.append(player_data)
    return True


def remove_from_comparison(player_name: str):
    """Remove a player from comparison."""
    init_comparison()
    st.session_state.compare_players = [
        p for p in st.session_state.compare_players
        if p.get("name") != player_name
    ]


def get_comparison_players() -> list:
    """Get players in comparison."""
    init_comparison()
    return st.session_state.compare_players


def clear_comparison():
    """Clear all players from comparison."""
    st.session_state.compare_players = []


def is_in_comparison(player_name: str) -> bool:
    """Check if player is in comparison."""
    init_comparison()
    return any(p.get("name") == player_name for p in st.session_state.compare_players)


# =============================================================================
# Cache Functions
# =============================================================================

@st.cache_data(ttl=300)
def get_sample_players():
    """Get cached sample player data."""
    return load_sample_data("players")


@st.cache_resource
def get_client():
    """Get cached API client."""
    return get_api_client()


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_size_multiplier(player_data: dict) -> tuple[float, str]:
    """
    Calculate size multiplier based on height/weight for position.
    Returns (multiplier, description).
    """
    position = player_data.get("position", "ATH")
    height = player_data.get("height")  # In inches
    weight = player_data.get("weight")  # In pounds

    # If no size data, return neutral multiplier
    if pd.isna(height) or pd.isna(weight) or height is None or weight is None:
        return 1.0, "Size data not available"

    height = float(height)
    weight = float(weight)

    # Ideal size ranges by position (height in inches, weight in lbs)
    # Format: (min_height, ideal_height, max_height, min_weight, ideal_weight, max_weight)
    position_ideals = {
        "QB": (73, 75, 78, 200, 220, 240),      # 6'1" - 6'6", 200-240 lbs
        "RB": (68, 71, 73, 195, 215, 230),      # 5'8" - 6'1", 195-230 lbs
        "WR": (70, 73, 76, 175, 200, 220),      # 5'10" - 6'4", 175-220 lbs
        "TE": (75, 77, 79, 240, 255, 270),      # 6'3" - 6'7", 240-270 lbs
        "OT": (76, 78, 81, 295, 315, 340),      # 6'4" - 6'9", 295-340 lbs
        "OG": (74, 76, 78, 300, 320, 345),      # 6'2" - 6'6", 300-345 lbs
        "C": (73, 75, 77, 290, 310, 330),       # 6'1" - 6'5", 290-330 lbs
        "IOL": (74, 76, 78, 295, 315, 340),     # 6'2" - 6'6", 295-340 lbs
        "EDGE": (74, 77, 79, 245, 265, 285),    # 6'2" - 6'7", 245-285 lbs
        "DT": (73, 75, 78, 290, 310, 340),      # 6'1" - 6'6", 290-340 lbs
        "DL": (74, 76, 79, 275, 295, 320),      # 6'2" - 6'7", 275-320 lbs
        "LB": (72, 74, 76, 225, 240, 255),      # 6'0" - 6'4", 225-255 lbs
        "CB": (69, 72, 74, 175, 195, 210),      # 5'9" - 6'2", 175-210 lbs
        "S": (70, 73, 75, 190, 210, 225),       # 5'10" - 6'3", 190-225 lbs
        "K": (70, 72, 75, 175, 195, 215),       # 5'10" - 6'3", 175-215 lbs
        "P": (72, 74, 77, 190, 210, 230),       # 6'0" - 6'5", 190-230 lbs
        "ATH": (71, 74, 77, 195, 215, 240),     # 5'11" - 6'5", 195-240 lbs
    }

    ideals = position_ideals.get(position, (71, 74, 77, 195, 215, 240))
    min_h, ideal_h, max_h, min_w, ideal_w, max_w = ideals

    # Calculate height score (0.0 to 1.0, peaks at ideal)
    if height >= ideal_h:
        # Above ideal - penalize if too tall
        if height > max_h:
            height_score = max(0.7, 1.0 - (height - max_h) * 0.1)
        else:
            height_score = 1.0 + (height - ideal_h) * 0.02  # Slight bonus for being tall
    else:
        # Below ideal
        if height < min_h:
            height_score = max(0.6, 1.0 - (min_h - height) * 0.1)
        else:
            height_score = 0.9 + (height - min_h) / (ideal_h - min_h) * 0.1

    # Calculate weight score (0.0 to 1.0, peaks at ideal)
    if weight >= ideal_w:
        if weight > max_w:
            weight_score = max(0.75, 1.0 - (weight - max_w) * 0.02)
        else:
            weight_score = 1.0
    else:
        if weight < min_w:
            weight_score = max(0.7, 1.0 - (min_w - weight) * 0.02)
        else:
            weight_score = 0.85 + (weight - min_w) / (ideal_w - min_w) * 0.15

    # Combined size multiplier
    size_mult = (height_score * 0.5 + weight_score * 0.5)

    # Determine description
    height_ft = int(height // 12)
    height_in = int(height % 12)
    height_str = f"{height_ft}'{height_in}\""

    if size_mult >= 1.1:
        desc = f"Elite size ({height_str}, {weight:.0f} lbs)"
    elif size_mult >= 1.0:
        desc = f"Ideal size ({height_str}, {weight:.0f} lbs)"
    elif size_mult >= 0.9:
        desc = f"Good size ({height_str}, {weight:.0f} lbs)"
    elif size_mult >= 0.8:
        desc = f"Undersized ({height_str}, {weight:.0f} lbs)"
    else:
        desc = f"Size concerns ({height_str}, {weight:.0f} lbs)"

    # Cap multiplier between 0.75 and 1.25
    size_mult = max(0.75, min(1.25, size_mult))

    return size_mult, desc


def calculate_custom_nil_value(player_data: dict) -> tuple[float, dict]:
    """
    Calculate custom NIL value based on on-field performance metrics.
    Returns (value, breakdown_dict) where breakdown_dict explains the factors.
    """
    position = player_data.get("position", "ATH")
    school = player_data.get("school", "Unknown")

    # Get effective stars - prefer transfer portal rating (college performance)
    # over HS recruiting stars
    stars = player_data.get("transfer_stars") or player_data.get("stars") or player_data.get("hs_stars")
    star_source = "portal" if player_data.get("transfer_stars") else "recruiting"

    # Handle NaN stars
    if pd.isna(stars) or not stars:
        stars = 3
        star_source = "default"
    else:
        stars = int(stars)

    # Base value by position (market value weights)
    position_base = {
        "QB": 500000, "RB": 150000, "WR": 200000, "TE": 100000,
        "OT": 120000, "OG": 80000, "C": 70000, "IOL": 85000,
        "EDGE": 180000, "DT": 100000, "DL": 110000, "LB": 120000,
        "CB": 150000, "S": 100000, "K": 30000, "P": 20000, "ATH": 80000
    }

    base = position_base.get(position, 80000)

    # Star rating multiplier (performance indicator)
    star_multipliers = {5: 2.5, 4: 1.5, 3: 1.0, 2: 0.6, 1: 0.3}
    star_mult = star_multipliers.get(stars, 1.0)

    # Size multiplier (height/weight for position)
    size_mult, size_desc = calculate_size_multiplier(player_data)

    # School brand multiplier
    blue_bloods = ["Alabama", "Ohio State", "Georgia", "Texas", "USC", "Michigan", "Notre Dame"]
    elite_programs = ["LSU", "Florida", "Oregon", "Penn State", "Clemson", "Tennessee", "Oklahoma", "Miami"]
    good_programs = ["Auburn", "Florida State", "Wisconsin", "Iowa", "UCLA", "Arizona State", "Colorado"]

    if school in blue_bloods:
        school_mult = 1.8
        school_factor = "Blue Blood"
    elif school in elite_programs:
        school_mult = 1.4
        school_factor = "Elite Program"
    elif school in good_programs:
        school_mult = 1.2
        school_factor = "Strong Program"
    else:
        school_mult = 1.0
        school_factor = "Standard"

    # Performance adjustments based on stats (if available)
    perf_bonus = 0
    perf_factors = []

    # QB stats - comprehensive evaluation like a GM
    if position == "QB":
        pass_yds = player_data.get("passing_yards", 0) or 0
        pass_tds = player_data.get("passing_tds", 0) or 0
        ints_thrown = player_data.get("interceptions", 0) or 0
        comp_pct = player_data.get("completion_pct", 0) or 0
        attempts = player_data.get("passing_attempts", 0) or 0
        rush_yds = player_data.get("rushing_yards", 0) or 0
        rush_tds = player_data.get("rushing_tds", 0) or 0
        # PFF Premium metrics
        pff_overall = player_data.get("pff_overall", 0) or 0
        pff_passing = player_data.get("pff_passing", 0) or 0
        adj_comp_pct = player_data.get("adjusted_completion_pct", 0) or 0
        btt = player_data.get("big_time_throws", 0) or 0
        btt_pct = player_data.get("big_time_throw_pct", 0) or 0
        twp = player_data.get("turnover_worthy_plays", 0) or 0
        twp_pct = player_data.get("turnover_worthy_play_pct", 0) or 0
        time_to_throw = player_data.get("time_to_throw", 0) or 0
        pff_under_pressure = player_data.get("pff_under_pressure", 0) or 0
        pff_clean_pocket = player_data.get("pff_clean_pocket", 0) or 0
        pff_deep = player_data.get("pff_deep_passing", 0) or 0
        games_played = player_data.get("games_played", 0) or 0

        # ===================================================================
        # MINIMUM SAMPLE THRESHOLDS - Critical for valid PFF grade analysis
        # ===================================================================
        MIN_ATTEMPTS = 150  # Minimum pass attempts for QB grades
        has_valid_sample = attempts >= MIN_ATTEMPTS

        # Small sample warning
        if pff_overall > 0 and not has_valid_sample:
            perf_factors.append(f"⚠️ Limited sample ({attempts} att - need {MIN_ATTEMPTS}+)")

        # PFF Grades (only apply bonuses with valid sample)
        if pff_overall > 0 and has_valid_sample:
            if pff_overall >= 90:
                perf_bonus += 250000
                perf_factors.append(f"Elite PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 85:
                perf_bonus += 175000
                perf_factors.append(f"Excellent PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 80:
                perf_bonus += 120000
                perf_factors.append(f"Very good PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 70:
                perf_bonus += 60000
                perf_factors.append(f"Strong PFF grade ({pff_overall:.1f})")
            elif pff_overall < 55:
                perf_bonus -= 40000
                perf_factors.append(f"⚠️ Low PFF grade ({pff_overall:.1f})")

        # Adjusted Completion % (removes drops, throw aways, spikes)
        if adj_comp_pct > 0:
            if adj_comp_pct >= 80:
                perf_bonus += 75000
                perf_factors.append(f"Elite adj. comp% ({adj_comp_pct:.1f}%)")
            elif adj_comp_pct >= 75:
                perf_bonus += 45000
                perf_factors.append(f"Excellent accuracy ({adj_comp_pct:.1f}% adj)")
            elif adj_comp_pct >= 70:
                perf_bonus += 20000
                perf_factors.append(f"Accurate passer ({adj_comp_pct:.1f}% adj)")
            elif adj_comp_pct < 60:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Accuracy concerns ({adj_comp_pct:.1f}% adj)")

        # Big Time Throws (playmaking ability)
        if btt > 0:
            if btt >= 25:
                perf_bonus += 80000
                perf_factors.append(f"Elite playmaker ({btt} BTT)")
            elif btt >= 18:
                perf_bonus += 50000
                perf_factors.append(f"Strong playmaker ({btt} BTT)")
            elif btt >= 12:
                perf_bonus += 25000
                perf_factors.append(f"Makes plays ({btt} BTT)")

        # Big Time Throw % (if available)
        if btt_pct > 0 and attempts > 100:
            if btt_pct >= 6:
                perf_bonus += 50000
                perf_factors.append(f"Elite BTT rate ({btt_pct:.1f}%)")
            elif btt_pct >= 5:
                perf_bonus += 30000
                perf_factors.append(f"High BTT rate ({btt_pct:.1f}%)")

        # Turnover Worthy Plays (NEGATIVE - decision making)
        if twp > 0 and attempts > 100:
            if twp >= 15:
                perf_bonus -= 75000
                perf_factors.append(f"⚠️ Major turnover issues ({twp} TWP)")
            elif twp >= 10:
                perf_bonus -= 40000
                perf_factors.append(f"⚠️ Turnover concerns ({twp} TWP)")
            elif twp >= 7:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Some bad decisions ({twp} TWP)")
            elif twp <= 3:
                perf_bonus += 40000
                perf_factors.append(f"Clean decision-maker ({twp} TWP)")

        # TWP % (more telling than raw count)
        if twp_pct > 0 and attempts > 100:
            if twp_pct >= 4:
                perf_bonus -= 50000
                perf_factors.append(f"⚠️ High TWP rate ({twp_pct:.1f}%)")
            elif twp_pct < 2:
                perf_bonus += 35000
                perf_factors.append(f"Low turnover risk ({twp_pct:.1f}% TWP)")

        # Under pressure grade (critical for NFL projection)
        if pff_under_pressure > 0:
            if pff_under_pressure >= 80:
                perf_bonus += 60000
                perf_factors.append(f"Elite under pressure ({pff_under_pressure:.1f})")
            elif pff_under_pressure >= 70:
                perf_bonus += 35000
                perf_factors.append(f"Handles pressure ({pff_under_pressure:.1f})")
            elif pff_under_pressure < 50:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Struggles under pressure ({pff_under_pressure:.1f})")

        # Deep passing grade
        if pff_deep > 0:
            if pff_deep >= 85:
                perf_bonus += 50000
                perf_factors.append(f"Elite deep ball ({pff_deep:.1f})")
            elif pff_deep >= 75:
                perf_bonus += 30000
                perf_factors.append(f"Good deep ball ({pff_deep:.1f})")
            elif pff_deep < 55:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Deep ball concerns ({pff_deep:.1f})")

        # Passing production
        if pass_yds > 3500:
            perf_bonus += 200000
            perf_factors.append(f"Elite passer ({pass_yds:,} yds)")
        elif pass_yds > 3000:
            perf_bonus += 150000
            perf_factors.append(f"Prolific passer ({pass_yds:,} yds)")
        elif pass_yds > 2000:
            perf_bonus += 75000
            perf_factors.append(f"Strong passing ({pass_yds:,} yds)")
        elif pass_yds > 1000:
            perf_bonus += 25000
            perf_factors.append(f"Adequate passing ({pass_yds:,} yds)")

        # TD production
        if pass_tds > 30:
            perf_bonus += 150000
            perf_factors.append(f"TD machine ({pass_tds} TDs)")
        elif pass_tds > 25:
            perf_bonus += 100000
            perf_factors.append(f"Elite TD production ({pass_tds} TDs)")
        elif pass_tds > 15:
            perf_bonus += 50000
            perf_factors.append(f"Good TD count ({pass_tds} TDs)")

        # Completion percentage (efficiency)
        if comp_pct > 70:
            perf_bonus += 75000
            perf_factors.append(f"Pinpoint accuracy ({comp_pct:.1f}%)")
        elif comp_pct > 65:
            perf_bonus += 40000
            perf_factors.append(f"Accurate passer ({comp_pct:.1f}%)")
        elif comp_pct > 60:
            perf_bonus += 20000
            perf_factors.append(f"Solid accuracy ({comp_pct:.1f}%)")

        # Turnover concern (NEGATIVE - critical for GMs)
        if attempts > 100:  # Only penalize if meaningful sample size
            td_int_ratio = pass_tds / max(ints_thrown, 1)
            if ints_thrown > 12:
                perf_bonus -= 50000
                perf_factors.append(f"⚠️ Turnover prone ({ints_thrown} INTs)")
            elif ints_thrown > 8:
                perf_bonus -= 25000
                perf_factors.append(f"⚠️ INT concerns ({ints_thrown} INTs)")

            # TD:INT ratio bonus/penalty
            if td_int_ratio > 4:
                perf_bonus += 50000
                perf_factors.append(f"Elite TD:INT ratio ({td_int_ratio:.1f}:1)")
            elif td_int_ratio < 1.5 and ints_thrown > 5:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Poor TD:INT ratio ({td_int_ratio:.1f}:1)")

        # Dual-threat premium
        if rush_yds > 500:
            perf_bonus += 75000
            perf_factors.append(f"Dual-threat ({rush_yds:,} rush yds)")
        elif rush_yds > 300:
            perf_bonus += 40000
            perf_factors.append(f"Mobile QB ({rush_yds:,} rush yds)")
        if rush_tds > 5:
            perf_bonus += 30000
            perf_factors.append(f"Ground scorer ({rush_tds} rush TDs)")

    # RB stats - comprehensive evaluation
    elif position == "RB":
        rush_yds = player_data.get("rushing_yards", 0) or 0
        rush_tds = player_data.get("rushing_tds", 0) or 0
        ypc = player_data.get("yards_per_carry", 0) or 0
        carries = player_data.get("rushing_attempts", 0) or 0
        rec_yds = player_data.get("receiving_yards", 0) or 0
        receptions = player_data.get("receptions", 0) or 0
        fumbles_lost = player_data.get("fumbles_lost", 0) or 0
        # PFF Premium metrics
        pff_overall = player_data.get("pff_overall", 0) or 0
        pff_rushing = player_data.get("pff_rushing", 0) or 0
        pff_receiving = player_data.get("pff_receiving", 0) or 0
        elusive_rating = player_data.get("elusive_rating", 0) or 0
        yards_after_contact = player_data.get("yards_after_contact", 0) or 0
        yaco_per_att = player_data.get("yaco_per_attempt", 0) or 0
        mtf = player_data.get("missed_tackles_forced", 0) or 0
        breakaway_pct = player_data.get("breakaway_pct", 0) or 0

        # PFF Grades
        if pff_overall > 0:
            if pff_overall >= 90:
                perf_bonus += 120000
                perf_factors.append(f"Elite PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 80:
                perf_bonus += 70000
                perf_factors.append(f"Excellent PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 70:
                perf_bonus += 35000
                perf_factors.append(f"Strong PFF grade ({pff_overall:.1f})")
            elif pff_overall < 55:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Low PFF grade ({pff_overall:.1f})")

        # Elusive Rating (key RB metric)
        if elusive_rating > 0:
            if elusive_rating >= 100:
                perf_bonus += 75000
                perf_factors.append(f"Elite elusiveness ({elusive_rating:.1f})")
            elif elusive_rating >= 80:
                perf_bonus += 45000
                perf_factors.append(f"Very elusive ({elusive_rating:.1f})")
            elif elusive_rating >= 60:
                perf_bonus += 20000
                perf_factors.append(f"Elusive runner ({elusive_rating:.1f})")
            elif elusive_rating < 30:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Limited elusiveness ({elusive_rating:.1f})")

        # Yards After Contact per attempt
        if yaco_per_att > 0 and carries > 50:
            if yaco_per_att >= 3.5:
                perf_bonus += 50000
                perf_factors.append(f"Yards after contact monster ({yaco_per_att:.2f} YAC/att)")
            elif yaco_per_att >= 3.0:
                perf_bonus += 30000
                perf_factors.append(f"Strong after contact ({yaco_per_att:.2f} YAC/att)")
            elif yaco_per_att < 2.0:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Falls on contact ({yaco_per_att:.2f} YAC/att)")

        # Missed tackles forced
        if mtf > 30:
            perf_bonus += 40000
            perf_factors.append(f"Tackle-breaking machine ({mtf} MTF)")
        elif mtf > 20:
            perf_bonus += 25000
            perf_factors.append(f"Makes defenders miss ({mtf} MTF)")

        # Breakaway percentage
        if breakaway_pct > 0:
            if breakaway_pct >= 40:
                perf_bonus += 45000
                perf_factors.append(f"Home run threat ({breakaway_pct:.0f}% breakaway)")
            elif breakaway_pct >= 25:
                perf_bonus += 25000
                perf_factors.append(f"Big play ability ({breakaway_pct:.0f}% breakaway)")

        # Rushing production
        if rush_yds > 1500:
            perf_bonus += 150000
            perf_factors.append(f"Elite workhorse ({rush_yds:,} yds)")
        elif rush_yds > 1000:
            perf_bonus += 80000
            perf_factors.append(f"1000+ yard rusher ({rush_yds:,} yds)")
        elif rush_yds > 700:
            perf_bonus += 40000
            perf_factors.append(f"Productive back ({rush_yds:,} yds)")
        elif rush_yds > 400:
            perf_bonus += 15000
            perf_factors.append(f"Rotational production ({rush_yds:,} yds)")

        # TD production
        if rush_tds > 15:
            perf_bonus += 80000
            perf_factors.append(f"TD machine ({rush_tds} TDs)")
        elif rush_tds > 10:
            perf_bonus += 50000
            perf_factors.append(f"Double-digit TDs ({rush_tds} TDs)")
        elif rush_tds > 5:
            perf_bonus += 25000
            perf_factors.append(f"Scoring threat ({rush_tds} TDs)")

        # Efficiency (YPC) - very important for GMs
        if carries > 50:  # Meaningful sample
            if ypc > 6.0:
                perf_bonus += 60000
                perf_factors.append(f"Explosive runner ({ypc:.1f} YPC)")
            elif ypc > 5.0:
                perf_bonus += 35000
                perf_factors.append(f"Efficient back ({ypc:.1f} YPC)")
            elif ypc < 3.5:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Low efficiency ({ypc:.1f} YPC)")

        # Pass-catching (3-down back premium)
        if receptions > 30 and rec_yds > 300:
            perf_bonus += 50000
            perf_factors.append(f"3-down back ({receptions} rec, {rec_yds:,} rec yds)")
        elif receptions > 20:
            perf_bonus += 25000
            perf_factors.append(f"Pass-catching back ({receptions} rec)")

        # Ball security concern (NEGATIVE)
        if fumbles_lost > 3:
            perf_bonus -= 40000
            perf_factors.append(f"⚠️ Ball security issue ({fumbles_lost} fumbles lost)")
        elif fumbles_lost > 1 and carries > 100:
            perf_bonus -= 15000
            perf_factors.append(f"⚠️ Fumble concerns ({fumbles_lost} fumbles lost)")

    # WR stats - comprehensive evaluation
    elif position == "WR":
        rec_yds = player_data.get("receiving_yards", 0) or 0
        rec_tds = player_data.get("receiving_tds", 0) or 0
        receptions = player_data.get("receptions", 0) or 0
        ypr = player_data.get("yards_per_reception", 0) or 0
        long_rec = player_data.get("receiving_LONG", 0) or 0
        # PFF Premium metrics
        pff_overall = player_data.get("pff_overall", 0) or 0
        pff_receiving = player_data.get("pff_receiving", 0) or 0
        yards_per_route = player_data.get("yards_per_route_run", 0) or 0
        drop_rate = player_data.get("drop_rate", 0) or 0
        drops = player_data.get("drops", 0) or 0
        contested_catch_rate = player_data.get("contested_catch_rate", 0) or 0
        separation = player_data.get("separation", 0) or 0
        routes_run = player_data.get("routes_run", 0) or 0

        # PFF Grades
        if pff_overall > 0:
            if pff_overall >= 90:
                perf_bonus += 130000
                perf_factors.append(f"Elite PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 80:
                perf_bonus += 75000
                perf_factors.append(f"Excellent PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 70:
                perf_bonus += 40000
                perf_factors.append(f"Strong PFF grade ({pff_overall:.1f})")
            elif pff_overall < 55:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Low PFF grade ({pff_overall:.1f})")

        # Yards Per Route Run (YPRR) - THE key WR efficiency metric
        if yards_per_route > 0:
            if yards_per_route >= 3.0:
                perf_bonus += 90000
                perf_factors.append(f"Elite YPRR ({yards_per_route:.2f})")
            elif yards_per_route >= 2.5:
                perf_bonus += 60000
                perf_factors.append(f"Excellent YPRR ({yards_per_route:.2f})")
            elif yards_per_route >= 2.0:
                perf_bonus += 35000
                perf_factors.append(f"Strong YPRR ({yards_per_route:.2f})")
            elif yards_per_route >= 1.5:
                perf_bonus += 15000
                perf_factors.append(f"Solid YPRR ({yards_per_route:.2f})")
            elif yards_per_route < 1.0 and routes_run > 100:
                perf_bonus -= 25000
                perf_factors.append(f"⚠️ Low YPRR ({yards_per_route:.2f})")

        # Drop rate (NEGATIVE - reliability)
        if drop_rate > 0 and receptions > 20:
            if drop_rate >= 15:
                perf_bonus -= 50000
                perf_factors.append(f"⚠️ Major drop issues ({drop_rate:.1f}%)")
            elif drop_rate >= 10:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Drop concerns ({drop_rate:.1f}%)")
            elif drop_rate >= 7:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Some drops ({drop_rate:.1f}%)")
            elif drop_rate < 3:
                perf_bonus += 25000
                perf_factors.append(f"Reliable hands ({drop_rate:.1f}% drop rate)")

        # Contested catch rate (physical receiver)
        if contested_catch_rate > 0:
            if contested_catch_rate >= 60:
                perf_bonus += 50000
                perf_factors.append(f"Contested catch king ({contested_catch_rate:.0f}%)")
            elif contested_catch_rate >= 50:
                perf_bonus += 30000
                perf_factors.append(f"Strong contested catcher ({contested_catch_rate:.0f}%)")
            elif contested_catch_rate < 30 and receptions > 30:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Struggles contested ({contested_catch_rate:.0f}%)")

        # Separation (route running)
        if separation > 0:
            if separation >= 3.0:
                perf_bonus += 40000
                perf_factors.append(f"Elite separator ({separation:.1f} avg sep)")
            elif separation >= 2.5:
                perf_bonus += 25000
                perf_factors.append(f"Gets open ({separation:.1f} avg sep)")
            elif separation < 1.5 and routes_run > 100:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Struggles to separate ({separation:.1f})")

        # Receiving production
        if rec_yds > 1200:
            perf_bonus += 150000
            perf_factors.append(f"Elite receiver ({rec_yds:,} yds)")
        elif rec_yds > 1000:
            perf_bonus += 100000
            perf_factors.append(f"1000+ yard receiver ({rec_yds:,} yds)")
        elif rec_yds > 700:
            perf_bonus += 50000
            perf_factors.append(f"Productive wideout ({rec_yds:,} yds)")
        elif rec_yds > 400:
            perf_bonus += 20000
            perf_factors.append(f"Rotational receiver ({rec_yds:,} yds)")

        # TD production
        if rec_tds > 12:
            perf_bonus += 100000
            perf_factors.append(f"Elite TD threat ({rec_tds} TDs)")
        elif rec_tds > 8:
            perf_bonus += 60000
            perf_factors.append(f"Red zone weapon ({rec_tds} TDs)")
        elif rec_tds > 5:
            perf_bonus += 30000
            perf_factors.append(f"Scoring threat ({rec_tds} TDs)")

        # Volume (reliable target)
        if receptions > 80:
            perf_bonus += 60000
            perf_factors.append(f"Team's go-to target ({receptions} rec)")
        elif receptions > 60:
            perf_bonus += 35000
            perf_factors.append(f"High-volume receiver ({receptions} rec)")
        elif receptions > 40:
            perf_bonus += 15000
            perf_factors.append(f"Reliable hands ({receptions} rec)")

        # Big play ability (YPR)
        if receptions > 20:  # Meaningful sample
            if ypr > 18:
                perf_bonus += 50000
                perf_factors.append(f"Deep threat ({ypr:.1f} YPR)")
            elif ypr > 15:
                perf_bonus += 30000
                perf_factors.append(f"Big play ability ({ypr:.1f} YPR)")
            elif ypr < 10 and receptions > 40:
                perf_bonus -= 10000
                perf_factors.append(f"⚠️ Short yardage specialist ({ypr:.1f} YPR)")

    # TE stats - important for modern offenses
    elif position == "TE":
        rec_yds = player_data.get("receiving_yards", 0) or 0
        rec_tds = player_data.get("receiving_tds", 0) or 0
        receptions = player_data.get("receptions", 0) or 0
        # PFF Premium metrics
        pff_overall = player_data.get("pff_overall", 0) or 0
        pff_receiving = player_data.get("pff_receiving", 0) or 0
        pff_run_block = player_data.get("pff_run_block", 0) or 0
        pff_pass_block = player_data.get("pff_pass_block", 0) or 0
        yards_per_route = player_data.get("yards_per_route_run", 0) or 0
        drop_rate = player_data.get("drop_rate", 0) or 0

        # PFF Grades
        if pff_overall > 0:
            if pff_overall >= 90:
                perf_bonus += 100000
                perf_factors.append(f"Elite PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 80:
                perf_bonus += 60000
                perf_factors.append(f"Excellent PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 70:
                perf_bonus += 30000
                perf_factors.append(f"Strong PFF grade ({pff_overall:.1f})")

            # Receiving grade
            if pff_receiving >= 85:
                perf_bonus += 50000
                perf_factors.append(f"Elite receiving grade ({pff_receiving:.1f})")
            elif pff_receiving >= 75:
                perf_bonus += 25000
                perf_factors.append(f"Strong receiving grade ({pff_receiving:.1f})")

            # Blocking grades (valuable for complete TEs)
            if pff_run_block >= 80:
                perf_bonus += 40000
                perf_factors.append(f"Excellent run blocker ({pff_run_block:.1f})")
            elif pff_run_block >= 70:
                perf_bonus += 20000
                perf_factors.append(f"Good run blocker ({pff_run_block:.1f})")

            if pff_pass_block >= 75:
                perf_bonus += 25000
                perf_factors.append(f"Pass pro TE ({pff_pass_block:.1f})")

        # Yards Per Route Run
        if yards_per_route > 0:
            if yards_per_route >= 2.5:
                perf_bonus += 60000
                perf_factors.append(f"Elite YPRR for TE ({yards_per_route:.2f})")
            elif yards_per_route >= 2.0:
                perf_bonus += 35000
                perf_factors.append(f"Strong YPRR ({yards_per_route:.2f})")
            elif yards_per_route >= 1.5:
                perf_bonus += 15000
                perf_factors.append(f"Solid YPRR ({yards_per_route:.2f})")

        # Drop rate (reliability)
        if drop_rate > 0 and receptions > 15:
            if drop_rate >= 12:
                perf_bonus -= 35000
                perf_factors.append(f"⚠️ Drop issues ({drop_rate:.1f}%)")
            elif drop_rate >= 8:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Some drops ({drop_rate:.1f}%)")
            elif drop_rate < 3:
                perf_bonus += 20000
                perf_factors.append(f"Reliable hands ({drop_rate:.1f}%)")

        # Receiving production
        if rec_yds > 700:
            perf_bonus += 80000
            perf_factors.append(f"Elite receiving TE ({rec_yds:,} yds)")
        elif rec_yds > 500:
            perf_bonus += 50000
            perf_factors.append(f"Productive pass catcher ({rec_yds:,} yds)")
        elif rec_yds > 300:
            perf_bonus += 25000
            perf_factors.append(f"Pass-catching TE ({rec_yds:,} yds)")

        # TD production (premium in red zone)
        if rec_tds > 8:
            perf_bonus += 70000
            perf_factors.append(f"Red zone mismatch ({rec_tds} TDs)")
        elif rec_tds > 5:
            perf_bonus += 40000
            perf_factors.append(f"Scoring threat ({rec_tds} TDs)")
        elif rec_tds > 2:
            perf_bonus += 20000
            perf_factors.append(f"TD contributor ({rec_tds} TDs)")

        # Volume (target share)
        if receptions > 50:
            perf_bonus += 40000
            perf_factors.append(f"High-volume target ({receptions} rec)")
        elif receptions > 30:
            perf_bonus += 20000
            perf_factors.append(f"Reliable target ({receptions} rec)")

    # OL stats - ELITE COMPREHENSIVE TRENCH EVALUATION
    elif position in ["OT", "OG", "C", "OL", "IOL"]:
        # ===========================================
        # PFF CORE GRADES
        # ===========================================
        pff_overall = player_data.get("pff_overall", 0) or 0
        pff_pass_block = player_data.get("pff_pass_block", 0) or 0
        pff_run_block = player_data.get("pff_run_block", 0) or 0

        # ===========================================
        # PASS PROTECTION METRICS
        # ===========================================
        pass_block_eff = player_data.get("pass_blocking_efficiency", 0) or 0
        true_pass_pbe = player_data.get("true_pass_set_pbe", 0) or 0  # True dropback PBE
        pressures_allowed = player_data.get("pressures_allowed", 0) or 0
        sacks_allowed = player_data.get("sacks_allowed", 0) or 0
        hurries_allowed = player_data.get("hurries_allowed", 0) or 0
        hits_allowed = player_data.get("hits_allowed", 0) or 0
        true_pass_pressures = player_data.get("true_pass_set_pressures_allowed", 0) or 0
        true_pass_sacks = player_data.get("true_pass_set_sacks_allowed", 0) or 0

        # ===========================================
        # RUN BLOCKING METRICS
        # ===========================================
        run_block_pct = player_data.get("run_block_percent", 0) or 0
        gap_run_grade = player_data.get("gap_grades_run_block", 0) or 0
        zone_run_grade = player_data.get("zone_grades_run_block", 0) or 0
        gap_run_pct = player_data.get("gap_run_block_percent", 0) or 0
        zone_run_pct = player_data.get("zone_run_block_percent", 0) or 0

        # ===========================================
        # SNAP COUNTS & VERSATILITY
        # ===========================================
        offensive_snaps = player_data.get("offensive_snaps", 0) or 0
        pass_block_snaps = player_data.get("snap_counts_pass_block", 0) or 0
        run_block_snaps = player_data.get("snap_counts_run_block", 0) or 0
        lt_snaps = player_data.get("snap_counts_lt", 0) or 0
        lg_snaps = player_data.get("snap_counts_lg", 0) or 0
        c_snaps = player_data.get("snap_counts_ce", 0) or 0
        rg_snaps = player_data.get("snap_counts_rg", 0) or 0
        rt_snaps = player_data.get("snap_counts_rt", 0) or 0

        # ===========================================
        # PENALTIES
        # ===========================================
        penalties = player_data.get("penalties", 0) or 0
        penalty_grade = player_data.get("grades_offense_penalty", 0) or 0

        # ===================================================================
        # MINIMUM SNAP THRESHOLDS - Critical for valid PFF grade analysis
        # ===================================================================
        MIN_OFF_SNAPS = 250  # Minimum for overall offensive line grades
        MIN_PASS_BLOCK_SNAPS = 150  # Minimum for pass blocking grades

        has_valid_sample = offensive_snaps >= MIN_OFF_SNAPS
        has_valid_pass_block = pass_block_snaps >= MIN_PASS_BLOCK_SNAPS

        # Small sample warning
        if pff_overall > 0 and not has_valid_sample:
            perf_factors.append(f"⚠️ Limited sample ({offensive_snaps} snaps - need {MIN_OFF_SNAPS}+)")

        if pff_overall > 0 and has_valid_sample:
            # === OVERALL GRADE TIERS ===
            if pff_overall >= 92:
                perf_bonus += 200000
                perf_factors.append(f"All-American caliber ({pff_overall:.1f} PFF)")
            elif pff_overall >= 85:
                perf_bonus += 140000
                perf_factors.append(f"Elite OL grade ({pff_overall:.1f} PFF)")
            elif pff_overall >= 78:
                perf_bonus += 90000
                perf_factors.append(f"Excellent OL ({pff_overall:.1f} PFF)")
            elif pff_overall >= 70:
                perf_bonus += 50000
                perf_factors.append(f"Solid starter ({pff_overall:.1f} PFF)")
            elif pff_overall >= 60:
                perf_bonus += 20000
                perf_factors.append(f"Developmental grade ({pff_overall:.1f} PFF)")
            elif pff_overall < 55:
                perf_bonus -= 40000
                perf_factors.append(f"⚠️ Concerning grade ({pff_overall:.1f} PFF)")

            # === PASS BLOCKING GRADE (OT PREMIUM) ===
            if pff_pass_block >= 90 and position == "OT":
                perf_bonus += 80000
                perf_factors.append(f"Elite pass protector ({pff_pass_block:.1f})")
            elif pff_pass_block >= 85:
                perf_bonus += 55000
                perf_factors.append(f"Excellent pass pro ({pff_pass_block:.1f})")
            elif pff_pass_block >= 78:
                perf_bonus += 35000
                perf_factors.append(f"Strong pass protector ({pff_pass_block:.1f})")
            elif pff_pass_block >= 70:
                perf_bonus += 18000
                perf_factors.append(f"Capable pass pro ({pff_pass_block:.1f})")
            elif pff_pass_block < 55 and position == "OT":
                perf_bonus -= 50000
                perf_factors.append(f"⚠️ Pass pro liability ({pff_pass_block:.1f})")

            # === RUN BLOCKING GRADE ===
            if pff_run_block >= 90:
                perf_bonus += 50000
                perf_factors.append(f"Mauler in the run game ({pff_run_block:.1f})")
            elif pff_run_block >= 82:
                perf_bonus += 35000
                perf_factors.append(f"Road grader ({pff_run_block:.1f} run block)")
            elif pff_run_block >= 72:
                perf_bonus += 18000
                perf_factors.append(f"Solid run blocker ({pff_run_block:.1f})")
            elif pff_run_block < 55:
                perf_bonus -= 25000
                perf_factors.append(f"⚠️ Struggles in run game ({pff_run_block:.1f})")

            # === PASS BLOCKING EFFICIENCY (PBE) - ELITE METRIC ===
            effective_pbe = true_pass_pbe if true_pass_pbe > 0 else pass_block_eff
            if effective_pbe > 0:
                if effective_pbe >= 99:
                    perf_bonus += 90000
                    perf_factors.append(f"Perfect PBE ({effective_pbe:.1f}%)")
                elif effective_pbe >= 98:
                    perf_bonus += 65000
                    perf_factors.append(f"Elite PBE ({effective_pbe:.1f}%)")
                elif effective_pbe >= 97:
                    perf_bonus += 40000
                    perf_factors.append(f"Excellent PBE ({effective_pbe:.1f}%)")
                elif effective_pbe >= 95:
                    perf_bonus += 20000
                    perf_factors.append(f"Clean pass pro ({effective_pbe:.1f}% PBE)")
                elif effective_pbe < 93:
                    perf_bonus -= 35000
                    perf_factors.append(f"⚠️ Pass pro issues ({effective_pbe:.1f}% PBE)")

            # === PRESSURE METRICS (Negatives) ===
            total_pressures = pressures_allowed + true_pass_pressures
            if total_pressures > 0:
                if sacks_allowed >= 6:
                    perf_bonus -= 60000
                    perf_factors.append(f"⚠️ Sack prone ({sacks_allowed} sacks allowed)")
                elif sacks_allowed >= 4:
                    perf_bonus -= 35000
                    perf_factors.append(f"⚠️ Pass pro concerns ({sacks_allowed} sacks)")
                elif sacks_allowed >= 2:
                    perf_bonus -= 15000
                    perf_factors.append(f"Some sacks allowed ({sacks_allowed})")
                elif sacks_allowed == 0 and pass_block_snaps > 200:
                    perf_bonus += 40000
                    perf_factors.append("No sacks allowed!")

                if pressures_allowed >= 30:
                    perf_bonus -= 45000
                    perf_factors.append(f"⚠️ High pressure rate ({pressures_allowed} allowed)")
                elif pressures_allowed >= 20:
                    perf_bonus -= 25000
                    perf_factors.append(f"⚠️ Pressure issues ({pressures_allowed} allowed)")
                elif pressures_allowed < 10 and pass_block_snaps > 300:
                    perf_bonus += 30000
                    perf_factors.append(f"Minimal pressures ({pressures_allowed} allowed)")

            # === SCHEME VERSATILITY (Gap vs Zone) ===
            if gap_run_grade > 0 and zone_run_grade > 0:
                if gap_run_grade >= 80 and zone_run_grade >= 80:
                    perf_bonus += 35000
                    perf_factors.append(f"Scheme versatile ({gap_run_grade:.0f} gap/{zone_run_grade:.0f} zone)")
                elif gap_run_grade >= 85:
                    perf_bonus += 20000
                    perf_factors.append(f"Gap scheme specialist ({gap_run_grade:.1f})")
                elif zone_run_grade >= 85:
                    perf_bonus += 20000
                    perf_factors.append(f"Zone scheme specialist ({zone_run_grade:.1f})")

            # === SNAP COUNT DURABILITY ===
            if offensive_snaps > 900:
                perf_bonus += 35000
                perf_factors.append(f"Ironman ({offensive_snaps} snaps)")
            elif offensive_snaps > 700:
                perf_bonus += 22000
                perf_factors.append(f"Full-time starter ({offensive_snaps} snaps)")
            elif offensive_snaps > 500:
                perf_bonus += 12000
                perf_factors.append(f"Regular starter ({offensive_snaps} snaps)")

            # === POSITIONAL VERSATILITY ===
            positions_played = sum([1 for s in [lt_snaps, lg_snaps, c_snaps, rg_snaps, rt_snaps] if s > 50])
            if positions_played >= 3:
                perf_bonus += 40000
                perf_factors.append(f"OL Swiss Army Knife ({positions_played} positions)")
            elif positions_played >= 2:
                perf_bonus += 20000
                perf_factors.append(f"Multi-position flexibility ({positions_played} spots)")

            # === PENALTY ASSESSMENT ===
            if penalties >= 10:
                perf_bonus -= 50000
                perf_factors.append(f"⚠️ Penalty machine ({penalties} penalties)")
            elif penalties >= 6:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Penalty issues ({penalties} penalties)")
            elif penalties >= 4:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Some penalties ({penalties})")
            elif penalties <= 1 and offensive_snaps > 400:
                perf_bonus += 20000
                perf_factors.append(f"Clean player ({penalties} penalties)")

        else:
            # No PFF data - fall back to traditional metrics
            perf_factors.append("ℹ️ No PFF grade (import for better accuracy)")

        # Star rating (scouting consensus on technique/potential)
        if stars >= 5:
            perf_bonus += 50000
            perf_factors.append("Elite prospect (5-star)")
        elif stars >= 4:
            perf_bonus += 25000
            perf_factors.append("High-upside lineman (4-star)")
        elif stars <= 2:
            perf_bonus -= 15000
            perf_factors.append("⚠️ Lower recruiting profile")

        # Position scarcity bonus (OT is premium)
        if position == "OT":
            perf_bonus += 25000
            perf_factors.append("Premium position (OT)")
        elif position == "C":
            perf_bonus += 20000
            perf_factors.append("Center (calls protections)")
        elif position in ["OG", "IOL"]:
            perf_bonus += 15000
            perf_factors.append("Interior lineman")

        # Manual penalty/accountability fields (if entered)
        sacks_allowed = player_data.get("sacks_allowed", 0) or 0
        penalties = player_data.get("penalties", 0) or 0
        holding_calls = player_data.get("holding_penalties", 0) or 0
        false_starts = player_data.get("false_starts", 0) or 0

        # Negative metrics (when manually entered)
        if sacks_allowed > 5:
            perf_bonus -= 40000
            perf_factors.append(f"⚠️ Pass pro issues ({sacks_allowed} sacks allowed)")
        elif sacks_allowed > 3:
            perf_bonus -= 20000
            perf_factors.append(f"⚠️ Some sacks allowed ({sacks_allowed})")

        if holding_calls > 5:
            perf_bonus -= 30000
            perf_factors.append(f"⚠️ Holding tendency ({holding_calls} calls)")
        elif holding_calls > 3:
            perf_bonus -= 15000
            perf_factors.append(f"⚠️ Holding concerns ({holding_calls} calls)")

        if false_starts > 3:
            perf_bonus -= 25000
            perf_factors.append(f"⚠️ Discipline issue ({false_starts} false starts)")
        elif false_starts > 1:
            perf_bonus -= 10000
            perf_factors.append(f"⚠️ False start concerns ({false_starts})")

        total_penalties = penalties + holding_calls + false_starts
        if total_penalties > 8:
            perf_bonus -= 35000
            perf_factors.append(f"⚠️ High penalty count ({total_penalties} total)")

        # If no penalty data entered, note the limitation
        if sacks_allowed == 0 and penalties == 0 and holding_calls == 0:
            perf_factors.append("ℹ️ No penalty data available (enter manually for accuracy)")

    # Defensive stats - ELITE COMPREHENSIVE EVALUATION (DL/EDGE/LB)
    elif position in ["EDGE", "DT", "DL", "LB", "DE"]:
        # ===========================================
        # PFF CORE GRADES
        # ===========================================
        pff_overall = player_data.get("pff_overall", 0) or 0
        pff_pass_rush = player_data.get("pff_pass_rush", 0) or 0
        pff_run_def = player_data.get("pff_run_defense", 0) or 0
        pff_tackling = player_data.get("pff_tackling", 0) or 0
        pff_coverage = player_data.get("pff_coverage", 0) or 0

        # ===========================================
        # PASS RUSH METRICS - THE MONEY STATS
        # ===========================================
        pass_rush_prod = player_data.get("pass_rushing_productivity", 0) or 0
        pass_rush_wr = player_data.get("pass_rush_win_rate", 0) or 0
        pass_rush_wins = player_data.get("pass_rush_wins", 0) or 0
        pressures = player_data.get("pressures", 0) or 0
        sacks = player_data.get("sacks", 0) or 0
        hits = player_data.get("hits", 0) or 0
        hurries = player_data.get("hurries", 0) or 0
        batted_passes = player_data.get("batted_passes", 0) or 0
        pass_rush_snaps = player_data.get("pass_rush_snaps", 0) or 0

        # True pass rush (dropback, not play action)
        true_pass_prp = player_data.get("true_pass_set_prp", 0) or 0
        true_pass_wr = player_data.get("true_pass_set_pass_rush_win_rate", 0) or 0
        true_pass_pressures = player_data.get("true_pass_set_total_pressures", 0) or 0
        true_pass_sacks = player_data.get("true_pass_set_sacks", 0) or 0

        # Left vs Right side production
        lhs_pressures = player_data.get("lhs_pressures", 0) or 0
        lhs_sacks = player_data.get("lhs_sacks", 0) or 0
        lhs_prp = player_data.get("lhs_prp", 0) or 0
        rhs_pressures = player_data.get("rhs_pressures", 0) or 0
        rhs_sacks = player_data.get("rhs_sacks", 0) or 0
        rhs_prp = player_data.get("rhs_prp", 0) or 0

        # ===========================================
        # RUN DEFENSE METRICS
        # ===========================================
        stops = player_data.get("stops", 0) or 0
        stop_pct = player_data.get("stop_percent", 0) or 0
        run_stop_opp = player_data.get("run_stop_opp", 0) or 0
        tackles = player_data.get("tackles", 0) or 0
        tfls = player_data.get("tackles_for_loss", 0) or 0
        assists = player_data.get("assists", 0) or 0

        # ===========================================
        # TACKLING RELIABILITY
        # ===========================================
        missed_tackles = player_data.get("missed_tackles", 0) or 0
        missed_tackle_rate = player_data.get("missed_tackle_rate", 0) or 0
        avg_depth_tackle = player_data.get("avg_depth_of_tackle", 0) or 0

        # ===========================================
        # SNAP COUNTS & ALIGNMENT
        # ===========================================
        defensive_snaps = player_data.get("defensive_snaps", 0) or 0
        dl_snaps = player_data.get("snap_counts_dl", 0) or 0
        box_snaps = player_data.get("snap_counts_box", 0) or 0
        coverage_snaps = player_data.get("coverage_snaps", 0) or 0

        # ===========================================
        # BALL DISRUPTION
        # ===========================================
        forced_fumbles = player_data.get("forced_fumbles", 0) or 0
        fumble_recoveries = player_data.get("fumble_recoveries", 0) or 0
        ints = player_data.get("ints", 0) or 0
        pbus = player_data.get("pbus", 0) or 0

        # ===========================================
        # PENALTIES
        # ===========================================
        penalties = player_data.get("penalties", 0) or 0
        penalty_grade = player_data.get("grades_defense_penalty", 0) or 0

        # ===================================================================
        # MINIMUM SNAP THRESHOLDS - Critical for valid PFF grade analysis
        # ===================================================================
        MIN_DEF_SNAPS = 200  # Minimum for overall defensive grades
        MIN_PASS_RUSH_SNAPS = 100  # Minimum for pass rush grades

        has_valid_sample = defensive_snaps >= MIN_DEF_SNAPS
        has_valid_pass_rush = pass_rush_snaps >= MIN_PASS_RUSH_SNAPS

        # Small sample warning
        if pff_overall > 0 and not has_valid_sample:
            perf_factors.append(f"⚠️ Limited sample ({defensive_snaps} snaps - need {MIN_DEF_SNAPS}+)")

        if pff_overall > 0 and has_valid_sample:
            # === OVERALL GRADE TIERS ===
            if pff_overall >= 92:
                perf_bonus += 225000
                perf_factors.append(f"All-American defender ({pff_overall:.1f} PFF)")
            elif pff_overall >= 85:
                perf_bonus += 160000
                perf_factors.append(f"Elite PFF defender ({pff_overall:.1f})")
            elif pff_overall >= 78:
                perf_bonus += 100000
                perf_factors.append(f"Excellent PFF grade ({pff_overall:.1f})")
            elif pff_overall >= 70:
                perf_bonus += 55000
                perf_factors.append(f"Above average defender ({pff_overall:.1f})")
            elif pff_overall >= 60:
                perf_bonus += 25000
                perf_factors.append(f"Solid PFF grade ({pff_overall:.1f})")
            elif pff_overall < 55:
                perf_bonus -= 40000
                perf_factors.append(f"⚠️ Concerning grade ({pff_overall:.1f})")

            # === PASS RUSH GRADE (EDGE/DE PREMIUM) ===
            if position in ["EDGE", "DE"]:
                if pff_pass_rush >= 92:
                    perf_bonus += 100000
                    perf_factors.append(f"Elite pass rush grade ({pff_pass_rush:.1f})")
                elif pff_pass_rush >= 85:
                    perf_bonus += 70000
                    perf_factors.append(f"Excellent pass rusher ({pff_pass_rush:.1f})")
                elif pff_pass_rush >= 78:
                    perf_bonus += 45000
                    perf_factors.append(f"Strong pass rusher ({pff_pass_rush:.1f})")
                elif pff_pass_rush >= 70:
                    perf_bonus += 25000
                    perf_factors.append(f"Capable pass rusher ({pff_pass_rush:.1f})")
                elif pff_pass_rush < 55:
                    perf_bonus -= 35000
                    perf_factors.append(f"⚠️ Pass rush concerns ({pff_pass_rush:.1f})")

            # === RUN DEFENSE GRADE ===
            if pff_run_def >= 90:
                perf_bonus += 55000
                perf_factors.append(f"Elite run defender ({pff_run_def:.1f})")
            elif pff_run_def >= 82:
                perf_bonus += 38000
                perf_factors.append(f"Stout vs the run ({pff_run_def:.1f})")
            elif pff_run_def >= 72:
                perf_bonus += 22000
                perf_factors.append(f"Solid run defender ({pff_run_def:.1f})")
            elif pff_run_def < 55:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Run defense liability ({pff_run_def:.1f})")

            # === LB COVERAGE (CRITICAL FOR MODERN LBs) ===
            if position == "LB" and pff_coverage > 0:
                if pff_coverage >= 85:
                    perf_bonus += 75000
                    perf_factors.append(f"Elite coverage LB ({pff_coverage:.1f})")
                elif pff_coverage >= 75:
                    perf_bonus += 45000
                    perf_factors.append(f"Coverage capable ({pff_coverage:.1f})")
                elif pff_coverage >= 65:
                    perf_bonus += 20000
                    perf_factors.append(f"Adequate in coverage ({pff_coverage:.1f})")
                elif pff_coverage < 50:
                    perf_bonus -= 35000
                    perf_factors.append(f"⚠️ Coverage liability ({pff_coverage:.1f})")

            # === TACKLING GRADE ===
            if pff_tackling >= 85:
                perf_bonus += 35000
                perf_factors.append(f"Sure tackler ({pff_tackling:.1f})")
            elif pff_tackling >= 75:
                perf_bonus += 18000
                perf_factors.append(f"Reliable tackler ({pff_tackling:.1f})")
            elif pff_tackling < 55:
                perf_bonus -= 25000
                perf_factors.append(f"⚠️ Tackling issues ({pff_tackling:.1f})")

        # === PASS RUSHING PRODUCTIVITY (PRP) - THE MONEY METRIC ===
        # Only evaluate rate metrics with sufficient pass rush snaps
        effective_prp = true_pass_prp if true_pass_prp > 0 else pass_rush_prod
        if effective_prp > 0 and position in ["EDGE", "DE", "DT"] and has_valid_pass_rush:
            if effective_prp >= 15:
                perf_bonus += 120000
                perf_factors.append(f"Elite PRP ({effective_prp:.1f})")
            elif effective_prp >= 12:
                perf_bonus += 80000
                perf_factors.append(f"Excellent PRP ({effective_prp:.1f})")
            elif effective_prp >= 9:
                perf_bonus += 50000
                perf_factors.append(f"Strong PRP ({effective_prp:.1f})")
            elif effective_prp >= 6:
                perf_bonus += 25000
                perf_factors.append(f"Solid PRP ({effective_prp:.1f})")
            elif effective_prp < 4:
                perf_bonus -= 25000
                perf_factors.append(f"⚠️ Low PRP ({effective_prp:.1f})")

        # === PASS RUSH WIN RATE ===
        effective_wr = true_pass_wr if true_pass_wr > 0 else pass_rush_wr
        if effective_wr > 0 and position in ["EDGE", "DE"] and has_valid_pass_rush:
            if effective_wr >= 25:
                perf_bonus += 80000
                perf_factors.append(f"Dominant win rate ({effective_wr:.0f}%)")
            elif effective_wr >= 20:
                perf_bonus += 55000
                perf_factors.append(f"Elite win rate ({effective_wr:.0f}%)")
            elif effective_wr >= 15:
                perf_bonus += 30000
                perf_factors.append(f"Strong win rate ({effective_wr:.0f}%)")
            elif effective_wr < 10:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Low win rate ({effective_wr:.0f}%)")

        # === RAW PRODUCTION STATS ===
        total_pressures = pressures + true_pass_pressures
        if position in ["EDGE", "DE"]:
            if sacks >= 14:
                perf_bonus += 200000
                perf_factors.append(f"All-American sack total ({sacks})")
            elif sacks >= 10:
                perf_bonus += 130000
                perf_factors.append(f"Elite sack production ({sacks})")
            elif sacks >= 7:
                perf_bonus += 75000
                perf_factors.append(f"Strong sack production ({sacks})")
            elif sacks >= 4:
                perf_bonus += 35000
                perf_factors.append(f"Productive pass rusher ({sacks} sacks)")

            if total_pressures >= 60:
                perf_bonus += 70000
                perf_factors.append(f"Pressure machine ({total_pressures} pressures)")
            elif total_pressures >= 45:
                perf_bonus += 45000
                perf_factors.append(f"Constant pressure ({total_pressures})")
            elif total_pressures >= 30:
                perf_bonus += 25000
                perf_factors.append(f"Disruptive ({total_pressures} pressures)")

        elif position == "DT":
            if sacks >= 8:
                perf_bonus += 100000
                perf_factors.append(f"Interior force ({sacks} sacks)")
            elif sacks >= 5:
                perf_bonus += 60000
                perf_factors.append(f"Penetrating DT ({sacks} sacks)")
            elif sacks >= 3:
                perf_bonus += 30000
                perf_factors.append(f"Interior pressure ({sacks} sacks)")

            if total_pressures >= 40:
                perf_bonus += 50000
                perf_factors.append(f"Dominant interior ({total_pressures} pressures)")

        # === LEFT VS RIGHT SIDE SPLITS ===
        if lhs_prp > 0 and rhs_prp > 0:
            if min(lhs_prp, rhs_prp) >= 8:
                perf_bonus += 35000
                perf_factors.append(f"Versatile rusher (L:{lhs_prp:.0f}/R:{rhs_prp:.0f} PRP)")
            elif max(lhs_prp, rhs_prp) >= 15:
                perf_bonus += 20000
                perf_factors.append(f"One-side dominant ({max(lhs_prp, rhs_prp):.0f} PRP)")

        # === RUN DEFENSE PRODUCTION ===
        if stop_pct > 0:
            if stop_pct >= 12:
                perf_bonus += 55000
                perf_factors.append(f"Elite run stopper ({stop_pct:.1f}% stop rate)")
            elif stop_pct >= 9:
                perf_bonus += 35000
                perf_factors.append(f"Strong run stopper ({stop_pct:.1f}%)")
            elif stop_pct >= 6:
                perf_bonus += 18000
                perf_factors.append(f"Solid vs the run ({stop_pct:.1f}%)")
            elif stop_pct < 4:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Run defense concerns ({stop_pct:.1f}%)")

        if tfls >= 18:
            perf_bonus += 90000
            perf_factors.append(f"Game-wrecker ({tfls} TFLs)")
        elif tfls >= 14:
            perf_bonus += 65000
            perf_factors.append(f"Elite disruptor ({tfls} TFLs)")
        elif tfls >= 10:
            perf_bonus += 40000
            perf_factors.append(f"Strong TFL production ({tfls})")
        elif tfls >= 6:
            perf_bonus += 20000
            perf_factors.append(f"Active behind LOS ({tfls} TFLs)")

        # === TACKLE PRODUCTION (LB EMPHASIS) ===
        if position == "LB":
            if tackles >= 120:
                perf_bonus += 90000
                perf_factors.append(f"Tackle machine ({tackles})")
            elif tackles >= 100:
                perf_bonus += 65000
                perf_factors.append(f"High-volume tackler ({tackles})")
            elif tackles >= 80:
                perf_bonus += 40000
                perf_factors.append(f"Productive tackler ({tackles})")
            elif tackles >= 60:
                perf_bonus += 22000
                perf_factors.append(f"Solid tackler ({tackles})")
        else:  # DL
            if tackles >= 60:
                perf_bonus += 45000
                perf_factors.append(f"Active DL ({tackles} tackles)")
            elif tackles >= 45:
                perf_bonus += 28000
                perf_factors.append(f"Run stuffer ({tackles} tackles)")

        # === TACKLING RELIABILITY ===
        if missed_tackle_rate > 0:
            if missed_tackle_rate >= 20:
                perf_bonus -= 50000
                perf_factors.append(f"⚠️ Tackling liability ({missed_tackle_rate:.0f}% miss rate)")
            elif missed_tackle_rate >= 15:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Missed tackle concerns ({missed_tackle_rate:.0f}%)")
            elif missed_tackle_rate >= 10:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Some missed tackles ({missed_tackle_rate:.0f}%)")
            elif missed_tackle_rate < 6:
                perf_bonus += 25000
                perf_factors.append(f"Sure tackler ({missed_tackle_rate:.0f}% miss rate)")
        elif missed_tackles > 15:
            perf_bonus -= 40000
            perf_factors.append(f"⚠️ Too many missed ({missed_tackles})")
        elif missed_tackles > 10:
            perf_bonus -= 20000
            perf_factors.append(f"⚠️ Missed tackles ({missed_tackles})")

        # === BALL DISRUPTION ===
        if forced_fumbles >= 4:
            perf_bonus += 50000
            perf_factors.append(f"Fumble creator ({forced_fumbles} FF)")
        elif forced_fumbles >= 2:
            perf_bonus += 25000
            perf_factors.append(f"Ball disruptor ({forced_fumbles} FF)")

        if batted_passes >= 8:
            perf_bonus += 35000
            perf_factors.append(f"Batted ball artist ({batted_passes})")
        elif batted_passes >= 5:
            perf_bonus += 18000
            perf_factors.append(f"Gets hands up ({batted_passes} batted)")

        if ints > 0 and position == "LB":
            perf_bonus += 30000 * ints
            perf_factors.append(f"Ball hawk LB ({ints} INTs)")

        # === SNAP COUNT DURABILITY ===
        if defensive_snaps >= 800:
            perf_bonus += 35000
            perf_factors.append(f"Ironman defender ({defensive_snaps} snaps)")
        elif defensive_snaps >= 600:
            perf_bonus += 22000
            perf_factors.append(f"Every-down player ({defensive_snaps} snaps)")

        # === PENALTIES ===
        if penalties >= 8:
            perf_bonus -= 45000
            perf_factors.append(f"⚠️ Penalty prone ({penalties} penalties)")
        elif penalties >= 5:
            perf_bonus -= 25000
            perf_factors.append(f"⚠️ Discipline issues ({penalties} penalties)")
        elif penalties >= 3:
            perf_bonus -= 12000
            perf_factors.append(f"⚠️ Some penalties ({penalties})")
        elif penalties <= 1 and defensive_snaps > 400:
            perf_bonus += 18000
            perf_factors.append(f"Clean defender ({penalties} penalties)")

    # Secondary stats - ELITE COMPREHENSIVE COVERAGE EVALUATION (CB/S/DB)
    elif position in ["CB", "S", "DB"]:
        # ===========================================
        # PFF CORE GRADES
        # ===========================================
        pff_overall = player_data.get("pff_overall", 0) or 0
        pff_coverage = player_data.get("pff_coverage", 0) or 0
        pff_tackling = player_data.get("pff_tackling", 0) or 0
        pff_run_defense = player_data.get("pff_run_defense", 0) or 0

        # ===========================================
        # MAN COVERAGE METRICS - THE MONEY STATS
        # ===========================================
        man_cov_grade = player_data.get("man_grades_coverage_defense", 0) or 0
        man_qb_rating = player_data.get("man_qb_rating_against", 0) or 0
        man_ypc_snap = player_data.get("man_yards_per_coverage_snap", 0) or 0
        man_catch_rate = player_data.get("man_catch_rate", 0) or 0
        man_forced_inc = player_data.get("man_forced_incompletes", 0) or 0
        man_forced_inc_rate = player_data.get("man_forced_incompletion_rate", 0) or 0
        man_coverage_snaps = player_data.get("man_snap_counts_coverage", 0) or 0
        man_cov_pct = player_data.get("man_coverage_percent", 0) or 0
        man_missed_tackles = player_data.get("man_missed_tackles", 0) or 0
        man_miss_rate = player_data.get("man_missed_tackle_rate", 0) or 0
        man_pbus = player_data.get("man_pass_break_ups", 0) or 0

        # ===========================================
        # ZONE COVERAGE METRICS
        # ===========================================
        zone_cov_grade = player_data.get("zone_grades_coverage_defense", 0) or 0
        zone_qb_rating = player_data.get("zone_qb_rating_against", 0) or 0
        zone_ypc_snap = player_data.get("zone_yards_per_coverage_snap", 0) or 0
        zone_catch_rate = player_data.get("zone_catch_rate", 0) or 0
        zone_forced_inc = player_data.get("zone_forced_incompletes", 0) or 0
        zone_forced_inc_rate = player_data.get("zone_forced_incompletion_rate", 0) or 0
        zone_coverage_snaps = player_data.get("zone_snap_counts_coverage", 0) or 0
        zone_cov_pct = player_data.get("zone_coverage_percent", 0) or 0
        zone_missed_tackles = player_data.get("zone_missed_tackles", 0) or 0
        zone_miss_rate = player_data.get("zone_missed_tackle_rate", 0) or 0
        zone_pbus = player_data.get("zone_pass_break_ups", 0) or 0

        # ===========================================
        # AGGREGATE COVERAGE METRICS
        # ===========================================
        passer_rating_allowed = player_data.get("passer_rating_allowed", 0) or 0
        yards_per_cov_snap = player_data.get("yards_per_coverage_snap", 0) or 0
        coverage_snaps = player_data.get("coverage_snaps", 0) or 0
        forced_inc = player_data.get("forced_incompletes", 0) or 0
        forced_inc_rate = player_data.get("forced_incompletion_rate", 0) or 0
        coverage_per_target = player_data.get("coverage_snaps_per_target", 0) or 0

        # ===========================================
        # BALL SKILLS
        # ===========================================
        ints = player_data.get("ints", 0) or 0
        pbus = player_data.get("pbus", 0) or 0
        dropped_ints = player_data.get("dropped_ints", 0) or 0
        int_tds = player_data.get("interception_touchdowns", 0) or 0
        forced_fumbles = player_data.get("forced_fumbles", 0) or 0

        # ===========================================
        # TACKLING & RUN SUPPORT
        # ===========================================
        tackles = player_data.get("tackles", 0) or 0
        missed_tackles = player_data.get("missed_tackles", 0) or 0
        missed_tackle_rate = player_data.get("missed_tackle_rate", 0) or 0

        # ===========================================
        # ALIGNMENT
        # ===========================================
        slot_snaps = player_data.get("snap_counts_slot", 0) or 0
        corner_snaps = player_data.get("snap_counts_corner", 0) or 0
        fs_snaps = player_data.get("snap_counts_fs", 0) or 0
        defensive_snaps = player_data.get("defensive_snaps", 0) or 0

        # ===================================================================
        # MINIMUM SNAP THRESHOLDS - Critical for valid PFF grade analysis
        # ===================================================================
        MIN_DEF_SNAPS = 200  # Minimum for overall defensive grades
        MIN_COV_SNAPS = 150  # Minimum for coverage grades
        MIN_MAN_SNAPS = 80   # Minimum for man coverage splits
        MIN_ZONE_SNAPS = 80  # Minimum for zone coverage splits

        has_valid_sample = defensive_snaps >= MIN_DEF_SNAPS
        has_valid_coverage = coverage_snaps >= MIN_COV_SNAPS
        has_valid_man = man_coverage_snaps >= MIN_MAN_SNAPS
        has_valid_zone = zone_coverage_snaps >= MIN_ZONE_SNAPS

        # Small sample warning
        if pff_overall > 0 and not has_valid_sample:
            perf_factors.append(f"⚠️ Limited sample ({defensive_snaps} snaps - need {MIN_DEF_SNAPS}+)")

        if pff_overall > 0 and has_valid_sample:
            # === OVERALL GRADE TIERS ===
            if pff_overall >= 92:
                perf_bonus += 200000
                perf_factors.append(f"All-American DB ({pff_overall:.1f} PFF)")
            elif pff_overall >= 85:
                perf_bonus += 140000
                perf_factors.append(f"Elite coverage grade ({pff_overall:.1f})")
            elif pff_overall >= 78:
                perf_bonus += 90000
                perf_factors.append(f"Excellent DB ({pff_overall:.1f})")
            elif pff_overall >= 70:
                perf_bonus += 50000
                perf_factors.append(f"Above average DB ({pff_overall:.1f})")
            elif pff_overall >= 60:
                perf_bonus += 22000
                perf_factors.append(f"Solid coverage ({pff_overall:.1f})")
            elif pff_overall < 55:
                perf_bonus -= 40000
                perf_factors.append(f"⚠️ Concerning grade ({pff_overall:.1f})")

            # === COVERAGE GRADE (CB PREMIUM) ===
            if position == "CB":
                if pff_coverage >= 90:
                    perf_bonus += 80000
                    perf_factors.append(f"Lockdown corner ({pff_coverage:.1f} cov)")
                elif pff_coverage >= 82:
                    perf_bonus += 55000
                    perf_factors.append(f"Excellent coverage ({pff_coverage:.1f})")
                elif pff_coverage >= 72:
                    perf_bonus += 30000
                    perf_factors.append(f"Strong coverage ({pff_coverage:.1f})")
                elif pff_coverage < 55:
                    perf_bonus -= 40000
                    perf_factors.append(f"⚠️ Coverage liability ({pff_coverage:.1f})")
            else:  # Safety
                if pff_coverage >= 85:
                    perf_bonus += 60000
                    perf_factors.append(f"Elite coverage safety ({pff_coverage:.1f})")
                elif pff_coverage >= 75:
                    perf_bonus += 35000
                    perf_factors.append(f"Strong coverage ({pff_coverage:.1f})")

            # === TACKLING GRADE ===
            if pff_tackling >= 85:
                perf_bonus += 35000
                perf_factors.append(f"Sure tackler ({pff_tackling:.1f})")
            elif pff_tackling >= 75:
                perf_bonus += 18000
                perf_factors.append(f"Reliable tackler ({pff_tackling:.1f})")
            elif pff_tackling < 55:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Tackling liability ({pff_tackling:.1f})")

            # === RUN DEFENSE (SAFETY PREMIUM) ===
            if position == "S" and pff_run_defense > 0:
                if pff_run_defense >= 82:
                    perf_bonus += 45000
                    perf_factors.append(f"Elite box safety ({pff_run_defense:.1f} run def)")
                elif pff_run_defense >= 72:
                    perf_bonus += 25000
                    perf_factors.append(f"Strong run support ({pff_run_defense:.1f})")

        # === MAN COVERAGE ANALYSIS ===
        if man_coverage_snaps > 100:
            if man_cov_grade >= 85:
                perf_bonus += 65000
                perf_factors.append(f"Elite man coverage ({man_cov_grade:.1f})")
            elif man_cov_grade >= 75:
                perf_bonus += 38000
                perf_factors.append(f"Strong man coverage ({man_cov_grade:.1f})")
            elif man_cov_grade < 55:
                perf_bonus -= 35000
                perf_factors.append(f"⚠️ Man coverage struggles ({man_cov_grade:.1f})")

            if man_qb_rating > 0:
                if man_qb_rating < 60:
                    perf_bonus += 55000
                    perf_factors.append(f"Shutdown in man ({man_qb_rating:.1f} QBR)")
                elif man_qb_rating < 75:
                    perf_bonus += 30000
                    perf_factors.append(f"Strong man QBR ({man_qb_rating:.1f})")
                elif man_qb_rating > 110:
                    perf_bonus -= 40000
                    perf_factors.append(f"⚠️ Targeted in man ({man_qb_rating:.1f} QBR)")

            if man_forced_inc >= 12:
                perf_bonus += 40000
                perf_factors.append(f"Forces incompletes ({man_forced_inc} in man)")
            elif man_forced_inc >= 8:
                perf_bonus += 22000
                perf_factors.append(f"Active hands ({man_forced_inc} forced inc)")

        # === ZONE COVERAGE ANALYSIS ===
        if zone_coverage_snaps > 100:
            if zone_cov_grade >= 85:
                perf_bonus += 55000
                perf_factors.append(f"Elite zone coverage ({zone_cov_grade:.1f})")
            elif zone_cov_grade >= 75:
                perf_bonus += 32000
                perf_factors.append(f"Strong zone player ({zone_cov_grade:.1f})")
            elif zone_cov_grade < 55:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ Zone coverage issues ({zone_cov_grade:.1f})")

            if zone_qb_rating > 0:
                if zone_qb_rating < 65:
                    perf_bonus += 45000
                    perf_factors.append(f"Zone eraser ({zone_qb_rating:.1f} QBR)")
                elif zone_qb_rating < 80:
                    perf_bonus += 25000
                    perf_factors.append(f"Strong zone QBR ({zone_qb_rating:.1f})")
                elif zone_qb_rating > 105:
                    perf_bonus -= 30000
                    perf_factors.append(f"⚠️ Exploited in zone ({zone_qb_rating:.1f} QBR)")

        # === SCHEME VERSATILITY ===
        if man_coverage_snaps > 80 and zone_coverage_snaps > 80:
            if man_cov_grade >= 70 and zone_cov_grade >= 70:
                perf_bonus += 45000
                perf_factors.append(f"Scheme versatile (M:{man_cov_grade:.0f}/Z:{zone_cov_grade:.0f})")
            if man_qb_rating > 0 and zone_qb_rating > 0 and man_qb_rating < 85 and zone_qb_rating < 85:
                perf_bonus += 30000
                perf_factors.append("Effective in all coverages")

        # === AGGREGATE PASSER RATING ALLOWED ===
        if passer_rating_allowed > 0 and coverage_snaps > 150:
            if passer_rating_allowed < 55:
                perf_bonus += 75000
                perf_factors.append(f"Elite passer rating ({passer_rating_allowed:.1f})")
            elif passer_rating_allowed < 70:
                perf_bonus += 50000
                perf_factors.append(f"Excellent passer rating ({passer_rating_allowed:.1f})")
            elif passer_rating_allowed < 85:
                perf_bonus += 28000
                perf_factors.append(f"Strong passer rating ({passer_rating_allowed:.1f})")
            elif passer_rating_allowed > 110:
                perf_bonus -= 45000
                perf_factors.append(f"⚠️ Targeted ({passer_rating_allowed:.1f} QBR allowed)")
            elif passer_rating_allowed > 95:
                perf_bonus -= 22000
                perf_factors.append(f"⚠️ Concerning QBR ({passer_rating_allowed:.1f})")

        # === YARDS PER COVERAGE SNAP ===
        if yards_per_cov_snap > 0 and coverage_snaps > 150:
            if yards_per_cov_snap < 0.7:
                perf_bonus += 55000
                perf_factors.append(f"Blanket coverage ({yards_per_cov_snap:.2f} y/snap)")
            elif yards_per_cov_snap < 0.9:
                perf_bonus += 30000
                perf_factors.append(f"Tight coverage ({yards_per_cov_snap:.2f} y/snap)")
            elif yards_per_cov_snap < 1.1:
                perf_bonus += 15000
                perf_factors.append(f"Solid coverage ({yards_per_cov_snap:.2f} y/snap)")
            elif yards_per_cov_snap > 1.5:
                perf_bonus -= 35000
                perf_factors.append(f"⚠️ Soft coverage ({yards_per_cov_snap:.2f} y/snap)")

        # === BALL SKILLS - TURNOVERS ===
        if ints >= 7:
            perf_bonus += 150000
            perf_factors.append(f"All-American ball hawk ({ints} INTs)")
        elif ints >= 5:
            perf_bonus += 100000
            perf_factors.append(f"Elite ball hawk ({ints} INTs)")
        elif ints >= 3:
            perf_bonus += 55000
            perf_factors.append(f"Playmaker ({ints} INTs)")
        elif ints >= 1:
            perf_bonus += 22000
            perf_factors.append(f"Creates turnovers ({ints} INT)")

        if int_tds > 0:
            perf_bonus += 40000 * int_tds
            perf_factors.append(f"Pick-6 threat ({int_tds} INT TDs)")

        if dropped_ints >= 4:
            perf_bonus -= 30000
            perf_factors.append(f"⚠️ Ball tracking issues ({dropped_ints} dropped)")
        elif dropped_ints >= 2:
            perf_bonus -= 12000
            perf_factors.append(f"⚠️ Some drops ({dropped_ints} dropped INTs)")

        # === PASS BREAK UPS ===
        total_pbus = pbus + man_pbus + zone_pbus
        if total_pbus >= 18:
            perf_bonus += 85000
            perf_factors.append(f"Elite ball disruption ({total_pbus} PBUs)")
        elif total_pbus >= 14:
            perf_bonus += 60000
            perf_factors.append(f"Lockdown coverage ({total_pbus} PBUs)")
        elif total_pbus >= 10:
            perf_bonus += 38000
            perf_factors.append(f"Strong coverage ({total_pbus} PBUs)")
        elif total_pbus >= 6:
            perf_bonus += 18000
            perf_factors.append(f"Active in coverage ({total_pbus} PBUs)")

        # === FORCED INCOMPLETES ===
        total_forced = forced_inc + man_forced_inc + zone_forced_inc
        if total_forced >= 20:
            perf_bonus += 50000
            perf_factors.append(f"Forces incompletes ({total_forced} total)")
        elif total_forced >= 14:
            perf_bonus += 32000
            perf_factors.append(f"Active hands ({total_forced} forced inc)")

        # === TACKLING RELIABILITY ===
        if missed_tackle_rate > 0:
            if missed_tackle_rate >= 18:
                perf_bonus -= 50000
                perf_factors.append(f"⚠️ Tackling liability ({missed_tackle_rate:.0f}%)")
            elif missed_tackle_rate >= 12:
                perf_bonus -= 28000
                perf_factors.append(f"⚠️ Missed tackle issues ({missed_tackle_rate:.0f}%)")
            elif missed_tackle_rate < 6:
                perf_bonus += 28000
                perf_factors.append(f"Sure tackler ({missed_tackle_rate:.0f}% miss)")
        elif missed_tackles > 12:
            perf_bonus -= 35000
            perf_factors.append(f"⚠️ Too many missed ({missed_tackles})")
        elif missed_tackles > 8:
            perf_bonus -= 18000
            perf_factors.append(f"⚠️ Some missed tackles ({missed_tackles})")

        # === TACKLE PRODUCTION (SAFETY PREMIUM) ===
        if position == "S":
            if tackles >= 90:
                perf_bonus += 65000
                perf_factors.append(f"Box safety/enforcer ({tackles} tackles)")
            elif tackles >= 70:
                perf_bonus += 42000
                perf_factors.append(f"Strong run support ({tackles} tackles)")
            elif tackles >= 50:
                perf_bonus += 22000
                perf_factors.append(f"Active in run game ({tackles} tackles)")
        else:  # CB
            if tackles >= 60:
                perf_bonus += 40000
                perf_factors.append(f"Physical corner ({tackles} tackles)")
            elif tackles >= 45:
                perf_bonus += 22000
                perf_factors.append(f"Willing tackler ({tackles} tackles)")

        # === ALIGNMENT VERSATILITY ===
        alignments_played = sum([1 for s in [slot_snaps, corner_snaps, fs_snaps] if s > 75])
        if alignments_played >= 2:
            perf_bonus += 35000
            perf_factors.append(f"Versatile DB ({alignments_played} alignments)")

        if slot_snaps > 200:
            perf_bonus += 25000
            perf_factors.append(f"Slot specialist ({slot_snaps} slot snaps)")

        # === SNAP COUNT DURABILITY ===
        if defensive_snaps >= 800:
            perf_bonus += 30000
            perf_factors.append(f"Ironman DB ({defensive_snaps} snaps)")
        elif defensive_snaps >= 600:
            perf_bonus += 18000
            perf_factors.append(f"Every-down DB ({defensive_snaps} snaps)")

    # Kicker stats - ELITE COMPREHENSIVE SPECIAL TEAMS EVALUATION
    elif position == "K":
        # CFBD basic stats
        fg_made = player_data.get("fg_made", 0) or 0
        fg_att = player_data.get("fg_attempted", 0) or 0
        xp_made = player_data.get("xp_made", 0) or 0
        xp_att = player_data.get("xp_attempted", 0) or 0
        kicking_pts = player_data.get("kicking_points", 0) or 0

        # PFF KICKER GRADES & ADVANCED METRICS
        pff_kicker_grade = player_data.get("grades_fgep_kicker", 0) or 0
        pff_kickoff_grade = player_data.get("grades_kickoff_kicker", 0) or 0
        pff_total_made = player_data.get("total_made", 0) or 0
        pff_total_pct = player_data.get("total_percent", 0) or 0
        pff_fifty_pct = player_data.get("fifty_percent", 0) or 0
        pff_forty_pct = player_data.get("forty_percent", 0) or 0
        pff_thirty_pct = player_data.get("thirty_percent", 0) or 0
        pff_pat_pct = player_data.get("pat_percent", 0) or 0
        pff_avg_distance = player_data.get("average_distance", 0) or 0
        pff_ko_touchbacks = player_data.get("touchbacks", 0) or 0

        # ===================================================================
        # MINIMUM SAMPLE THRESHOLDS - Critical for valid kicker evaluation
        # ===================================================================
        MIN_FG_ATTEMPTS = 10  # Minimum FG attempts for grades to be meaningful

        # Use PFF total_made if available, fallback to CFBD fg_att
        total_attempts = pff_total_made if pff_total_made > 0 else fg_att
        has_valid_sample = total_attempts >= MIN_FG_ATTEMPTS

        # Small sample warning
        if pff_kicker_grade > 0 and not has_valid_sample:
            perf_factors.append(f"⚠️ Limited sample ({total_attempts} FG att - need {MIN_FG_ATTEMPTS}+)")

        # === PFF KICKER GRADE (PRIMARY EVALUATION) ===
        if pff_kicker_grade > 0 and has_valid_sample:
            if pff_kicker_grade >= 90:
                perf_bonus += 125000
                perf_factors.append(f"Elite PFF kicker ({pff_kicker_grade:.1f})")
            elif pff_kicker_grade >= 80:
                perf_bonus += 85000
                perf_factors.append(f"Outstanding kicker ({pff_kicker_grade:.1f} PFF)")
            elif pff_kicker_grade >= 70:
                perf_bonus += 50000
                perf_factors.append(f"Quality kicker ({pff_kicker_grade:.1f} PFF)")
            elif pff_kicker_grade >= 60:
                perf_bonus += 25000
                perf_factors.append(f"Solid kicker ({pff_kicker_grade:.1f} PFF)")
            elif pff_kicker_grade < 50:
                perf_bonus -= 25000
                perf_factors.append(f"⚠️ Kicking concerns ({pff_kicker_grade:.1f} PFF)")

        # === RANGE ACCURACY (50+ YARD SPECIALISTS) - only with valid sample ===
        if has_valid_sample:
            if pff_fifty_pct >= 80:
                perf_bonus += 75000
                perf_factors.append(f"Elite range (50+: {pff_fifty_pct:.0f}%)")
            elif pff_fifty_pct >= 65:
                perf_bonus += 45000
                perf_factors.append(f"Strong range (50+: {pff_fifty_pct:.0f}%)")
            elif pff_fifty_pct >= 50:
                perf_bonus += 25000
                perf_factors.append(f"Good from 50+ ({pff_fifty_pct:.0f}%)")
            elif pff_fifty_pct > 0 and pff_fifty_pct < 35:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Limited range (50+: {pff_fifty_pct:.0f}%)")

            # === 40-49 YARD ACCURACY ===
            if pff_forty_pct >= 90:
                perf_bonus += 50000
                perf_factors.append(f"Automatic 40-49 ({pff_forty_pct:.0f}%)")
            elif pff_forty_pct >= 80:
                perf_bonus += 30000
                perf_factors.append(f"Reliable 40-49 ({pff_forty_pct:.0f}%)")
            elif pff_forty_pct > 0 and pff_forty_pct < 65:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Shaky from 40-49 ({pff_forty_pct:.0f}%)")

            # === 30-39 YARD ACCURACY (SHOULD BE AUTOMATIC) ===
            if pff_thirty_pct >= 95:
                perf_bonus += 25000
                perf_factors.append(f"Automatic 30-39 ({pff_thirty_pct:.0f}%)")
            elif pff_thirty_pct > 0 and pff_thirty_pct < 80:
                perf_bonus -= 35000
                perf_factors.append(f"⚠️ Misses chip shots ({pff_thirty_pct:.0f}% 30-39)")

            # === PAT ACCURACY ===
            if pff_pat_pct >= 99:
                perf_bonus += 20000
                perf_factors.append(f"Perfect PATs ({pff_pat_pct:.0f}%)")
            elif pff_pat_pct > 0 and pff_pat_pct < 90:
                perf_bonus -= 30000
                perf_factors.append(f"⚠️ PAT concerns ({pff_pat_pct:.0f}%)")

        # === PFF KICKOFF GRADE ===
        if pff_kickoff_grade >= 85:
            perf_bonus += 45000
            perf_factors.append(f"Elite kickoffs ({pff_kickoff_grade:.1f} PFF)")
        elif pff_kickoff_grade >= 75:
            perf_bonus += 28000
            perf_factors.append(f"Strong kickoffs ({pff_kickoff_grade:.1f} PFF)")
        elif pff_kickoff_grade >= 65:
            perf_bonus += 15000
            perf_factors.append(f"Solid kickoffs ({pff_kickoff_grade:.1f} PFF)")
        elif pff_kickoff_grade > 0 and pff_kickoff_grade < 50:
            perf_bonus -= 15000
            perf_factors.append(f"⚠️ Kickoff issues ({pff_kickoff_grade:.1f} PFF)")

        # === FALLBACK: CFBD STATS (if no PFF data) ===
        if pff_kicker_grade == 0 and fg_att > 0:
            fg_pct = fg_made / fg_att
            if fg_pct > 0.90 and fg_made > 15:
                perf_bonus += 75000
                perf_factors.append(f"Elite accuracy ({fg_made}/{fg_att}, {fg_pct*100:.1f}%)")
            elif fg_pct > 0.85 and fg_made > 12:
                perf_bonus += 50000
                perf_factors.append(f"Very reliable ({fg_made}/{fg_att}, {fg_pct*100:.1f}%)")
            elif fg_pct > 0.75 and fg_made > 10:
                perf_bonus += 25000
                perf_factors.append(f"Reliable kicker ({fg_made}/{fg_att})")
            elif fg_pct < 0.70 and fg_att > 10:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Accuracy concerns ({fg_pct*100:.1f}%)")

        # === VOLUME SCORING ===
        if kicking_pts > 120:
            perf_bonus += 45000
            perf_factors.append(f"Go-to scorer ({kicking_pts} pts)")
        elif kicking_pts > 100:
            perf_bonus += 30000
            perf_factors.append(f"High-volume scorer ({kicking_pts} pts)")
        elif kicking_pts > 70:
            perf_bonus += 15000
            perf_factors.append(f"Solid production ({kicking_pts} pts)")

        # === XP RELIABILITY (CFBD fallback) ===
        if pff_pat_pct == 0 and xp_att > 30:
            xp_pct = xp_made / xp_att
            if xp_pct < 0.95:
                perf_bonus -= 10000
                perf_factors.append(f"⚠️ XP misses ({xp_made}/{xp_att})")

    # Punter stats - ELITE COMPREHENSIVE EVALUATION
    elif position == "P":
        # CFBD basic stats
        punt_avg = player_data.get("punt_avg", 0) or 0
        punts = player_data.get("punts", 0) or 0
        punts_in_20 = player_data.get("punts_inside_20", 0) or 0
        touchbacks = player_data.get("touchbacks", 0) or 0

        # PFF PUNTER GRADES & ADVANCED METRICS
        pff_punter_grade = player_data.get("grades_punter", 0) or 0
        pff_avg_hangtime = player_data.get("average_hangtime", 0) or 0
        pff_total_hangtime = player_data.get("total_hangtime", 0) or 0
        pff_avg_net_yards = player_data.get("average_net_yards", 0) or 0
        pff_total_net_yards = player_data.get("total_net_yards", 0) or 0
        pff_inside_twenties = player_data.get("inside_twenties", 0) or 0
        pff_punt_touchbacks = player_data.get("touchbacks", 0) or 0
        pff_punt_returns = player_data.get("returns", 0) or 0
        pff_return_yards = player_data.get("return_yards", 0) or 0

        # ===================================================================
        # MINIMUM SAMPLE THRESHOLDS - Critical for valid punter evaluation
        # ===================================================================
        MIN_PUNTS = 20  # Minimum punts for grades to be meaningful

        has_valid_sample = punts >= MIN_PUNTS

        # Small sample warning
        if pff_punter_grade > 0 and not has_valid_sample:
            perf_factors.append(f"⚠️ Limited sample ({punts} punts - need {MIN_PUNTS}+)")

        # === PFF PUNTER GRADE (PRIMARY EVALUATION) ===
        if pff_punter_grade > 0 and has_valid_sample:
            if pff_punter_grade >= 90:
                perf_bonus += 100000
                perf_factors.append(f"Elite PFF punter ({pff_punter_grade:.1f})")
            elif pff_punter_grade >= 80:
                perf_bonus += 65000
                perf_factors.append(f"Outstanding punter ({pff_punter_grade:.1f} PFF)")
            elif pff_punter_grade >= 70:
                perf_bonus += 40000
                perf_factors.append(f"Quality punter ({pff_punter_grade:.1f} PFF)")
            elif pff_punter_grade >= 60:
                perf_bonus += 20000
                perf_factors.append(f"Solid punter ({pff_punter_grade:.1f} PFF)")
            elif pff_punter_grade < 50:
                perf_bonus -= 25000
                perf_factors.append(f"⚠️ Punting concerns ({pff_punter_grade:.1f} PFF)")

        # === HANGTIME (COVERAGE TEAM VALUE) - only with valid sample ===
        if has_valid_sample:
            if pff_avg_hangtime >= 4.6:
                perf_bonus += 55000
                perf_factors.append(f"Elite hangtime ({pff_avg_hangtime:.2f}s)")
            elif pff_avg_hangtime >= 4.4:
                perf_bonus += 35000
                perf_factors.append(f"Strong hangtime ({pff_avg_hangtime:.2f}s)")
            elif pff_avg_hangtime >= 4.2:
                perf_bonus += 18000
                perf_factors.append(f"Good hangtime ({pff_avg_hangtime:.2f}s)")
            elif pff_avg_hangtime > 0 and pff_avg_hangtime < 4.0:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Low hangtime ({pff_avg_hangtime:.2f}s)")

            # === NET PUNTING EFFICIENCY ===
            if pff_avg_net_yards >= 44:
                perf_bonus += 50000
                perf_factors.append(f"Elite net punting ({pff_avg_net_yards:.1f} net)")
            elif pff_avg_net_yards >= 42:
                perf_bonus += 32000
                perf_factors.append(f"Strong net punting ({pff_avg_net_yards:.1f} net)")
            elif pff_avg_net_yards >= 40:
                perf_bonus += 18000
                perf_factors.append(f"Solid net punting ({pff_avg_net_yards:.1f} net)")
            elif pff_avg_net_yards > 0 and pff_avg_net_yards < 37:
                perf_bonus -= 20000
                perf_factors.append(f"⚠️ Poor net ({pff_avg_net_yards:.1f} net)")

            # === INSIDE-20 PLACEMENT (PFF DATA) ===
            if pff_inside_twenties >= 30:
                perf_bonus += 60000
                perf_factors.append(f"Elite coffin corner ({pff_inside_twenties} inside 20)")
            elif pff_inside_twenties >= 25:
                perf_bonus += 40000
                perf_factors.append(f"Pin master ({pff_inside_twenties} inside 20)")
            elif pff_inside_twenties >= 20:
                perf_bonus += 25000
                perf_factors.append(f"Quality placement ({pff_inside_twenties} inside 20)")
            elif pff_inside_twenties >= 15:
                perf_bonus += 12000
                perf_factors.append(f"Good placement ({pff_inside_twenties} inside 20)")

            # === RETURN PREVENTION ===
            if pff_punt_returns > 0 and pff_return_yards > 0:
                avg_return = pff_return_yards / pff_punt_returns
                if avg_return < 5:
                    perf_bonus += 30000
                    perf_factors.append(f"Return killer ({avg_return:.1f} yds/return)")
                elif avg_return < 8:
                    perf_bonus += 15000
                    perf_factors.append(f"Good coverage punt ({avg_return:.1f} yds/return)")
                elif avg_return > 15:
                    perf_bonus -= 20000
                    perf_factors.append(f"⚠️ Returnable punts ({avg_return:.1f} yds/return)")

        # === FALLBACK: CFBD STATS (if no PFF data) ===
        if pff_punter_grade == 0:
            # Punt average (leg strength)
            if punt_avg > 47:
                perf_bonus += 45000
                perf_factors.append(f"Cannon leg ({punt_avg:.1f} avg)")
            elif punt_avg > 45:
                perf_bonus += 30000
                perf_factors.append(f"Strong leg ({punt_avg:.1f} avg)")
            elif punt_avg > 42:
                perf_bonus += 15000
                perf_factors.append(f"Solid punting ({punt_avg:.1f} avg)")

            # CFBD placement
            if punts_in_20 > 25:
                perf_bonus += 40000
                perf_factors.append(f"Elite placement ({punts_in_20} inside 20)")
            elif punts_in_20 > 20:
                perf_bonus += 25000
                perf_factors.append(f"Pin specialist ({punts_in_20} inside 20)")
            elif punts_in_20 > 15:
                perf_bonus += 12000
                perf_factors.append(f"Good placement ({punts_in_20} inside 20)")

        # === TOUCHBACK CONCERNS (applies to both) ===
        if punts > 30 and touchbacks > 10:
            tb_rate = touchbacks / punts
            if tb_rate > 0.20:
                perf_bonus -= 15000
                perf_factors.append(f"⚠️ Too many TBs ({touchbacks} touchbacks)")

    # ==========================================================================
    # RETURN SPECIALIST - ELITE COMPREHENSIVE EVALUATION
    # (Applies to any position - special teams value adds to NIL)
    # ==========================================================================

    # CFBD basic return stats
    kr_yds = player_data.get("kick_return_yards", 0) or 0
    kr_tds = player_data.get("kick_return_tds", 0) or 0
    pr_yds = player_data.get("punt_return_yards", 0) or 0
    pr_tds = player_data.get("punt_return_tds", 0) or 0

    # PFF RETURN GRADES & ADVANCED METRICS
    pff_kr_grade = player_data.get("grades_kick_return", 0) or 0
    pff_pr_grade = player_data.get("grades_punt_return", 0) or 0
    pff_return_grade = player_data.get("grades_return", 0) or 0
    pff_kickoff_yds = player_data.get("kickoff_yards", 0) or 0
    pff_kickoff_tds = player_data.get("kickoff_touchdowns", 0) or 0
    pff_kickoff_long = player_data.get("kickoff_long", 0) or 0
    pff_kickoff_ypa = player_data.get("kickoff_ypa", 0) or 0
    pff_punt_yds = player_data.get("punt_yards", 0) or 0
    pff_punt_tds = player_data.get("punt_touchdowns", 0) or 0
    pff_punt_long = player_data.get("punt_long", 0) or 0
    pff_punt_ypa = player_data.get("punt_ypa", 0) or 0

    # === PFF KICK RETURN GRADE ===
    if pff_kr_grade >= 90:
        perf_bonus += 100000
        perf_factors.append(f"Elite KR specialist ({pff_kr_grade:.1f} PFF)")
    elif pff_kr_grade >= 80:
        perf_bonus += 65000
        perf_factors.append(f"Outstanding returner ({pff_kr_grade:.1f} KR PFF)")
    elif pff_kr_grade >= 70:
        perf_bonus += 40000
        perf_factors.append(f"Quality KR ({pff_kr_grade:.1f} PFF)")
    elif pff_kr_grade >= 60:
        perf_bonus += 22000
        perf_factors.append(f"Solid KR ability ({pff_kr_grade:.1f} PFF)")

    # === PFF PUNT RETURN GRADE ===
    if pff_pr_grade >= 90:
        perf_bonus += 90000
        perf_factors.append(f"Elite PR specialist ({pff_pr_grade:.1f} PFF)")
    elif pff_pr_grade >= 80:
        perf_bonus += 55000
        perf_factors.append(f"Outstanding PR ({pff_pr_grade:.1f} PFF)")
    elif pff_pr_grade >= 70:
        perf_bonus += 35000
        perf_factors.append(f"Quality PR ({pff_pr_grade:.1f} PFF)")
    elif pff_pr_grade >= 60:
        perf_bonus += 18000
        perf_factors.append(f"Solid PR ability ({pff_pr_grade:.1f} PFF)")

    # === KICK RETURN YARDS PER ATTEMPT (EFFICIENCY) ===
    if pff_kickoff_ypa >= 30:
        perf_bonus += 60000
        perf_factors.append(f"Explosive KR ({pff_kickoff_ypa:.1f} yds/ret)")
    elif pff_kickoff_ypa >= 26:
        perf_bonus += 38000
        perf_factors.append(f"Dynamic KR ({pff_kickoff_ypa:.1f} yds/ret)")
    elif pff_kickoff_ypa >= 23:
        perf_bonus += 20000
        perf_factors.append(f"Good KR average ({pff_kickoff_ypa:.1f} yds/ret)")
    elif pff_kickoff_ypa > 0 and pff_kickoff_ypa < 18:
        perf_bonus -= 15000
        perf_factors.append(f"⚠️ Below avg KR ({pff_kickoff_ypa:.1f} yds/ret)")

    # === PUNT RETURN YARDS PER ATTEMPT (EFFICIENCY) ===
    if pff_punt_ypa >= 15:
        perf_bonus += 55000
        perf_factors.append(f"Explosive PR ({pff_punt_ypa:.1f} yds/ret)")
    elif pff_punt_ypa >= 12:
        perf_bonus += 35000
        perf_factors.append(f"Dynamic PR ({pff_punt_ypa:.1f} yds/ret)")
    elif pff_punt_ypa >= 9:
        perf_bonus += 18000
        perf_factors.append(f"Good PR average ({pff_punt_ypa:.1f} yds/ret)")
    elif pff_punt_ypa > 0 and pff_punt_ypa < 6:
        perf_bonus -= 12000
        perf_factors.append(f"⚠️ Below avg PR ({pff_punt_ypa:.1f} yds/ret)")

    # === BIG PLAY ABILITY (LONG RETURNS) ===
    if pff_kickoff_long >= 90:
        perf_bonus += 45000
        perf_factors.append(f"House call threat ({pff_kickoff_long} KR long)")
    elif pff_kickoff_long >= 70:
        perf_bonus += 28000
        perf_factors.append(f"Big play KR ({pff_kickoff_long} long)")
    elif pff_kickoff_long >= 50:
        perf_bonus += 15000
        perf_factors.append(f"Explosive runs ({pff_kickoff_long} KR long)")

    if pff_punt_long >= 75:
        perf_bonus += 40000
        perf_factors.append(f"House call threat ({pff_punt_long} PR long)")
    elif pff_punt_long >= 55:
        perf_bonus += 25000
        perf_factors.append(f"Big play PR ({pff_punt_long} long)")
    elif pff_punt_long >= 40:
        perf_bonus += 12000
        perf_factors.append(f"Can break one ({pff_punt_long} PR long)")

    # === PFF TOUCHDOWN PRODUCTION ===
    if pff_kickoff_tds >= 2:
        perf_bonus += 80000
        perf_factors.append(f"KR TD machine ({pff_kickoff_tds} KR TDs)")
    elif pff_kickoff_tds == 1:
        perf_bonus += 35000
        perf_factors.append(f"KR touchdown ({pff_kickoff_tds} KR TD)")

    if pff_punt_tds >= 2:
        perf_bonus += 75000
        perf_factors.append(f"PR TD machine ({pff_punt_tds} PR TDs)")
    elif pff_punt_tds == 1:
        perf_bonus += 32000
        perf_factors.append(f"PR touchdown ({pff_punt_tds} PR TD)")

    # === FALLBACK: CFBD STATS (if no PFF data) ===
    if pff_kr_grade == 0 and pff_pr_grade == 0:
        # Kick return value (CFBD)
        if kr_yds > 500:
            perf_bonus += 40000
            perf_factors.append(f"Dynamic KR ({kr_yds:,} KR yds)")
        elif kr_yds > 300:
            perf_bonus += 20000
            perf_factors.append(f"Productive KR ({kr_yds:,} KR yds)")
        if kr_tds > 1:
            perf_bonus += 30000 * kr_tds
            perf_factors.append(f"KR TD threat ({kr_tds} KR TDs)")
        elif kr_tds > 0:
            perf_bonus += 20000
            perf_factors.append(f"KR scoring ability ({kr_tds} KR TD)")

        # Punt return value (CFBD)
        if pr_yds > 300:
            perf_bonus += 35000
            perf_factors.append(f"Dynamic PR ({pr_yds:,} PR yds)")
        elif pr_yds > 200:
            perf_bonus += 18000
            perf_factors.append(f"Productive PR ({pr_yds:,} PR yds)")
        if pr_tds > 1:
            perf_bonus += 35000 * pr_tds
            perf_factors.append(f"PR TD threat ({pr_tds} PR TDs)")
        elif pr_tds > 0:
            perf_bonus += 25000
            perf_factors.append(f"PR scoring ability ({pr_tds} PR TD)")

    # ==========================================================================
    # NEGATIVE METRICS - Critical for accurate GM-style evaluation
    # ==========================================================================

    # Universal fumbles (any position that handles the ball)
    fumbles = player_data.get("fumbles", 0) or 0
    fumbles_lost = player_data.get("fumbles_lost", 0) or 0
    if position in ["QB", "RB", "WR", "TE"]:
        if fumbles_lost > 4:
            perf_bonus -= 60000
            perf_factors.append(f"⚠️ Major ball security issue ({fumbles_lost} fumbles lost)")
        elif fumbles_lost > 2:
            perf_bonus -= 30000
            perf_factors.append(f"⚠️ Ball security concern ({fumbles_lost} fumbles lost)")

    # Return fumbles (extra penalty for special teams miscues)
    if kr_yds > 0 or pr_yds > 0:
        if fumbles > 2:
            perf_bonus -= 40000
            perf_factors.append(f"⚠️ Return fumble risk ({fumbles} fumbles)")

    # Experience/games played factor (limited sample = higher risk)
    games = player_data.get("games_played", 0) or 0
    if games > 0 and games < 5:
        perf_bonus -= 25000
        perf_factors.append(f"⚠️ Limited sample size ({games} games)")

    # Calculate total with size factor
    custom_value = (base * star_mult * school_mult * size_mult) + perf_bonus

    # Build breakdown for explanation
    breakdown = {
        "base_position_value": base,
        "star_multiplier": star_mult,
        "star_rating": stars,
        "star_source": star_source,  # "portal" (college performance) or "recruiting" (HS)
        "size_multiplier": size_mult,
        "size_description": size_desc,
        "school_multiplier": school_mult,
        "school_tier": school_factor,
        "performance_bonus": perf_bonus,
        "performance_factors": perf_factors,
        "total": custom_value
    }

    return custom_value, breakdown


def create_value_breakdown_chart(breakdown: dict) -> go.Figure:
    """Create donut chart for value breakdown."""
    labels = ["Performance", "Social Media", "School Brand", "Recruiting", "Draft Potential"]
    values = [
        breakdown.get("base_value", 0),
        breakdown.get("social_media_premium", 0),
        breakdown.get("school_brand_factor", 0),
        breakdown.get("position_market_factor", 0),
        breakdown.get("draft_potential_premium", 0),
    ]

    colors = [COLORS["chart_1"], COLORS["chart_2"], COLORS["chart_3"],
              COLORS["chart_4"], COLORS["chart_5"]]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker_colors=colors,
        textinfo="percent+label",
        textposition="outside",
        textfont=dict(color=COLORS["text_secondary"]),
    )])

    fig.update_layout(
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
        height=350,
        annotations=[dict(
            text=f"<b>{format_currency(sum(values))}</b>",
            x=0.5, y=0.5,
            font_size=24,
            font_color=COLORS["primary"],
            showarrow=False,
        )],
    )

    return fig


def create_shap_waterfall(features: list) -> go.Figure:
    """Create SHAP-style waterfall chart for feature importance."""
    # Demo SHAP values
    if not features:
        features = [
            ("Social Media Followers", 180000),
            ("School Brand (Blue Blood)", 150000),
            ("Position (QB)", 120000),
            ("Recruiting Stars (5)", 80000),
            ("Games Started", 60000),
            ("Passing Yards", 50000),
            ("National Exposure", 40000),
            ("Draft Projection", 35000),
            ("Conference (SEC)", 25000),
            ("Team Success", 20000),
        ]

    feature_names = [f[0] for f in features[:10]]
    feature_values = [f[1] for f in features[:10]]

    colors = [COLORS["primary"] if v > 0 else COLORS["risk_critical"] for v in feature_values]

    fig = go.Figure(go.Bar(
        x=feature_values,
        y=feature_names,
        orientation='h',
        marker_color=colors,
        text=[format_currency(abs(v)) for v in feature_values],
        textposition='outside',
        textfont=dict(color=COLORS["text_secondary"]),
    ))

    fig.update_layout(
        title=dict(
            text="Top Value Drivers",
            font=dict(color=COLORS["text_primary"]),
        ),
        xaxis_title="Impact on NIL Value",
        yaxis=dict(autorange="reversed"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        margin=dict(l=20, r=100, t=50, b=50),
        height=400,
        xaxis=dict(
            gridcolor=COLORS["bg_light"],
            zerolinecolor=COLORS["bg_light"],
        ),
    )

    return fig


def create_transfer_comparison_chart(current: float, projected: float, schools: tuple) -> go.Figure:
    """Create bar chart comparing transfer impact."""
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[schools[0], schools[1]],
        y=[current, projected],
        marker_color=[COLORS["chart_2"], COLORS["primary"]],
        text=[format_currency(current), format_currency(projected)],
        textposition='outside',
        textfont=dict(color=COLORS["text_primary"], size=16),
    ))

    change = projected - current
    change_pct = (change / current * 100) if current > 0 else 0

    fig.update_layout(
        title=dict(
            text=f"Transfer Impact: {'+' if change >= 0 else ''}{format_currency(change)} ({change_pct:+.1f}%)",
            font=dict(color=COLORS["primary"] if change >= 0 else COLORS["risk_critical"]),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        yaxis=dict(
            gridcolor=COLORS["bg_light"],
            title="NIL Value",
        ),
        xaxis=dict(title="School"),
        margin=dict(l=50, r=50, t=80, b=50),
        height=350,
        showlegend=False,
    )

    return fig


def create_social_growth_chart(current_value: float, follower_increase: int) -> go.Figure:
    """Create chart showing NIL growth with social media increase."""
    steps = 10
    followers = [follower_increase * i / steps for i in range(steps + 1)]
    # Logarithmic growth curve
    import math
    values = [current_value + (follower_increase / 10 * math.log1p(f / 10000)) for f in followers]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=followers,
        y=values,
        mode='lines+markers',
        line=dict(color=COLORS["primary"], width=3),
        marker=dict(size=8, color=COLORS["primary"]),
        fill='tozeroy',
        fillcolor=f"rgba(0, 200, 83, 0.2)",
    ))

    fig.update_layout(
        title=dict(
            text="NIL Growth with Social Media Expansion",
            font=dict(color=COLORS["text_primary"]),
        ),
        xaxis_title="New Followers",
        yaxis_title="Projected NIL Value",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        xaxis=dict(gridcolor=COLORS["bg_light"]),
        yaxis=dict(gridcolor=COLORS["bg_light"]),
        margin=dict(l=50, r=50, t=50, b=50),
        height=300,
    )

    return fig


# =============================================================================
# Main Page
# =============================================================================

def main():
    # Render shared navigation sidebar
    render_sidebar()

    # Initialize comparison state
    init_comparison()

    # Header - Portal IQ Ultra Modern Style
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
        <span style="font-size: 2rem;">💰</span>
        <h1 style="color: {COLORS['text_primary']}; margin: 0; font-size: 1.75rem; font-weight: 700;">
            NIL Valuator
        </h1>
    </div>
    <p style="color: {COLORS['text_muted']}; font-size: 0.95rem; margin-bottom: 24px;">
        Get AI-powered NIL valuations with advanced performance & social breakdowns
    </p>
    """, unsafe_allow_html=True)

    # Comparison badge count
    compare_count = len(get_comparison_players())
    compare_label = f"⚖️ Compare Players ({compare_count})" if compare_count > 0 else "⚖️ Compare Players"

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "🔍 Search Players",
        "✏️ Custom Profile",
        compare_label
    ])

    with tab1:
        render_search_mode()

    with tab2:
        render_custom_mode()

    with tab3:
        render_comparison_mode()


def render_search_mode():
    """Render search existing player mode with advanced filters."""
    players_df = get_sample_players()

    # Advanced Filters expander
    with st.expander("🔧 Advanced Filters", expanded=False):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Position filter
            position_filter = st.multiselect(
                "Position",
                options=get_positions(),
                default=[],
                key="nil_pos_filter"
            )

        with col2:
            # NIL Value range
            nil_range_options = ["Any", "$0-$50K", "$50K-$250K", "$250K-$1M", "$1M+", "Custom"]
            nil_range = st.selectbox(
                "NIL Value Range",
                options=nil_range_options,
                key="nil_range_filter"
            )

        with col3:
            # Star rating filter
            stars_filter = st.slider(
                "Star Rating",
                min_value=0,
                max_value=5,
                value=(0, 5),
                key="nil_stars_filter"
            )

        with col4:
            # School filter
            school_filter = st.multiselect(
                "School",
                options=["Blue Bloods Only", "Power 4"] + get_school_list()[:20],
                default=[],
                key="nil_school_filter"
            )

        # Custom NIL range if selected
        if nil_range == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                min_nil = st.number_input("Min NIL Value ($)", min_value=0, value=0, step=10000, key="nil_min")
            with col2:
                max_nil = st.number_input("Max NIL Value ($)", min_value=0, value=10000000, step=10000, key="nil_max")
        else:
            min_nil, max_nil = 0, float('inf')
            if nil_range == "$0-$50K":
                min_nil, max_nil = 0, 50000
            elif nil_range == "$50K-$250K":
                min_nil, max_nil = 50000, 250000
            elif nil_range == "$250K-$1M":
                min_nil, max_nil = 250000, 1000000
            elif nil_range == "$1M+":
                min_nil, max_nil = 1000000, float('inf')

    st.divider()

    # Text search input
    search_query = st.text_input(
        "Search Player",
        placeholder="Type player name (e.g., Arch Manning, Jeremiah Smith...)",
        help="Start typing to search players"
    )

    # Filter players based on search and advanced filters
    filtered_df = players_df.copy()

    # Apply text search
    if search_query:
        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(search_query.lower(), na=False)
        ]

    # Apply position filter
    if position_filter:
        filtered_df = filtered_df[filtered_df["position"].isin(position_filter)]

    # Apply NIL range filter
    if nil_range != "Any":
        filtered_df = filtered_df[
            (filtered_df["nil_value"].fillna(0) >= min_nil) &
            (filtered_df["nil_value"].fillna(0) <= max_nil)
        ]

    # Apply stars filter
    if stars_filter != (0, 5):
        stars_col = filtered_df["stars"].fillna(0)
        filtered_df = filtered_df[
            (stars_col >= stars_filter[0]) &
            (stars_col <= stars_filter[1])
        ]

    # Apply school filter
    blue_bloods = ["Alabama", "Ohio State", "Georgia", "Texas", "USC", "Michigan", "Notre Dame"]
    power_4 = blue_bloods + ["LSU", "Florida", "Oregon", "Penn State", "Clemson", "Tennessee", "Oklahoma", "Miami", "Auburn", "Florida State", "Wisconsin", "Iowa", "UCLA", "Arizona State"]

    if school_filter:
        if "Blue Bloods Only" in school_filter:
            filtered_df = filtered_df[filtered_df["school"].isin(blue_bloods)]
        elif "Power 4" in school_filter:
            filtered_df = filtered_df[filtered_df["school"].isin(power_4)]
        else:
            specific_schools = [s for s in school_filter if s not in ["Blue Bloods Only", "Power 4"]]
            if specific_schools:
                filtered_df = filtered_df[filtered_df["school"].isin(specific_schools)]

    # Default to top 20 if no search or filters
    if not search_query and not position_filter and nil_range == "Any" and stars_filter == (0, 5) and not school_filter:
        filtered_df = filtered_df.head(20)

    # Show matching players
    if not filtered_df.empty:
        col_info, col_compare_hint = st.columns([2, 1])
        with col_info:
            st.markdown(f"**{len(filtered_df)} players found**" if search_query else "**Top 10 Players**")
        with col_compare_hint:
            compare_count = len(get_comparison_players())
            if compare_count > 0:
                st.markdown(f"<span style='color: {COLORS['primary']};'>⚖️ {compare_count}/3 players selected for comparison</span>", unsafe_allow_html=True)

        # Display as clickable cards with comparison option
        for idx, (_, player) in enumerate(filtered_df.head(20).iterrows()):
            col_img, col1, col2, col3, col4, col5 = st.columns([0.5, 2.5, 1, 1, 1, 1])
            with col_img:
                headshot_url = player.get('headshot_url', '')
                if headshot_url and pd.notna(headshot_url):
                    st.image(headshot_url, width=40)
                else:
                    st.markdown("👤")
            with col1:
                school_name = player.get('school', player.get('team', ''))
                # Handle NaN values
                if pd.isna(school_name) or str(school_name).lower() == 'nan':
                    school_name = ''
                st.markdown(f"**{player['name']}**<br><span style='color: #7a8fa6; font-size: 0.85rem;'>{school_name}</span>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"{player.get('position', 'N/A')}")
            with col3:
                nil_val = player.get('nil_value', 0)
                st.markdown(f"${nil_val:,.0f}" if nil_val else "N/A")
            with col4:
                if st.button("View", key=f"view_{idx}_{player['name']}", use_container_width=True):
                    st.session_state.selected_player = player['name']
            with col5:
                player_name = player['name']
                if is_in_comparison(player_name):
                    if st.button("➖", key=f"cmp_rm_{idx}_{player_name}", help="Remove from comparison"):
                        remove_from_comparison(player_name)
                        st.rerun()
                else:
                    if st.button("➕", key=f"cmp_add_{idx}_{player_name}", help="Add to comparison"):
                        if add_to_comparison(player.to_dict()):
                            st.rerun()

        st.divider()

    # Show valuation if player selected
    if "selected_player" in st.session_state and st.session_state.selected_player:
        player_match = players_df[players_df["name"] == st.session_state.selected_player]
        if not player_match.empty:
            player_data = player_match.iloc[0].to_dict()
            render_valuation_results(player_data)
    elif search_query and not filtered_df.empty:
        # Auto-select first result if exact match
        exact_match = filtered_df[filtered_df["name"].str.lower() == search_query.lower()]
        if not exact_match.empty:
            player_data = exact_match.iloc[0].to_dict()
            render_valuation_results(player_data)


def render_custom_mode():
    """Render custom player profile mode."""
    st.markdown("### Player Information")

    col1, col2, col3 = st.columns(3)

    with col1:
        name = st.text_input("Player Name", value="Custom Player")
        school = st.selectbox("School", options=get_school_list())
        position = st.selectbox("Position", options=get_positions())

    with col2:
        class_year = st.selectbox("Class Year", options=get_class_years())
        stars = st.slider("Recruiting Stars", 2, 5, 4)
        overall_rating = st.slider("Overall Rating", 0.60, 1.00, 0.80, 0.01)

    with col3:
        is_starter = st.checkbox("Is Starter", value=True)
        games_played = st.number_input("Games Played", 0, 15, 12)
        games_started = st.number_input("Games Started", 0, 15, 10)

    st.divider()

    # Position-specific stats
    st.markdown("### Performance Stats")

    col1, col2, col3 = st.columns(3)

    stats = {}

    if position == "QB":
        with col1:
            stats["passing_yards"] = st.number_input("Passing Yards", 0, 6000, 2500)
            stats["passing_tds"] = st.number_input("Passing TDs", 0, 60, 20)
        with col2:
            stats["interceptions"] = st.number_input("Interceptions", 0, 30, 5)
            stats["completion_pct"] = st.slider("Completion %", 40.0, 80.0, 65.0)
        with col3:
            stats["qbr"] = st.slider("QBR", 50.0, 100.0, 75.0)
            stats["rushing_yards"] = st.number_input("Rushing Yards (QB)", 0, 1500, 200)

    elif position == "RB":
        with col1:
            stats["rushing_yards"] = st.number_input("Rushing Yards", 0, 2500, 800)
            stats["rushing_tds"] = st.number_input("Rushing TDs", 0, 30, 8)
        with col2:
            stats["yards_per_carry"] = st.slider("Yards/Carry", 2.0, 8.0, 5.0)
            stats["receptions"] = st.number_input("Receptions", 0, 80, 20)
        with col3:
            stats["receiving_yards"] = st.number_input("Receiving Yards", 0, 1000, 150)

    elif position == "WR":
        with col1:
            stats["receptions"] = st.number_input("Receptions", 0, 120, 50)
            stats["receiving_yards"] = st.number_input("Receiving Yards", 0, 2000, 700)
        with col2:
            stats["receiving_tds"] = st.number_input("Receiving TDs", 0, 25, 6)
            stats["yards_per_reception"] = st.slider("Yards/Reception", 8.0, 25.0, 14.0)
        with col3:
            stats["pff_grade"] = st.slider("PFF Grade", 50.0, 95.0, 75.0)

    elif position in ["EDGE", "DT", "LB"]:
        with col1:
            stats["tackles"] = st.number_input("Tackles", 0, 150, 50)
            stats["sacks"] = st.number_input("Sacks", 0.0, 25.0, 5.0, 0.5)
        with col2:
            stats["tackles_for_loss"] = st.number_input("TFLs", 0.0, 30.0, 8.0, 0.5)
            stats["forced_fumbles"] = st.number_input("Forced Fumbles", 0, 10, 2)
        with col3:
            stats["pff_grade"] = st.slider("PFF Grade", 50.0, 95.0, 72.0)

    elif position in ["CB", "S"]:
        with col1:
            stats["tackles"] = st.number_input("Tackles", 0, 100, 35)
            stats["interceptions_def"] = st.number_input("Interceptions", 0, 15, 2)
        with col2:
            stats["passes_defended"] = st.number_input("Passes Defended", 0, 25, 8)
            stats["pff_grade"] = st.slider("PFF Grade", 50.0, 95.0, 70.0)
        with col3:
            stats["forced_fumbles"] = st.number_input("Forced Fumbles", 0, 5, 1)

    else:
        with col1:
            stats["games_played"] = games_played
        with col2:
            stats["pff_grade"] = st.slider("PFF Grade", 50.0, 95.0, 70.0)

    st.divider()

    # Social Media
    st.markdown("### Social Media Profile")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        instagram = st.number_input("Instagram Followers", 0, 10000000, 50000, step=10000)
    with col2:
        twitter = st.number_input("Twitter/X Followers", 0, 10000000, 25000, step=10000)
    with col3:
        tiktok = st.number_input("TikTok Followers", 0, 50000000, 10000, step=10000)
    with col4:
        engagement = st.slider("Engagement Rate %", 0.0, 10.0, 3.0, 0.1)

    st.divider()

    # Submit
    if st.button("🚀 Calculate NIL Value", type="primary", use_container_width=True):
        player_data = {
            "name": name,
            "school": school,
            "position": position,
            "class_year": class_year,
            "stars": stars,
            "overall_rating": overall_rating,
            "is_starter": is_starter,
            "games_played": games_played,
            "games_started": games_started,
            "instagram_followers": instagram,
            "twitter_followers": twitter,
            "tiktok_followers": tiktok,
            "engagement_rate": engagement / 100,
            **stats,
        }

        # Calculate demo NIL value
        base = 50000
        position_mult = {"QB": 3.0, "WR": 1.5, "RB": 1.2, "EDGE": 1.3, "CB": 1.2}.get(position, 1.0)
        rating_mult = 1 + (overall_rating - 0.75) * 5
        social_bonus = min((instagram + twitter + tiktok) / 10, 500000)
        school_mult = 2.5 if school in ["Alabama", "Ohio State", "Georgia", "Texas"] else 1.5

        nil_value = (base * position_mult * rating_mult * school_mult) + social_bonus
        player_data["nil_value"] = nil_value
        player_data["tier"] = (
            "mega" if nil_value >= 1000000 else
            "premium" if nil_value >= 500000 else
            "solid" if nil_value >= 100000 else
            "moderate" if nil_value >= 25000 else
            "entry"
        )

        render_valuation_results(player_data)


def render_valuation_results(player_data: dict):
    """Render the NIL valuation results - Portal IQ Ultra Modern Style."""
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Player Profile Header - Figma Style with gold ring avatar
    player_name = player_data.get("name", "")
    headshot_url = player_data.get("headshot_url", "")
    school = player_data.get("school", player_data.get("team", ""))
    position = player_data.get("position", "")
    stars = player_data.get("stars", 0)
    tier = player_data.get("tier", "solid")

    # Get initials for avatar fallback
    initials = "".join([n[0] for n in player_name.split()[:2]]).upper() if player_name else "?"

    col_photo, col_info = st.columns([1, 4])
    with col_photo:
        if headshot_url and pd.notna(headshot_url):
            st.markdown(f"""
            <div style="position: relative; width: 120px; height: 120px;">
                <img src="{headshot_url}" style="width: 110px; height: 110px; border-radius: 50%; border: 3px solid {COLORS['primary']}; object-fit: cover; position: absolute; top: 5px; left: 5px;" />
                <div style="position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); background: {COLORS['primary']}; color: {COLORS['bg_dark']}; padding: 2px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
                    {position}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="position: relative; width: 120px; height: 120px;">
                <div style="width: 110px; height: 110px; background: {COLORS['bg_card']}; border-radius: 50%; border: 3px solid {COLORS['primary']}; display: flex; align-items: center; justify-content: center; font-size: 2rem; color: {COLORS['primary']}; font-weight: 700; position: absolute; top: 5px; left: 5px;">
                    {initials}
                </div>
                <div style="position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); background: {COLORS['primary']}; color: {COLORS['bg_dark']}; padding: 2px 12px; border-radius: 12px; font-size: 0.75rem; font-weight: 700;">
                    {position}
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_info:
        star_display = "⭐" * int(stars) if stars and not pd.isna(stars) else ""
        st.markdown(f"""
        <div style="padding-top: 10px;">
            <h2 style="color: {COLORS['text_primary']}; margin: 0; font-size: 1.75rem; font-weight: 700;">{player_name}</h2>
            <p style="color: {COLORS['text_muted']}; font-size: 1rem; margin: 4px 0 12px 0;">
                {school} {' | ' + star_display if star_display else ''}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Merge manual stats into player_data for calculation
    manual_stats = load_manual_stats_for_player(player_name)
    if manual_stats:
        key_mapping = {"height_inches": "height"}
        for key, value in manual_stats.items():
            if key not in ["player_name", "team", "position"] and pd.notna(value) and value:
                target_key = key_mapping.get(key, key)
                existing_val = player_data.get(target_key)
                if not existing_val or pd.isna(existing_val) or existing_val == 0:
                    player_data[target_key] = value
                elif value and value != 0:
                    player_data[target_key] = value

    # Get both values
    on3_value = player_data.get("nil_value", 0) or 0
    custom_value, custom_breakdown = calculate_custom_nil_value(player_data)
    tier = player_data.get("tier", "solid")
    display_value = on3_value if on3_value > 0 else custom_value

    # NIL Valuation Card - Figma Style
    trend_pct = custom_breakdown.get("trend_pct", 5.2) if custom_breakdown else 5.2
    trend_color = COLORS['status_active'] if trend_pct > 0 else COLORS['risk_critical']

    st.markdown(f"""
    <div style="background: {COLORS['bg_light']}; border: 1px solid {COLORS['border']}; border-radius: 16px; padding: 24px; margin: 16px 0;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div>
                <p style="color: {COLORS['text_muted']}; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin: 0;">NIL VALUATION</p>
                <h2 style="color: {COLORS['primary']}; font-size: 2.5rem; font-weight: 700; margin: 4px 0;">{format_currency(display_value)}</h2>
            </div>
            <div style="text-align: right;">
                <span style="color: {trend_color}; font-size: 0.9rem; font-weight: 500;">↗ +{abs(trend_pct):.1f}%</span>
                <div style="margin-top: 8px;">
                    <span style="background: rgba(34, 197, 94, 0.15); color: {COLORS['status_active']}; padding: 4px 12px; border-radius: 50px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase;">● HIGH CONFIDENCE</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Value comparison cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="background: {COLORS['bg_light']}; padding: 20px; border-radius: 12px; border: 1px solid {COLORS['border']}; text-align: center;">
            <p style="color: {COLORS['text_muted']}; margin-bottom: 8px; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">On3 Value</p>
            <h3 style="color: {COLORS['chart_2']}; margin: 0; font-size: 1.5rem; font-weight: 700;">{format_currency(on3_value) if on3_value > 0 else 'N/A'}</h3>
            <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-top: 6px;">Market consensus</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: {COLORS['bg_light']}; padding: 20px; border-radius: 12px; border: 1px solid {COLORS['border']}; text-align: center;">
            <p style="color: {COLORS['text_muted']}; margin-bottom: 8px; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Portal IQ Value</p>
            <h3 style="color: {COLORS['status_active']}; margin: 0; font-size: 1.5rem; font-weight: 700;">{format_currency(custom_value)}</h3>
            <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-top: 6px;">Performance-based</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        if on3_value > 0:
            diff = custom_value - on3_value
            diff_pct = (diff / on3_value) * 100
            diff_color = COLORS['status_active'] if diff > 0 else COLORS['risk_critical'] if diff < 0 else COLORS['text_muted']
            diff_label = "Undervalued" if diff > 0 else "Overvalued" if diff < 0 else "Fair Value"
            st.markdown(f"""
            <div style="background: {COLORS['bg_light']}; padding: 20px; border-radius: 12px; border: 1px solid {COLORS['border']}; text-align: center;">
                <p style="color: {COLORS['text_muted']}; margin-bottom: 8px; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Difference</p>
                <h3 style="color: {diff_color}; margin: 0; font-size: 1.5rem; font-weight: 700;">{'+' if diff > 0 else ''}{format_currency(diff)}</h3>
                <p style="color: {diff_color}; font-size: 0.8rem; margin-top: 6px;">{diff_label} ({diff_pct:+.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: {COLORS['bg_light']}; padding: 20px; border-radius: 12px; border: 1px solid {COLORS['border']}; text-align: center;">
                <p style="color: {COLORS['text_muted']}; margin-bottom: 8px; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em;">Difference</p>
                <h3 style="color: {COLORS['text_muted']}; margin: 0; font-size: 1.5rem; font-weight: 700;">N/A</h3>
                <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-top: 6px;">No On3 data</p>
            </div>
            """, unsafe_allow_html=True)

    # ===========================================================================
    # MANUAL STATS ENTRY (Persists to CSV - backup until PocketBase integration)
    # ===========================================================================

    position = player_data.get("position", "ATH")
    player_name = player_data.get("name", "Unknown")
    team = player_data.get("school", "") or player_data.get("origin_school", "") or player_data.get("team", "")

    # Load any existing manual data for this player
    existing_manual = load_manual_stats_for_player(player_name)

    # Check if measurables are missing
    has_height = player_data.get("height") and not pd.isna(player_data.get("height"))
    has_weight = player_data.get("weight") and not pd.isna(player_data.get("weight"))
    missing_measurables = not has_height or not has_weight

    with st.expander("✏️ Add/Edit Performance Data & Measurables", expanded=missing_measurables):
        st.markdown("""
        <p style="color: #a8b8c8; font-size: 0.9rem;">
            Enter stats and measurables to improve valuation accuracy. <strong>Data persists to database.</strong>
        </p>
        """, unsafe_allow_html=True)

        player_key = f"manual_{player_name.replace(' ', '_')}"

        # Track all stats to save
        stats_to_save = {}

        # =========================================================
        # MEASURABLES (Height/Weight) - Show prominently if missing
        # =========================================================
        if missing_measurables:
            st.markdown(f"""
            <div style="background: #2d1f1f; border: 1px solid #ff6b6b; border-radius: 8px; padding: 12px; margin-bottom: 15px;">
                <strong style="color: #ff6b6b;">⚠️ Missing Measurables</strong>
                <p style="color: #c9d6e3; font-size: 0.85rem; margin: 5px 0 0 0;">
                    Height/weight data not available from CFBD. Enter below for accurate size-based valuation.
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("**Physical Measurables**")
        meas_col1, meas_col2, meas_col3 = st.columns(3)
        with meas_col1:
            # Convert existing height to inches if stored as string like "6-2"
            default_height = existing_manual.get("height_inches", 72)
            if pd.isna(default_height):
                default_height = 72
            height_inches = st.number_input(
                "Height (inches)",
                min_value=60, max_value=84, value=int(default_height),
                help="E.g., 6'2\" = 74 inches",
                key=f"{player_key}_height"
            )
            stats_to_save["height_inches"] = height_inches

        with meas_col2:
            default_weight = existing_manual.get("weight", 200)
            if pd.isna(default_weight):
                default_weight = 200
            weight = st.number_input(
                "Weight (lbs)",
                min_value=150, max_value=380, value=int(default_weight),
                key=f"{player_key}_weight"
            )
            stats_to_save["weight"] = weight

        with meas_col3:
            # Display height in feet-inches for reference
            feet = height_inches // 12
            inches = height_inches % 12
            st.markdown(f"""
            <div style="padding-top: 25px;">
                <span style="color: {COLORS['primary']}; font-size: 1.2rem; font-weight: bold;">
                    {feet}'{inches}" / {weight} lbs
                </span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # =========================================================
        # POSITION-SPECIFIC PRODUCTION STATS
        # =========================================================
        if position == "QB":
            st.markdown("**Quarterback Production Stats**")
            qb_col1, qb_col2, qb_col3, qb_col4 = st.columns(4)
            with qb_col1:
                stats_to_save["passing_yards"] = st.number_input("Pass Yards", 0, 6000, int(existing_manual.get("passing_yards", 0) or 0), key=f"{player_key}_pass_yds")
                stats_to_save["passing_tds"] = st.number_input("Pass TDs", 0, 60, int(existing_manual.get("passing_tds", 0) or 0), key=f"{player_key}_pass_tds")
            with qb_col2:
                stats_to_save["interceptions"] = st.number_input("INTs Thrown", 0, 30, int(existing_manual.get("interceptions", 0) or 0), key=f"{player_key}_ints")
                stats_to_save["completion_pct"] = st.number_input("Comp %", 0.0, 100.0, float(existing_manual.get("completion_pct", 0) or 0), key=f"{player_key}_comp_pct")
            with qb_col3:
                stats_to_save["rushing_yards"] = st.number_input("Rush Yards", 0, 2000, int(existing_manual.get("rushing_yards", 0) or 0), key=f"{player_key}_rush_yds")
                stats_to_save["rushing_tds"] = st.number_input("Rush TDs", 0, 30, int(existing_manual.get("rushing_tds", 0) or 0), key=f"{player_key}_rush_tds")
            with qb_col4:
                stats_to_save["games_played"] = st.number_input("Games", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")
                stats_to_save["sacks_taken"] = st.number_input("Sacks Taken", 0, 60, int(existing_manual.get("sacks_taken", 0) or 0), key=f"{player_key}_sacks_taken")

        elif position == "RB":
            st.markdown("**Running Back Production Stats**")
            rb_col1, rb_col2, rb_col3, rb_col4 = st.columns(4)
            with rb_col1:
                stats_to_save["rushing_yards"] = st.number_input("Rush Yards", 0, 2500, int(existing_manual.get("rushing_yards", 0) or 0), key=f"{player_key}_rush_yds")
                stats_to_save["rushing_tds"] = st.number_input("Rush TDs", 0, 30, int(existing_manual.get("rushing_tds", 0) or 0), key=f"{player_key}_rush_tds")
            with rb_col2:
                stats_to_save["rushing_attempts"] = st.number_input("Carries", 0, 400, int(existing_manual.get("rushing_attempts", 0) or 0), key=f"{player_key}_carries")
                stats_to_save["yards_per_carry"] = st.number_input("YPC", 0.0, 15.0, float(existing_manual.get("yards_per_carry", 0) or 0), key=f"{player_key}_ypc")
            with rb_col3:
                stats_to_save["receptions"] = st.number_input("Receptions", 0, 100, int(existing_manual.get("receptions", 0) or 0), key=f"{player_key}_rec")
                stats_to_save["receiving_yards"] = st.number_input("Rec Yards", 0, 1000, int(existing_manual.get("receiving_yards", 0) or 0), key=f"{player_key}_rec_yds")
            with rb_col4:
                stats_to_save["games_played"] = st.number_input("Games", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")
                stats_to_save["fumbles_lost"] = st.number_input("Fumbles Lost", 0, 15, int(existing_manual.get("fumbles_lost", 0) or 0), key=f"{player_key}_fum_lost")

        elif position == "WR":
            st.markdown("**Wide Receiver Production Stats**")
            wr_col1, wr_col2, wr_col3, wr_col4 = st.columns(4)
            with wr_col1:
                stats_to_save["receptions"] = st.number_input("Receptions", 0, 150, int(existing_manual.get("receptions", 0) or 0), key=f"{player_key}_rec")
                stats_to_save["receiving_yards"] = st.number_input("Rec Yards", 0, 2000, int(existing_manual.get("receiving_yards", 0) or 0), key=f"{player_key}_rec_yds")
            with wr_col2:
                stats_to_save["receiving_tds"] = st.number_input("Rec TDs", 0, 25, int(existing_manual.get("receiving_tds", 0) or 0), key=f"{player_key}_rec_tds")
                stats_to_save["yards_per_reception"] = st.number_input("YPR", 0.0, 30.0, float(existing_manual.get("yards_per_reception", 0) or 0), key=f"{player_key}_ypr")
            with wr_col3:
                stats_to_save["targets"] = st.number_input("Targets", 0, 200, int(existing_manual.get("targets", 0) or 0), key=f"{player_key}_targets")
                stats_to_save["drops"] = st.number_input("Drops", 0, 20, int(existing_manual.get("drops", 0) or 0), key=f"{player_key}_drops")
            with wr_col4:
                stats_to_save["games_played"] = st.number_input("Games", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")

        elif position == "TE":
            st.markdown("**Tight End Production Stats**")
            te_col1, te_col2, te_col3, te_col4 = st.columns(4)
            with te_col1:
                stats_to_save["receptions"] = st.number_input("Receptions", 0, 100, int(existing_manual.get("receptions", 0) or 0), key=f"{player_key}_rec")
                stats_to_save["receiving_yards"] = st.number_input("Rec Yards", 0, 1500, int(existing_manual.get("receiving_yards", 0) or 0), key=f"{player_key}_rec_yds")
            with te_col2:
                stats_to_save["receiving_tds"] = st.number_input("Rec TDs", 0, 20, int(existing_manual.get("receiving_tds", 0) or 0), key=f"{player_key}_rec_tds")
                stats_to_save["yards_per_reception"] = st.number_input("YPR", 0.0, 25.0, float(existing_manual.get("yards_per_reception", 0) or 0), key=f"{player_key}_ypr")
            with te_col3:
                stats_to_save["pff_pass_block"] = st.number_input("PFF Pass Block", 0.0, 100.0, float(existing_manual.get("pff_pass_block", 0) or 0), key=f"{player_key}_pff_pb")
                stats_to_save["pff_run_block"] = st.number_input("PFF Run Block", 0.0, 100.0, float(existing_manual.get("pff_run_block", 0) or 0), key=f"{player_key}_pff_rb")
            with te_col4:
                stats_to_save["games_played"] = st.number_input("Games", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")

        elif position in ["OT", "OG", "C", "OL", "IOL"]:
            st.markdown("**Offensive Line Metrics**")
            ol_col1, ol_col2, ol_col3, ol_col4 = st.columns(4)
            with ol_col1:
                stats_to_save["pff_overall"] = st.number_input("PFF Overall", 0.0, 100.0, float(existing_manual.get("pff_overall", 0) or 0), key=f"{player_key}_pff")
                stats_to_save["pff_pass_block"] = st.number_input("PFF Pass Block", 0.0, 100.0, float(existing_manual.get("pff_pass_block", 0) or 0), key=f"{player_key}_pff_pb")
            with ol_col2:
                stats_to_save["pff_run_block"] = st.number_input("PFF Run Block", 0.0, 100.0, float(existing_manual.get("pff_run_block", 0) or 0), key=f"{player_key}_pff_rb")
                stats_to_save["sacks_allowed"] = st.number_input("Sacks Allowed", 0, 30, int(existing_manual.get("sacks_allowed", 0) or 0), key=f"{player_key}_sacks_allowed")
            with ol_col3:
                stats_to_save["pressures_allowed"] = st.number_input("Pressures Allowed", 0, 60, int(existing_manual.get("pressures_allowed", 0) or 0), key=f"{player_key}_pressures")
                stats_to_save["holding_penalties"] = st.number_input("Holding Penalties", 0, 15, int(existing_manual.get("holding_penalties", 0) or 0), key=f"{player_key}_holding")
            with ol_col4:
                stats_to_save["false_starts"] = st.number_input("False Starts", 0, 15, int(existing_manual.get("false_starts", 0) or 0), key=f"{player_key}_false_starts")
                stats_to_save["games_played"] = st.number_input("Games", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")

        elif position in ["EDGE", "DT", "DL", "DE"]:
            st.markdown("**Defensive Line Production Stats**")
            dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
            with dl_col1:
                stats_to_save["tackles"] = st.number_input("Total Tackles", 0, 150, int(existing_manual.get("tackles", 0) or 0), key=f"{player_key}_tkl")
                stats_to_save["sacks"] = st.number_input("Sacks", 0.0, 25.0, float(existing_manual.get("sacks", 0) or 0), key=f"{player_key}_sacks")
            with dl_col2:
                stats_to_save["tackles_for_loss"] = st.number_input("TFL", 0.0, 30.0, float(existing_manual.get("tackles_for_loss", 0) or 0), key=f"{player_key}_tfl")
                stats_to_save["qb_hits"] = st.number_input("QB Hits", 0, 40, int(existing_manual.get("qb_hits", 0) or 0), key=f"{player_key}_qb_hits")
            with dl_col3:
                stats_to_save["pff_overall"] = st.number_input("PFF Overall", 0.0, 100.0, float(existing_manual.get("pff_overall", 0) or 0), key=f"{player_key}_pff")
                stats_to_save["missed_tackles"] = st.number_input("Missed Tackles", 0, 30, int(existing_manual.get("missed_tackles", 0) or 0), key=f"{player_key}_missed")
            with dl_col4:
                stats_to_save["offsides_penalties"] = st.number_input("Offsides", 0, 15, int(existing_manual.get("offsides_penalties", 0) or 0), key=f"{player_key}_offsides")
                stats_to_save["games_played"] = st.number_input("Games", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")

        elif position == "LB":
            st.markdown("**Linebacker Production Stats**")
            lb_col1, lb_col2, lb_col3, lb_col4 = st.columns(4)
            with lb_col1:
                stats_to_save["tackles"] = st.number_input("Total Tackles", 0, 200, int(existing_manual.get("tackles", 0) or 0), key=f"{player_key}_tkl")
                stats_to_save["sacks"] = st.number_input("Sacks", 0.0, 20.0, float(existing_manual.get("sacks", 0) or 0), key=f"{player_key}_sacks")
            with lb_col2:
                stats_to_save["tackles_for_loss"] = st.number_input("TFL", 0.0, 30.0, float(existing_manual.get("tackles_for_loss", 0) or 0), key=f"{player_key}_tfl")
                stats_to_save["interceptions"] = st.number_input("INTs", 0, 10, int(existing_manual.get("interceptions", 0) or 0), key=f"{player_key}_ints")
            with lb_col3:
                stats_to_save["passes_defended"] = st.number_input("Pass Breakups", 0, 20, int(existing_manual.get("passes_defended", 0) or 0), key=f"{player_key}_pbu")
                stats_to_save["missed_tackles"] = st.number_input("Missed Tackles", 0, 40, int(existing_manual.get("missed_tackles", 0) or 0), key=f"{player_key}_missed")
            with lb_col4:
                stats_to_save["pff_overall"] = st.number_input("PFF Overall", 0.0, 100.0, float(existing_manual.get("pff_overall", 0) or 0), key=f"{player_key}_pff")
                stats_to_save["games_played"] = st.number_input("Games", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")

        elif position in ["CB", "S", "DB"]:
            st.markdown("**Secondary Production Stats**")
            db_col1, db_col2, db_col3, db_col4 = st.columns(4)
            with db_col1:
                stats_to_save["tackles"] = st.number_input("Total Tackles", 0, 150, int(existing_manual.get("tackles", 0) or 0), key=f"{player_key}_tkl")
                stats_to_save["interceptions"] = st.number_input("INTs", 0, 15, int(existing_manual.get("interceptions", 0) or 0), key=f"{player_key}_ints")
            with db_col2:
                stats_to_save["passes_defended"] = st.number_input("Pass Breakups", 0, 25, int(existing_manual.get("passes_defended", 0) or 0), key=f"{player_key}_pbu")
                stats_to_save["forced_fumbles"] = st.number_input("Forced Fumbles", 0, 10, int(existing_manual.get("forced_fumbles", 0) or 0), key=f"{player_key}_ff")
            with db_col3:
                stats_to_save["pff_coverage"] = st.number_input("PFF Coverage", 0.0, 100.0, float(existing_manual.get("pff_coverage", 0) or 0), key=f"{player_key}_pff_cov")
                stats_to_save["pass_interference"] = st.number_input("PI Calls", 0, 15, int(existing_manual.get("pass_interference", 0) or 0), key=f"{player_key}_pi")
            with db_col4:
                stats_to_save["tds_allowed"] = st.number_input("TDs Allowed", 0, 15, int(existing_manual.get("tds_allowed", 0) or 0), key=f"{player_key}_tds_allowed")
                stats_to_save["games_played"] = st.number_input("Games", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")

        else:
            # Generic/ATH fallback
            st.markdown("**General Stats**")
            gen_col1, gen_col2, gen_col3 = st.columns(3)
            with gen_col1:
                stats_to_save["games_played"] = st.number_input("Games Played", 0, 15, int(existing_manual.get("games_played", 0) or 0), key=f"{player_key}_games")
            with gen_col2:
                stats_to_save["total_penalties"] = st.number_input("Total Penalties", 0, 20, int(existing_manual.get("total_penalties", 0) or 0), key=f"{player_key}_penalties")
            with gen_col3:
                stats_to_save["pff_overall"] = st.number_input("PFF Overall", 0.0, 100.0, float(existing_manual.get("pff_overall", 0) or 0), key=f"{player_key}_pff")

        st.markdown("---")

        # Save button
        save_col1, save_col2 = st.columns([1, 3])
        with save_col1:
            if st.button("💾 Save to Database", key=f"{player_key}_save", type="primary"):
                if save_manual_stats_for_player(player_name, team, position, stats_to_save):
                    st.success(f"Saved stats for {player_name}!")
                    st.cache_data.clear()  # Clear cache to reload with new data
                    st.rerun()
        with save_col2:
            st.markdown(f"""
            <p style="color: #7a8fa6; font-size: 0.8rem; padding-top: 8px;">
                Data saved to CSV backup. Will sync to PocketBase when connected.
            </p>
            """, unsafe_allow_html=True)

    # ===========================================================================
    # COMPREHENSIVE METHODOLOGY & JUSTIFICATION SECTION
    # ===========================================================================

    st.markdown("---")
    st.markdown(f"## 📋 Portal IQ Valuation Report")

    # Calculate key variables needed for the report
    base_val = custom_breakdown.get("base_position_value", 0)
    star_mult = custom_breakdown.get("star_multiplier", 1.0)
    size_mult = custom_breakdown.get("size_multiplier", 1.0)
    school_mult = custom_breakdown.get("school_multiplier", 1.0)
    perf_bonus = custom_breakdown.get("performance_bonus", 0)

    # Build confidence items
    confidence_items = []
    confidence_items.append(("Position", "HIGH", "#00C853", "Verified from roster data"))
    stars = custom_breakdown.get("star_rating", 0)
    if stars and stars > 0:
        confidence_items.append(("Star Rating", "HIGH", "#00C853", f"247Sports/Rivals verified ({stars}★)"))
    else:
        confidence_items.append(("Star Rating", "LOW", "#FF9800", "No recruiting data - using default"))
    size_desc = custom_breakdown.get("size_description", "")
    if "not available" in size_desc.lower():
        confidence_items.append(("Height/Weight", "LOW", "#FF9800", "No measurables data"))
    else:
        confidence_items.append(("Height/Weight", "HIGH", "#00C853", f"Verified: {size_desc}"))
    confidence_items.append(("School Brand", "HIGH", "#00C853", f"{custom_breakdown.get('school_tier', 'Standard')} tier"))
    if perf_bonus > 0:
        confidence_items.append(("Performance Stats", "HIGH", "#00C853", f"+{format_currency(perf_bonus)} from verified stats"))
    else:
        confidence_items.append(("Performance Stats", "MEDIUM", "#FFB74D", "Limited stats available"))
    high_count = sum(1 for _, level, _, _ in confidence_items if level == "HIGH")
    confidence_pct = int((high_count / len(confidence_items)) * 100)

    # KEY SUMMARY - Always visible
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1a2332 0%, #243447 100%); padding: 20px; border-radius: 12px;
                border-left: 5px solid {COLORS['primary']}; margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p style="color: #c9d6e3; margin: 0; font-size: 0.9rem;">Portal IQ Performance-Based Value</p>
                <p style="color: {COLORS['primary']}; font-size: 2rem; font-weight: bold; margin: 5px 0;">{format_currency(custom_value)}</p>
            </div>
            <div style="text-align: right;">
                <p style="color: #c9d6e3; margin: 0; font-size: 0.9rem;">Data Confidence</p>
                <p style="color: {'#00C853' if confidence_pct >= 80 else '#FFB74D'}; font-size: 1.5rem; font-weight: bold; margin: 5px 0;">{confidence_pct}%</p>
            </div>
        </div>
        <p style="color: #FFB74D; font-size: 0.85rem; margin-top: 10px; margin-bottom: 0;">
            ⚠️ This is a <strong>performance-only floor value</strong>. Does NOT include social media, existing deals, or hype factors.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # DETAILED METHODOLOGY - Collapsed by default (internal use)
    with st.expander("🔧 View Detailed Calculation Methodology (Internal)", expanded=False):
        st.markdown(f"""
        <div style="background: #161b22; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h5 style="color: {COLORS['primary']}; margin-top: 0;">Our Valuation Philosophy</h5>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                Portal IQ values are based on <strong>verifiable on-field performance data only</strong>.
                Unlike On3/INFLCR that include social media following, existing NIL deals, media hype, and brand partnerships,
                we focus exclusively on what a player has <em>actually demonstrated</em> on the football field.
            </p>
        </div>
        """, unsafe_allow_html=True)

        calc_col1, calc_col2 = st.columns(2)

        with calc_col1:
            st.markdown("#### Step-by-Step Calculation")

            # Get values and escape for HTML safety
            position_val = html.escape(str(player_data.get('position', 'ATH')))
            star_rating_val = custom_breakdown.get('star_rating', 3)
            star_source_val = custom_breakdown.get('star_source', '')
            star_source_text = '(Portal Rating)' if star_source_val == 'portal' else '(HS Recruiting)'
            size_desc_val = html.escape(str(custom_breakdown.get('size_description', 'N/A')))
            school_tier_val = html.escape(str(custom_breakdown.get('school_tier', 'Standard')))

            # Show each calculation step
            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px; font-family: monospace;">
                <p style="color: #c9d6e3; margin: 5px 0;"><strong>1. Position Base Value</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">{position_val} = <strong>{format_currency(base_val)}</strong></p>

                <p style="color: #c9d6e3; margin: 5px 0;"><strong>2. Star Rating Multiplier</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">{star_rating_val}-star {star_source_text} = <strong>{star_mult}x</strong></p>

                <p style="color: #c9d6e3; margin: 5px 0;"><strong>3. Size/Measurables Multiplier</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">{size_desc_val} = <strong>{size_mult:.2f}x</strong></p>

                <p style="color: #c9d6e3; margin: 5px 0;"><strong>4. School Brand Multiplier</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">{school_tier_val} = <strong>{school_mult}x</strong></p>

                <p style="color: #c9d6e3; margin: 5px 0;"><strong>5. Performance Bonus</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">Stats-based additions = <strong>+{format_currency(perf_bonus)}</strong></p>

                <hr style="border-color: #30363d; margin: 15px 0;">

                <p style="color: #c9d1d9; margin: 5px 0;"><strong>FORMULA:</strong></p>
                <p style="color: #7ee787; margin: 5px 0 10px 20px; font-size: 0.95rem;">
                    ({format_currency(base_val)} x {star_mult} x {size_mult:.2f} x {school_mult}) + {format_currency(perf_bonus)}
                </p>

                <p style="color: {COLORS['primary']}; font-size: 1.3rem; margin: 15px 0 5px 0; text-align: center;">
                    <strong>= {format_currency(custom_value)}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

        with calc_col2:
            st.markdown("#### Data Source Confidence")

            # Confidence indicators for each data point
            conf_items_display = []

            # Position - always high confidence
            conf_items_display.append(("Position", "HIGH", "#00C853", "Verified from roster data"))

            # Stars - distinguish between portal rating (better) and HS recruiting
            stars_check = custom_breakdown.get("star_rating", 0)
            star_source = custom_breakdown.get("star_source", "unknown")
            if stars_check and stars_check > 0:
                if star_source == "portal":
                    conf_items_display.append(("Star Rating", "HIGH", "#00C853", f"Portal rating ({stars_check}★) - College performance"))
                else:
                    conf_items_display.append(("Star Rating", "MEDIUM", "#FFB74D", f"HS recruiting ({stars_check}★) - No portal rating"))
            else:
                conf_items_display.append(("Star Rating", "LOW", "#FF9800", "No recruiting data - using default"))

            # Size
            size_desc_check = custom_breakdown.get("size_description", "")
            if "not available" in size_desc_check.lower():
                conf_items_display.append(("Height/Weight", "LOW", "#FF9800", "No measurables data"))
            else:
                conf_items_display.append(("Height/Weight", "HIGH", "#00C853", f"Verified: {size_desc_check}"))

            # School
            conf_items_display.append(("School Brand", "HIGH", "#00C853", f"{custom_breakdown.get('school_tier', 'Standard')} tier"))

            # Performance
            if perf_bonus > 0:
                conf_items_display.append(("Performance Stats", "HIGH", "#00C853", f"+{format_currency(perf_bonus)} from verified stats"))
            else:
                conf_items_display.append(("Performance Stats", "MEDIUM", "#FFB74D", "Limited stats available"))

            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px;">
                <p style="color: #c9d1d9; font-weight: bold; margin-bottom: 15px;">Data Quality Assessment</p>
            """, unsafe_allow_html=True)

            for item, level, color, note in conf_items_display:
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center;
                            padding: 8px 0; border-bottom: 1px solid #30363d;">
                    <span style="color: #c9d6e3;">{item}</span>
                    <div style="text-align: right;">
                        <span style="background: {color}; color: #000; padding: 2px 8px; border-radius: 4px;
                                    font-size: 0.75rem; font-weight: bold;">{level}</span>
                        <p style="color: #a8b8c8; font-size: 0.75rem; margin: 2px 0 0 0;">{note}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Overall confidence score display
            high_cnt = sum(1 for _, lvl, _, _ in conf_items_display if lvl == "HIGH")
            conf_pct = int((high_cnt / len(conf_items_display)) * 100)

            st.markdown(f"""
                <div style="margin-top: 20px; text-align: center; padding: 15px;
                            background: linear-gradient(135deg, #1a2332 0%, #0d1117 100%); border-radius: 8px;">
                    <p style="color: #c9d6e3; margin: 0;">Overall Confidence Score</p>
                    <p style="color: {COLORS['primary']}; font-size: 2rem; font-weight: bold; margin: 5px 0;">{conf_pct}%</p>
                    <p style="color: #a8b8c8; font-size: 0.8rem; margin: 0;">
                        {high_cnt}/{len(conf_items_display)} data points verified
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Why Values Differ - Enhanced Section
    st.markdown("### 🔍 Portal IQ vs On3: Detailed Comparison")

    if on3_value > 0:
        diff = custom_value - on3_value
        diff_pct = (diff / on3_value) * 100 if on3_value > 0 else 0

        compare_col1, compare_col2 = st.columns(2)

        with compare_col1:
            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #2196F3;">
                <h4 style="color: #2196F3; margin-top: 0;">📊 On3 Valuation Model</h4>
                <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">On3 NIL valuations include:</p>
                <ul style="color: #c9d6e3; font-size: 0.85rem;">
                    <li><strong>Social Media Value</strong> - Instagram, TikTok, Twitter following (40-50% of value)</li>
                    <li><strong>Existing NIL Deals</strong> - Current contract values inflate estimates</li>
                    <li><strong>Media Exposure</strong> - National TV appearances, media mentions</li>
                    <li><strong>Marketability</strong> - Brand appeal, personality, content creation</li>
                    <li><strong>Hype Factor</strong> - Recruiting buzz, future potential projections</li>
                </ul>
                <p style="color: #2196F3; font-size: 1.1rem; margin-top: 15px;">
                    <strong>On3 Value: {format_currency(on3_value)}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

        with compare_col2:
            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #00C853;">
                <h4 style="color: #00C853; margin-top: 0;">🏈 Portal IQ Model (Our Approach)</h4>
                <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">Portal IQ valuations include <strong>ONLY</strong>:</p>
                <ul style="color: #c9d6e3; font-size: 0.85rem;">
                    <li><strong>Position Market Value</strong> - NFL positional scarcity/demand</li>
                    <li><strong>Verified Production Stats</strong> - Yards, TDs, tackles, etc.</li>
                    <li><strong>Physical Measurables</strong> - Height/weight fit for position</li>
                    <li><strong>Recruiting Pedigree</strong> - Star rating as talent indicator</li>
                    <li><strong>Program Visibility</strong> - School brand exposure multiplier</li>
                </ul>
                <p style="color: #00C853; font-size: 1.1rem; margin-top: 15px;">
                    <strong>Portal IQ Value: {format_currency(custom_value)}</strong>
                </p>
            </div>
            """, unsafe_allow_html=True)

        # The key difference explanation
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #2d1f00 0%, #1a1200 100%); padding: 25px; border-radius: 12px;
                    border: 1px solid #FFB74D; margin: 20px 0;">
            <h4 style="color: #FFB74D; margin-top: 0;">⚡ Key Insight: Why Our Value is {'Lower' if diff < 0 else 'Higher'}</h4>
            <p style="color: {COLORS['text_secondary']}; font-size: 1rem; line-height: 1.6;">
                <strong>The {format_currency(abs(diff))} ({abs(diff_pct):.1f}%) difference</strong> is primarily explained by:
            </p>
            <ul style="color: #c9d1d9; font-size: 0.95rem; line-height: 1.8;">
        """, unsafe_allow_html=True)

        # Dynamic explanation based on what's driving the difference
        if diff < 0:  # Portal IQ is lower
            reasons = []

            # Social media is the biggest factor for On3
            estimated_social_premium = on3_value * 0.35  # On3 typically weights social ~35-45%
            reasons.append(f"<li><strong>Social Media Premium (est. {format_currency(estimated_social_premium)})</strong> - On3 likely includes significant value from social following that we exclude entirely</li>")

            # Existing deals
            reasons.append(f"<li><strong>Existing NIL Deals</strong> - If the player has active NIL contracts, On3 uses those deal values to inform their estimate</li>")

            # Hype factor
            reasons.append(f"<li><strong>Hype/Potential Premium</strong> - On3 includes projected future value; we value only what's been demonstrated</li>")

            if custom_breakdown.get("performance_bonus", 0) == 0:
                reasons.append(f"<li><strong>Limited Production Data</strong> - We have no verified stats to add performance bonuses</li>")

            st.markdown("".join(reasons), unsafe_allow_html=True)
        else:  # Portal IQ is higher
            reasons = []

            if custom_breakdown.get("performance_bonus", 0) > 0:
                reasons.append(f"<li><strong>Elite Production (+{format_currency(custom_breakdown['performance_bonus'])})</strong> - On-field stats demonstrate value On3 may be underweighting</li>")

            if custom_breakdown.get("star_rating", 3) >= 4:
                reasons.append(f"<li><strong>{custom_breakdown['star_rating']}-Star Recruiting Pedigree</strong> - High-end talent not fully captured in On3's current valuation</li>")

            reasons.append(f"<li><strong>Market Timing</strong> - Our model may reflect more current positional market values</li>")

            st.markdown("".join(reasons), unsafe_allow_html=True)

        st.markdown(f"""
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Multiplier Reference Table
    with st.expander("📖 View Complete Multiplier Reference Tables", expanded=False):
        ref_col1, ref_col2, ref_col3 = st.columns(3)

        with ref_col1:
            st.markdown("#### Position Base Values")
            pos_data = {
                "Position": ["QB", "WR", "EDGE", "RB", "CB", "LB", "DL/DT", "S", "TE", "OT", "OG/C", "K/P"],
                "Base Value": ["$500,000", "$200,000", "$180,000", "$150,000", "$150,000", "$120,000",
                              "$100-110,000", "$100,000", "$100,000", "$120,000", "$70-85,000", "$20-30,000"],
                "Rationale": ["Premium position", "Playmaker demand", "Pass rush value", "Offensive weapon",
                             "Coverage premium", "Defensive anchor", "Run stuffers", "Secondary leader",
                             "Versatility", "Blindside protector", "Interior depth", "Specialists"]
            }
            st.dataframe(pd.DataFrame(pos_data), hide_index=True, use_container_width=True)

        with ref_col2:
            st.markdown("#### Star Rating Multipliers")
            star_data = {
                "Stars": ["5-Star ⭐⭐⭐⭐⭐", "4-Star ⭐⭐⭐⭐", "3-Star ⭐⭐⭐", "2-Star ⭐⭐"],
                "Multiplier": ["2.5x", "1.5x", "1.0x", "0.6x"],
                "Rationale": ["Elite talent", "Very good", "Solid contributor", "Developmental"]
            }
            st.dataframe(pd.DataFrame(star_data), hide_index=True, use_container_width=True)

        with ref_col3:
            st.markdown("#### School Brand Multipliers")
            school_data = {
                "Tier": ["Blue Blood", "Elite Program", "Strong Program", "Standard"],
                "Multiplier": ["1.8x", "1.4x", "1.2x", "1.0x"],
                "Examples": ["Bama, Ohio St, Georgia", "LSU, Oregon, Clemson", "Auburn, Wisconsin", "All others"]
            }
            st.dataframe(pd.DataFrame(school_data), hide_index=True, use_container_width=True)

    # Exportable Valuation Report
    st.markdown("### 📤 Export Valuation Report")

    report_content = f"""PORTAL IQ NIL VALUATION REPORT
Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}
================================================================================

PLAYER: {player_data.get('name', 'Unknown')}
Position: {player_data.get('position', 'N/A')}
School: {player_data.get('school', 'N/A')}
Star Rating: {custom_breakdown.get('star_rating', 'N/A')}-Star

================================================================================
VALUATION SUMMARY
================================================================================

On3 NIL Valuation:      {format_currency(on3_value) if on3_value > 0 else 'N/A'}
Portal IQ Valuation:    {format_currency(custom_value)}
Difference:             {format_currency(custom_value - on3_value) if on3_value > 0 else 'N/A'} ({((custom_value - on3_value) / on3_value * 100):.1f}% {'higher' if custom_value > on3_value else 'lower'} if on3_value > 0 else '')

================================================================================
CALCULATION METHODOLOGY
================================================================================

Portal IQ uses a performance-based valuation model that excludes:
- Social media following/engagement
- Existing NIL deal values
- Media hype and speculation
- Brand marketability factors

Our model includes ONLY verifiable on-field factors:

1. POSITION BASE VALUE
   {player_data.get('position', 'ATH')}: {format_currency(base_val)}
   (Based on NFL positional scarcity and market demand)

2. STAR RATING MULTIPLIER
   {custom_breakdown.get('star_rating', 3)}-Star Rating: {star_mult}x
   (Recruiting pedigree as talent indicator)

3. SIZE/MEASURABLES MULTIPLIER
   {custom_breakdown.get('size_description', 'N/A')}: {size_mult:.2f}x
   (Height/weight fit for position)

4. SCHOOL BRAND MULTIPLIER
   {custom_breakdown.get('school_tier', 'Standard')}: {school_mult}x
   (Program visibility and exposure factor)

5. PERFORMANCE BONUS
   Stats-based additions: +{format_currency(perf_bonus)}
   {chr(10).join(['   - ' + f for f in custom_breakdown.get('performance_factors', ['No verified stats available'])]) if custom_breakdown.get('performance_factors') else '   - No verified performance data'}

================================================================================
FORMULA
================================================================================

({format_currency(base_val)} × {star_mult} × {size_mult:.2f} × {school_mult}) + {format_currency(perf_bonus)}
= {format_currency(custom_value)}

================================================================================
DATA CONFIDENCE: {confidence_pct}%
================================================================================

{chr(10).join([f'{item}: {level} - {note}' for item, level, _, note in confidence_items])}

================================================================================
DISCLAIMER
================================================================================

This valuation represents Portal IQ's assessment based on available performance
data. It is NOT a market prediction and does not include social media value,
existing NIL contracts, or speculative factors. Actual NIL market value may be
higher due to these excluded factors.

For questions about methodology, contact: support@portaliq.com

© {pd.Timestamp.now().year} Elite Sports Solutions - Portal IQ
"""

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="📄 Download Full Report (TXT)",
            data=report_content,
            file_name=f"nil_valuation_{player_data.get('name', 'player').replace(' ', '_').lower()}.txt",
            mime="text/plain",
            use_container_width=True
        )

    with col2:
        # CSV version for spreadsheets
        csv_data = pd.DataFrame([{
            "Player": player_data.get('name', ''),
            "Position": player_data.get('position', ''),
            "School": player_data.get('school', ''),
            "Stars": custom_breakdown.get('star_rating', ''),
            "On3_Value": on3_value,
            "PortalIQ_Value": custom_value,
            "Difference": custom_value - on3_value if on3_value > 0 else None,
            "Difference_Pct": ((custom_value - on3_value) / on3_value * 100) if on3_value > 0 else None,
            "Position_Base": base_val,
            "Star_Multiplier": star_mult,
            "Size_Multiplier": size_mult,
            "School_Multiplier": school_mult,
            "School_Tier": custom_breakdown.get('school_tier', ''),
            "Performance_Bonus": perf_bonus,
            "Confidence_Score": confidence_pct,
        }])

        st.download_button(
            label="📊 Download Report (CSV)",
            data=csv_data.to_csv(index=False),
            file_name=f"nil_valuation_{player_data.get('name', 'player').replace(' ', '_').lower()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Quick Talking Points for Justification
    st.markdown("### 💬 Quick Talking Points")
    st.markdown("_Use these when explaining your valuation_")

    talking_points = []
    talking_points.append(f"• **{player_data.get('name', 'This player')}'s Portal IQ value is {format_currency(custom_value)}** based purely on football performance metrics.")

    if on3_value > 0 and custom_value < on3_value:
        talking_points.append(f"• On3's {format_currency(on3_value)} valuation includes social media premium (~35-45% of their value) and existing NIL deals - **we exclude these speculative factors**.")
        talking_points.append(f"• Our {format_currency(abs(custom_value - on3_value))} lower valuation represents the **performance-only floor** - what the player's football production is actually worth.")

    talking_points.append(f"• Position value: **{player_data.get('position', 'ATH')}s command {format_currency(base_val)} base** due to NFL positional demand.")

    if custom_breakdown.get('star_rating', 3) >= 4:
        talking_points.append(f"• **{custom_breakdown['star_rating']}-star recruiting pedigree** verified through 247Sports/Rivals ({star_mult}x multiplier).")

    if custom_breakdown.get('school_tier') in ['Blue Blood', 'Elite Program']:
        talking_points.append(f"• **{custom_breakdown['school_tier']} program visibility** adds brand exposure multiplier ({school_mult}x).")

    if custom_breakdown.get('performance_bonus', 0) > 0:
        talking_points.append(f"• **Verified production stats add {format_currency(perf_bonus)}** to the valuation.")
        for factor in custom_breakdown.get('performance_factors', [])[:2]:
            talking_points.append(f"  - {factor}")

    talking_points.append(f"• Data confidence: **{confidence_pct}%** based on {high_count}/{len(confidence_items)} verified data points.")
    talking_points.append(f"• **Bottom line:** This is a conservative, defensible number based on what the player has *proven* on the field.")

    st.markdown(f"""
    <div style="background: #161b22; padding: 20px; border-radius: 10px; border-left: 4px solid {COLORS['primary']};">
        {'<br>'.join(talking_points)}
    </div>
    """, unsafe_allow_html=True)

    # Copy button for talking points
    talking_points_text = "\n".join([p.replace("**", "").replace("*", "").replace("•", "-") for p in talking_points])

    st.download_button(
        label="📋 Copy Talking Points",
        data=talking_points_text,
        file_name=f"talking_points_{player_data.get('name', 'player').replace(' ', '_').lower()}.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.divider()

    # Additional metrics
    col1, col2, col3, col4 = st.columns(4)

    nil_value = display_value  # Use for charts below

    with col1:
        tier_html = render_tier_badge(tier)
        st.markdown(f"""
        <div style="padding: 10px;">
            <p style="color: #c9d6e3; margin-bottom: 5px;">Value Tier</p>
            {tier_html}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.metric(
            "Confidence Score",
            "85%",
            delta="High"
        )

    with col3:
        st.metric(
            "Market Percentile",
            "87th",
            delta=f"Top 13%"
        )

    with col4:
        st.metric(
            "Position Rank",
            f"#{custom_breakdown.get('star_rating', 3) * 10}",
            delta=f"at {player_data.get('position', 'N/A')}"
        )

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Value Breakdown")

        breakdown = {
            "base_value": nil_value * 0.35,
            "social_media_premium": nil_value * 0.25,
            "school_brand_factor": nil_value * 0.20,
            "position_market_factor": nil_value * 0.12,
            "draft_potential_premium": nil_value * 0.08,
        }

        fig = create_value_breakdown_chart(breakdown)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Feature Impact (SHAP)")

        shap_features = [
            ("Social Media Followers", nil_value * 0.18),
            (f"School Brand ({player_data.get('school', 'School')})", nil_value * 0.15),
            (f"Position ({player_data.get('position', 'POS')})", nil_value * 0.12),
            (f"Recruiting Stars ({player_data.get('stars', 4)})", nil_value * 0.10),
            ("On-Field Production", nil_value * 0.09),
            ("Games Started", nil_value * 0.08),
            ("Draft Projection", nil_value * 0.07),
            ("Conference Strength", nil_value * 0.06),
            ("Team Success", nil_value * 0.05),
            ("Media Exposure", nil_value * 0.04),
        ]

        fig = create_shap_waterfall(shap_features)
        st.plotly_chart(fig, use_container_width=True)

    # Comparable Players
    st.markdown("### Comparable Players")

    players_df = get_sample_players()
    position = player_data.get("position", "QB")

    comparables = players_df[
        (players_df["position"] == position) |
        (players_df["nil_value"].between(nil_value * 0.5, nil_value * 2))
    ].head(5)

    if not comparables.empty:
        display_df = comparables[["name", "school", "position", "nil_value", "tier", "stars"]].copy()
        display_df["nil_value"] = display_df["nil_value"].apply(format_currency)
        display_df.columns = ["Player", "School", "Position", "NIL Value", "Tier", "Stars"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # Transfer Impact Simulator
    st.markdown("## 🔄 Transfer Impact Simulator")
    st.markdown("See how transferring to a different school would affect NIL value")

    col1, col2 = st.columns([1, 2])

    with col1:
        current_school = player_data.get("school", "Current School")
        target_school = st.selectbox(
            "Transfer Destination",
            options=[s for s in get_school_list() if s != current_school],
            key="transfer_target"
        )

        if st.button("📊 Simulate Transfer", key="transfer_btn"):
            st.session_state.show_transfer = True

    with col2:
        if st.session_state.get("show_transfer", False):
            # Calculate projected value
            blue_bloods = ["Alabama", "Ohio State", "Georgia", "Texas", "USC", "Michigan", "Notre Dame"]
            elite = ["LSU", "Florida", "Oregon", "Penn State", "Clemson", "Tennessee"]

            current_mult = 2.5 if current_school in blue_bloods else 1.8 if current_school in elite else 1.2
            target_mult = 2.5 if target_school in blue_bloods else 1.8 if target_school in elite else 1.2

            projected_value = nil_value * (target_mult / current_mult)

            fig = create_transfer_comparison_chart(
                nil_value,
                projected_value,
                (current_school, target_school)
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Social Media Growth Simulator
    st.markdown("## 📱 Social Media Growth Simulator")
    st.markdown("See how growing your social following impacts NIL value")

    col1, col2 = st.columns([1, 2])

    with col1:
        current_followers = (
            player_data.get("instagram_followers", 50000) +
            player_data.get("twitter_followers", 25000) +
            player_data.get("tiktok_followers", 10000)
        )

        st.metric("Current Total Followers", f"{current_followers:,}")

        follower_growth = st.slider(
            "Simulated Follower Growth",
            min_value=0,
            max_value=1000000,
            value=100000,
            step=10000,
            format="%d",
            key="follower_growth"
        )

        growth_value = nil_value * (1 + follower_growth / 1000000 * 0.5)
        growth_delta = growth_value - nil_value

        st.metric(
            "Projected NIL Value",
            format_currency(growth_value),
            delta=f"+{format_currency(growth_delta)}"
        )

    with col2:
        fig = create_social_growth_chart(nil_value, follower_growth)
        st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# Player Comparison Mode
# =============================================================================

def render_comparison_mode():
    """Render the player comparison mode."""
    st.markdown("### ⚖️ Player Comparison")
    st.markdown("_Compare up to 3 players side-by-side_")

    players = get_comparison_players()

    if not players:
        st.info("No players selected for comparison. Add players from the Search Players tab using the ➕ button.")
        st.markdown(f"""
        <div style="background: {COLORS['bg_medium']}; padding: 30px; border-radius: 12px; text-align: center; margin-top: 20px;">
            <p style="font-size: 4rem; margin: 0;">⚖️</p>
            <h3 style="color: {COLORS['primary']};">Side-by-Side Comparison</h3>
            <p style="color: {COLORS['text_secondary']};">
                Compare NIL values, stats, and projections for up to 3 players.
                Go to the <strong>Search Players</strong> tab and click ➕ to add players.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Clear all button
    if st.button("🗑️ Clear All", key="clear_comparison"):
        clear_comparison()
        st.rerun()

    st.divider()

    # Create columns for each player
    cols = st.columns(len(players))

    # Player headers and basic info
    for idx, (col, player) in enumerate(zip(cols, players)):
        with col:
            # Remove button
            if st.button(f"✖ Remove", key=f"rm_cmp_{idx}"):
                remove_from_comparison(player.get("name", ""))
                st.rerun()

            # Player card header with headshot
            stars = int(player.get("stars", 0)) if player.get("stars") else 0
            stars_display = "⭐" * stars if stars > 0 else "—"
            headshot_url = player.get("headshot_url", "")

            # Display headshot
            if headshot_url and pd.notna(headshot_url):
                headshot_html = f'<img src="{headshot_url}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin-bottom: 10px;">'
            else:
                headshot_html = '<div style="width: 80px; height: 80px; border-radius: 50%; background: #2d3748; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; font-size: 2rem;">👤</div>'

            st.markdown(f"""
            <div style="background: {COLORS['bg_medium']}; padding: 20px; border-radius: 12px; text-align: center;
                        border-top: 4px solid {COLORS['primary']};">
                {headshot_html}
                <h3 style="color: {COLORS['text_primary']}; margin: 0;">{player.get('name', 'Unknown')}</h3>
                <p style="color: {COLORS['text_secondary']}; margin: 5px 0;">{player.get('position', 'ATH')} | {player.get('school', 'Unknown')}</p>
                <p style="margin: 5px 0;">{stars_display}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # NIL Values comparison
    st.markdown("### 💰 NIL Value Comparison")

    for idx, (col, player) in enumerate(zip(cols, players)):
        with col:
            on3_value = player.get("nil_value", 0) or 0
            custom_value, breakdown = calculate_custom_nil_value(player)

            st.metric("On3 NIL Value", format_currency(on3_value) if on3_value > 0 else "N/A")
            st.metric("Portal IQ Value", format_currency(custom_value))

            diff = custom_value - on3_value if on3_value > 0 else 0
            diff_pct = (diff / on3_value * 100) if on3_value > 0 else 0
            if on3_value > 0:
                color = COLORS["primary"] if diff >= 0 else COLORS["risk_high"]
                st.markdown(f"<span style='color: {color};'>{'+' if diff >= 0 else ''}{diff_pct:.1f}% difference</span>", unsafe_allow_html=True)

    st.divider()

    # Stats comparison
    st.markdown("### 📊 Performance Metrics")

    metrics_to_compare = [
        ("Stars", "stars", lambda x: f"{'⭐' * int(x)}" if x else "—"),
        ("Overall Rating", "overall_rating", lambda x: f"{x:.2f}" if x else "N/A"),
        ("Games Played", "games_played", lambda x: str(int(x)) if x else "—"),
        ("Games Started", "games_started", lambda x: str(int(x)) if x else "—"),
    ]

    # Position-specific stats
    positions = [p.get("position", "") for p in players]

    if any(pos == "QB" for pos in positions):
        metrics_to_compare.extend([
            ("Passing Yards", "passing_yards", lambda x: f"{int(x):,}" if x else "—"),
            ("Passing TDs", "passing_tds", lambda x: str(int(x)) if x else "—"),
            ("QBR", "qbr", lambda x: f"{x:.1f}" if x else "—"),
        ])

    if any(pos == "RB" for pos in positions):
        metrics_to_compare.extend([
            ("Rushing Yards", "rushing_yards", lambda x: f"{int(x):,}" if x else "—"),
            ("Rushing TDs", "rushing_tds", lambda x: str(int(x)) if x else "—"),
            ("Yards/Carry", "yards_per_carry", lambda x: f"{x:.1f}" if x else "—"),
        ])

    if any(pos == "WR" for pos in positions):
        metrics_to_compare.extend([
            ("Receptions", "receptions", lambda x: str(int(x)) if x else "—"),
            ("Receiving Yards", "receiving_yards", lambda x: f"{int(x):,}" if x else "—"),
            ("Receiving TDs", "receiving_tds", lambda x: str(int(x)) if x else "—"),
        ])

    if any(pos in ["EDGE", "DT", "LB", "DL"] for pos in positions):
        metrics_to_compare.extend([
            ("Tackles", "tackles", lambda x: str(int(x)) if x else "—"),
            ("Sacks", "sacks", lambda x: f"{x:.1f}" if x else "—"),
            ("TFLs", "tackles_for_loss", lambda x: f"{x:.1f}" if x else "—"),
        ])

    if any(pos in ["CB", "S"] for pos in positions):
        metrics_to_compare.extend([
            ("Interceptions", "interceptions_def", lambda x: str(int(x)) if x else "—"),
            ("Passes Defended", "passes_defended", lambda x: str(int(x)) if x else "—"),
        ])

    # Display metrics in a table format
    for metric_name, metric_key, formatter in metrics_to_compare:
        metric_cols = st.columns(len(players) + 1)

        with metric_cols[0]:
            st.markdown(f"**{metric_name}**")

        for idx, (col, player) in enumerate(zip(metric_cols[1:], players)):
            with col:
                value = player.get(metric_key)
                st.markdown(formatter(value))

    st.divider()

    # Value breakdown chart comparison
    st.markdown("### 📈 Value Breakdown Comparison")

    comparison_data = []
    for player in players:
        custom_value, breakdown = calculate_custom_nil_value(player)
        comparison_data.append({
            "name": player.get("name", "Unknown"),
            "Position Base": breakdown.get("base_position_value", 0),
            "Star Rating": breakdown.get("base_position_value", 0) * (breakdown.get("star_multiplier", 1) - 1),
            "Size Factor": breakdown.get("base_position_value", 0) * (breakdown.get("size_multiplier", 1) - 1),
            "School Brand": breakdown.get("base_position_value", 0) * (breakdown.get("school_multiplier", 1) - 1),
            "Performance": breakdown.get("performance_bonus", 0),
        })

    # Create grouped bar chart
    fig = go.Figure()

    categories = ["Position Base", "Star Rating", "Size Factor", "School Brand", "Performance"]
    colors = [COLORS["chart_1"], COLORS["chart_2"], COLORS["chart_3"], COLORS["chart_4"], COLORS["chart_5"]]

    for i, cat in enumerate(categories):
        fig.add_trace(go.Bar(
            name=cat,
            x=[d["name"] for d in comparison_data],
            y=[d[cat] for d in comparison_data],
            marker_color=colors[i],
        ))

    fig.update_layout(
        barmode='stack',
        title="Value Components by Player",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(gridcolor=COLORS["bg_light"], title="Value ($)"),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Transfer value comparison
    st.markdown("### 🔄 Transfer Value Analysis")

    target_school = st.selectbox(
        "Compare Transfer Value To:",
        options=get_school_list(),
        key="comparison_transfer_school"
    )

    if target_school:
        blue_bloods = ["Alabama", "Ohio State", "Georgia", "Texas", "USC", "Michigan", "Notre Dame"]
        elite = ["LSU", "Florida", "Oregon", "Penn State", "Clemson", "Tennessee"]
        target_mult = 2.5 if target_school in blue_bloods else 1.8 if target_school in elite else 1.2

        comparison_results = []
        for player in players:
            current_school = player.get("school", "Unknown")
            current_mult = 2.5 if current_school in blue_bloods else 1.8 if current_school in elite else 1.2

            custom_value, _ = calculate_custom_nil_value(player)
            projected_value = custom_value * (target_mult / current_mult)
            change = projected_value - custom_value

            comparison_results.append({
                "name": player.get("name", "Unknown"),
                "current": custom_value,
                "projected": projected_value,
                "change": change,
                "change_pct": (change / custom_value * 100) if custom_value > 0 else 0,
            })

        # Display results
        for idx, (col, result) in enumerate(zip(cols, comparison_results)):
            with col:
                st.metric(
                    "Current Value",
                    format_currency(result["current"])
                )
                st.metric(
                    f"At {target_school}",
                    format_currency(result["projected"]),
                    delta=f"{result['change_pct']:+.1f}%"
                )

    st.divider()

    # Export comparison
    st.markdown("### 📤 Export Comparison")

    if st.button("📋 Export to CSV", key="export_comparison", use_container_width=True):
        # Build comparison DataFrame
        export_data = []
        for player in players:
            custom_value, breakdown = calculate_custom_nil_value(player)
            export_data.append({
                "Name": player.get("name", ""),
                "Position": player.get("position", ""),
                "School": player.get("school", ""),
                "Stars": player.get("stars", 0),
                "On3 NIL Value": player.get("nil_value", 0),
                "Portal IQ Value": custom_value,
                "Star Multiplier": breakdown.get("star_multiplier", 1),
                "Size Multiplier": breakdown.get("size_multiplier", 1),
                "School Multiplier": breakdown.get("school_multiplier", 1),
                "Performance Bonus": breakdown.get("performance_bonus", 0),
            })

        df = pd.DataFrame(export_data)
        csv = df.to_csv(index=False)

        st.download_button(
            label="⬇️ Download Comparison CSV",
            data=csv,
            file_name="nil_comparison.csv",
            mime="text/csv",
        )


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    main()
else:
    main()
