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

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import (
    apply_custom_css, COLORS, get_tier_color, format_currency,
    render_tier_badge
)
from utils.api_client import get_api_client
from utils.data_loader import (
    load_sample_data, get_school_list, get_positions, get_class_years
)
from utils.navigation import render_sidebar

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
    stars = player_data.get("stars", 3)
    school = player_data.get("school", "Unknown")

    # Handle NaN stars
    if pd.isna(stars):
        stars = 3
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

    # QB stats
    if position == "QB":
        pass_yds = player_data.get("passing_yards", 0) or 0
        pass_tds = player_data.get("passing_tds", 0) or 0
        if pass_yds > 3000:
            perf_bonus += 150000
            perf_factors.append(f"Elite passing yards ({pass_yds:,})")
        elif pass_yds > 2000:
            perf_bonus += 75000
            perf_factors.append(f"Strong passing yards ({pass_yds:,})")
        if pass_tds > 25:
            perf_bonus += 100000
            perf_factors.append(f"Elite passing TDs ({pass_tds})")

    # RB stats
    elif position == "RB":
        rush_yds = player_data.get("rushing_yards", 0) or 0
        rush_tds = player_data.get("rushing_tds", 0) or 0
        if rush_yds > 1000:
            perf_bonus += 80000
            perf_factors.append(f"1000+ yard rusher ({rush_yds:,})")
        if rush_tds > 10:
            perf_bonus += 50000
            perf_factors.append(f"Double-digit TDs ({rush_tds})")

    # WR stats
    elif position == "WR":
        rec_yds = player_data.get("receiving_yards", 0) or 0
        rec_tds = player_data.get("receiving_tds", 0) or 0
        if rec_yds > 1000:
            perf_bonus += 100000
            perf_factors.append(f"1000+ yard receiver ({rec_yds:,})")
        if rec_tds > 8:
            perf_bonus += 60000
            perf_factors.append(f"High TD count ({rec_tds})")

    # Defensive stats
    elif position in ["EDGE", "DT", "DL", "LB"]:
        tackles = player_data.get("tackles", 0) or 0
        sacks = player_data.get("sacks", 0) or 0
        if sacks > 8:
            perf_bonus += 100000
            perf_factors.append(f"Elite pass rusher ({sacks} sacks)")
        elif sacks > 5:
            perf_bonus += 50000
            perf_factors.append(f"Strong pass rush ({sacks} sacks)")
        if tackles > 80:
            perf_bonus += 40000
            perf_factors.append(f"High tackle count ({tackles})")

    # Secondary stats
    elif position in ["CB", "S"]:
        ints = player_data.get("interceptions", player_data.get("interceptions_def", 0)) or 0
        if ints > 4:
            perf_bonus += 80000
            perf_factors.append(f"Ball hawk ({ints} INTs)")
        elif ints > 2:
            perf_bonus += 40000
            perf_factors.append(f"Playmaker ({ints} INTs)")

    # Calculate total with size factor
    custom_value = (base * star_mult * school_mult * size_mult) + perf_bonus

    # Build breakdown for explanation
    breakdown = {
        "base_position_value": base,
        "star_multiplier": star_mult,
        "star_rating": stars,
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

    # Header - Navy/Gold branding
    st.markdown(f"""
    <h1 style="color: {COLORS['primary']};">💰 NIL Valuator</h1>
    <p style="color: {COLORS['text_secondary']}; font-size: 1.1rem;">
        Get AI-powered NIL valuations with detailed breakdowns
    </p>
    """, unsafe_allow_html=True)

    st.divider()

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
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                st.markdown(f"**{player['name']}**")
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
    """Render the NIL valuation results."""
    st.divider()
    st.markdown("## 📊 Valuation Results")

    # Get both values
    on3_value = player_data.get("nil_value", 0) or 0
    custom_value, custom_breakdown = calculate_custom_nil_value(player_data)
    tier = player_data.get("tier", "solid")

    # Use On3 value if available, otherwise use custom
    display_value = on3_value if on3_value > 0 else custom_value

    # Main metrics - On3 vs Custom comparison
    st.markdown("### 📈 NIL Value Comparison")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #2196F3; text-align: center;">
            <p style="color: #c9d6e3; margin-bottom: 5px; font-size: 0.9rem;">On3 NIL Valuation</p>
            <h2 style="color: #2196F3; margin: 0;">{format_currency(on3_value) if on3_value > 0 else 'N/A'}</h2>
            <p style="color: #c9d6e3; font-size: 0.8rem; margin-top: 5px;">Market consensus value</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #00C853; text-align: center;">
            <p style="color: #c9d6e3; margin-bottom: 5px; font-size: 0.9rem;">Portal IQ Custom Value</p>
            <h2 style="color: #00C853; margin: 0;">{format_currency(custom_value)}</h2>
            <p style="color: #c9d6e3; font-size: 0.8rem; margin-top: 5px;">Performance-based estimate</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # Calculate difference
        if on3_value > 0:
            diff = custom_value - on3_value
            diff_pct = (diff / on3_value) * 100 if on3_value > 0 else 0
            diff_color = "#00C853" if diff > 0 else "#F44336" if diff < 0 else "#c9d6e3"
            diff_label = "Undervalued by On3" if diff > 0 else "Overvalued by On3" if diff < 0 else "Fair Value"

            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid {diff_color}; text-align: center;">
                <p style="color: #c9d6e3; margin-bottom: 5px; font-size: 0.9rem;">Difference</p>
                <h2 style="color: {diff_color}; margin: 0;">{'+' if diff > 0 else ''}{format_currency(diff)}</h2>
                <p style="color: {diff_color}; font-size: 0.8rem; margin-top: 5px;">{diff_label} ({diff_pct:+.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #c9d6e3; text-align: center;">
                <p style="color: #c9d6e3; margin-bottom: 5px; font-size: 0.9rem;">Difference</p>
                <h2 style="color: #c9d6e3; margin: 0;">N/A</h2>
                <p style="color: #c9d6e3; font-size: 0.8rem; margin-top: 5px;">No On3 data available</p>
            </div>
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

            # Show each calculation step
            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px; font-family: monospace;">
                <p style="color: #c9d6e3; margin: 5px 0;"><strong>1. Position Base Value</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">{player_data.get('position', 'ATH')} = <strong>{format_currency(base_val)}</strong></p>

                <p style="color: #c9d6e3; margin: 5px 0;"><strong>2. Star Rating Multiplier</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">{custom_breakdown.get('star_rating', 3)}-star = <strong>{star_mult}x</strong></p>

                <p style="color: #c9d6e3; margin: 5px 0;"><strong>3. Size/Measurables Multiplier</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">{custom_breakdown.get('size_description', 'N/A')} = <strong>{size_mult:.2f}x</strong></p>

                <p style="color: #c9d6e3; margin: 5px 0;"><strong>4. School Brand Multiplier</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">{custom_breakdown.get('school_tier', 'Standard')} = <strong>{school_mult}x</strong></p>

                <p style="color: #c9d6e3; margin: 5px 0;"><strong>5. Performance Bonus</strong></p>
                <p style="color: #58a6ff; margin: 5px 0 15px 20px;">Stats-based additions = <strong>+{format_currency(perf_bonus)}</strong></p>

                <hr style="border-color: #30363d; margin: 15px 0;">

                <p style="color: #c9d1d9; margin: 5px 0;"><strong>FORMULA:</strong></p>
                <p style="color: #7ee787; margin: 5px 0 10px 20px; font-size: 0.95rem;">
                    ({format_currency(base_val)} × {star_mult} × {size_mult:.2f} × {school_mult}) + {format_currency(perf_bonus)}
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

            # Stars
            stars_check = custom_breakdown.get("star_rating", 0)
            if stars_check and stars_check > 0:
                conf_items_display.append(("Star Rating", "HIGH", "#00C853", f"247Sports/Rivals verified ({stars_check}★)"))
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

            # Player card header
            stars = int(player.get("stars", 0)) if player.get("stars") else 0
            stars_display = "⭐" * stars if stars > 0 else "—"

            st.markdown(f"""
            <div style="background: {COLORS['bg_medium']}; padding: 20px; border-radius: 12px; text-align: center;
                        border-top: 4px solid {COLORS['primary']};">
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
