"""
NIL Valuator Page

AI-powered NIL valuation for college football players.
- Search existing players or create custom profiles
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

    # Header
    st.markdown("""
    <h1 style="color: #00C853;">💰 NIL Valuator</h1>
    <p style="color: #e6edf3; font-size: 1.1rem;">
        Get AI-powered NIL valuations with detailed breakdowns
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    # Mode selection
    mode = st.radio(
        "Select Mode",
        ["Search Existing Player", "Custom Player Profile"],
        horizontal=True,
    )

    st.divider()

    if mode == "Search Existing Player":
        render_search_mode()
    else:
        render_custom_mode()


def render_search_mode():
    """Render search existing player mode."""
    players_df = get_sample_players()

    # Text search input
    search_query = st.text_input(
        "Search Player",
        placeholder="Type player name (e.g., Arch Manning, Jeremiah Smith...)",
        help="Start typing to search players"
    )

    # Filter players based on search
    if search_query:
        filtered_df = players_df[
            players_df["name"].str.lower().str.contains(search_query.lower(), na=False)
        ]
    else:
        filtered_df = players_df.head(10)  # Show top 10 by default

    # Show matching players
    if not filtered_df.empty:
        st.markdown(f"**{len(filtered_df)} players found**" if search_query else "**Top 10 Players**")

        # Display as clickable cards
        for idx, (_, player) in enumerate(filtered_df.head(20).iterrows()):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
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
            <p style="color: #8b949e; margin-bottom: 5px; font-size: 0.9rem;">On3 NIL Valuation</p>
            <h2 style="color: #2196F3; margin: 0;">{format_currency(on3_value) if on3_value > 0 else 'N/A'}</h2>
            <p style="color: #8b949e; font-size: 0.8rem; margin-top: 5px;">Market consensus value</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #00C853; text-align: center;">
            <p style="color: #8b949e; margin-bottom: 5px; font-size: 0.9rem;">Portal IQ Custom Value</p>
            <h2 style="color: #00C853; margin: 0;">{format_currency(custom_value)}</h2>
            <p style="color: #8b949e; font-size: 0.8rem; margin-top: 5px;">Performance-based estimate</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        # Calculate difference
        if on3_value > 0:
            diff = custom_value - on3_value
            diff_pct = (diff / on3_value) * 100 if on3_value > 0 else 0
            diff_color = "#00C853" if diff > 0 else "#F44336" if diff < 0 else "#8b949e"
            diff_label = "Undervalued by On3" if diff > 0 else "Overvalued by On3" if diff < 0 else "Fair Value"

            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid {diff_color}; text-align: center;">
                <p style="color: #8b949e; margin-bottom: 5px; font-size: 0.9rem;">Difference</p>
                <h2 style="color: {diff_color}; margin: 0;">{'+' if diff > 0 else ''}{format_currency(diff)}</h2>
                <p style="color: {diff_color}; font-size: 0.8rem; margin-top: 5px;">{diff_label} ({diff_pct:+.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background: #161b22; padding: 20px; border-radius: 10px; border: 2px solid #8b949e; text-align: center;">
                <p style="color: #8b949e; margin-bottom: 5px; font-size: 0.9rem;">Difference</p>
                <h2 style="color: #8b949e; margin: 0;">N/A</h2>
                <p style="color: #8b949e; font-size: 0.8rem; margin-top: 5px;">No On3 data available</p>
            </div>
            """, unsafe_allow_html=True)

    # Explanation of why values differ
    if on3_value > 0 and abs(custom_value - on3_value) > 10000:
        st.markdown("### 🔍 Why Do The Values Differ?")

        diff = custom_value - on3_value

        explanation_items = []

        # Custom is higher - explain what we see that On3 might miss
        if diff > 0:
            explanation_items.append("**Our custom model values this player higher because:**")

            if custom_breakdown.get("performance_bonus", 0) > 0:
                explanation_items.append(f"• **On-field production** adds {format_currency(custom_breakdown['performance_bonus'])} to our estimate")
                for factor in custom_breakdown.get("performance_factors", []):
                    explanation_items.append(f"  - {factor}")

            if custom_breakdown.get("star_rating", 3) >= 4:
                explanation_items.append(f"• **{custom_breakdown['star_rating']}-star rating** indicates elite potential ({custom_breakdown['star_multiplier']}x multiplier)")

            if custom_breakdown.get("size_multiplier", 1.0) >= 1.05:
                explanation_items.append(f"• **{custom_breakdown['size_description']}** - premium size for position ({custom_breakdown['size_multiplier']:.2f}x multiplier)")

            if custom_breakdown.get("school_tier") in ["Blue Blood", "Elite Program"]:
                explanation_items.append(f"• **{custom_breakdown['school_tier']} school** brand value ({custom_breakdown['school_multiplier']}x multiplier)")

            explanation_items.append("")
            explanation_items.append("*On3 may not fully capture this player's production metrics or is using older data.*")

        # Custom is lower - explain why On3 might be inflating
        else:
            explanation_items.append("**On3 values this player higher, possibly because:**")
            explanation_items.append("• **Social media following** - On3 heavily weights social presence")
            explanation_items.append("• **NIL deal history** - existing deals may inflate market value")
            explanation_items.append("• **Hype/Brand deals** - marketing appeal beyond on-field stats")

            if custom_breakdown.get("size_multiplier", 1.0) < 0.95:
                explanation_items.append(f"• **Size concerns** - {custom_breakdown.get('size_description', 'undersized')} affects our valuation ({custom_breakdown.get('size_multiplier', 1.0):.2f}x)")

            if custom_breakdown.get("performance_bonus", 0) == 0:
                explanation_items.append("")
                explanation_items.append("*Our model sees limited verified production stats, suggesting the market value may be driven by potential/hype rather than performance.*")

        st.markdown(f"""
        <div style="background: #161b22; padding: 20px; border-radius: 10px; border-left: 4px solid {'#00C853' if diff > 0 else '#FF9800'};">
            {'<br>'.join(explanation_items)}
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Additional metrics
    col1, col2, col3, col4 = st.columns(4)

    nil_value = display_value  # Use for charts below

    with col1:
        tier_html = render_tier_badge(tier)
        st.markdown(f"""
        <div style="padding: 10px;">
            <p style="color: #8b949e; margin-bottom: 5px;">Value Tier</p>
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
# Run
# =============================================================================

if __name__ == "__main__":
    main()
else:
    main()
