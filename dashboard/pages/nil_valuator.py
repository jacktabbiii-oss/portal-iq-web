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
    # Header
    st.markdown("""
    <h1 style="color: #00C853;">💰 NIL Valuator</h1>
    <p style="color: #aaa; font-size: 1.1rem;">
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

    col1, col2 = st.columns([2, 1])

    with col1:
        player_options = players_df["name"].tolist()
        selected_player = st.selectbox(
            "Search Player",
            options=player_options,
            help="Select a player from the database",
        )

    with col2:
        st.write("")  # Spacer
        search_btn = st.button("🔍 Get Valuation", type="primary", use_container_width=True)

    if selected_player and search_btn:
        player_data = players_df[players_df["name"] == selected_player].iloc[0].to_dict()
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

    # Main metrics
    col1, col2, col3, col4 = st.columns(4)

    nil_value = player_data.get("nil_value", 500000)
    tier = player_data.get("tier", "solid")

    with col1:
        st.metric(
            "Predicted NIL Value",
            format_currency(nil_value),
            delta="±15% confidence range"
        )

    with col2:
        tier_html = render_tier_badge(tier)
        st.markdown(f"""
        <div style="padding: 10px;">
            <p style="color: #888; margin-bottom: 5px;">Value Tier</p>
            {tier_html}
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.metric(
            "Confidence Score",
            "85%",
            delta="High"
        )

    with col4:
        st.metric(
            "Market Percentile",
            "87th",
            delta=f"Top 13%"
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
