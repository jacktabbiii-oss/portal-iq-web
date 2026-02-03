"""
Win Impact Page

Analyze player contribution to team wins and NIL correlation.
- Win Impact metrics by position
- NIL-to-Win correlation
- Transfer impact projections
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import (
    apply_custom_css, COLORS, format_currency, get_tier_color
)
from utils.data_loader import (
    get_nil_players, get_portal_players, get_team_rankings, get_school_list, get_positions
)

# Page config
st.set_page_config(
    page_title="Win Impact | Portal IQ",
    page_icon="📈",
    layout="wide",
)

apply_custom_css()


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_win_impact(player_data: dict) -> dict:
    """Calculate estimated win impact for a player based on position and metrics."""
    position = player_data.get("position", "ATH")
    nil_value = player_data.get("nil_value", 0)
    stars_raw = player_data.get("stars", 3)
    # Handle NaN values
    stars = int(stars_raw) if pd.notna(stars_raw) else 3

    # Base win impact by position (expected wins above replacement)
    position_war = {
        "QB": 2.5, "RB": 0.8, "WR": 0.6, "TE": 0.4,
        "OT": 0.7, "OG": 0.5, "C": 0.4, "IOL": 0.5,
        "EDGE": 1.2, "DT": 0.6, "DL": 0.7, "LB": 0.8,
        "CB": 0.9, "S": 0.7, "K": 0.3, "P": 0.2, "ATH": 0.5
    }

    base_war = position_war.get(position, 0.5)

    # Adjust by star rating
    star_mult = {5: 1.8, 4: 1.3, 3: 1.0, 2: 0.7}
    war = base_war * star_mult.get(stars, 1.0)

    # NIL correlation - higher NIL usually means higher impact
    nil_bonus = min(nil_value / 2000000, 0.5) if nil_value else 0
    war += nil_bonus

    return {
        "war": round(war, 2),
        "position_impact": position_war.get(position, 0.5),
        "star_multiplier": star_mult.get(stars, 1.0),
        "nil_bonus": round(nil_bonus, 2),
    }


def create_position_war_chart(nil_df: pd.DataFrame) -> go.Figure:
    """Create bar chart showing average WAR by position."""
    # Calculate WAR for each player
    war_data = []
    for _, row in nil_df.iterrows():
        impact = calculate_win_impact(row.to_dict())
        war_data.append({
            "position": row["position"],
            "war": impact["war"],
            "nil_value": row.get("nil_value", 0)
        })

    war_df = pd.DataFrame(war_data)
    pos_avg = war_df.groupby("position").agg({
        "war": "mean",
        "nil_value": "mean"
    }).reset_index()
    pos_avg = pos_avg.sort_values("war", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=pos_avg["war"],
        y=pos_avg["position"],
        orientation='h',
        marker_color=COLORS["primary"],
        text=[f"{w:.2f}" for w in pos_avg["war"]],
        textposition='outside',
        textfont=dict(color=COLORS["text_secondary"]),
        name="Avg WAR"
    ))

    fig.update_layout(
        title=dict(text="Average Win Impact by Position", font=dict(color=COLORS["text_primary"])),
        xaxis_title="Wins Above Replacement (WAR)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        xaxis=dict(gridcolor=COLORS["bg_light"]),
        margin=dict(l=20, r=80, t=50, b=50),
        height=400,
    )

    return fig


def create_nil_war_scatter(nil_df: pd.DataFrame) -> go.Figure:
    """Create scatter plot of NIL value vs WAR."""
    war_data = []
    for _, row in nil_df.iterrows():
        impact = calculate_win_impact(row.to_dict())
        # Handle NaN stars values - default to 3
        stars_val = row.get("stars", 3)
        if pd.isna(stars_val):
            stars_val = 3
        else:
            stars_val = int(stars_val)
        war_data.append({
            "name": row["name"],
            "position": row["position"],
            "war": impact["war"],
            "nil_value": row.get("nil_value", 0),
            "stars": stars_val
        })

    war_df = pd.DataFrame(war_data)

    fig = px.scatter(
        war_df,
        x="war",
        y="nil_value",
        color="position",
        size="stars",
        hover_data=["name"],
        title="NIL Value vs Win Impact",
        labels={"war": "Win Impact (WAR)", "nil_value": "NIL Value ($)"}
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        xaxis=dict(gridcolor=COLORS["bg_light"]),
        yaxis=dict(gridcolor=COLORS["bg_light"]),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLORS["text_secondary"])
        ),
        height=500,
    )

    return fig


def create_team_impact_chart(team_df: pd.DataFrame) -> go.Figure:
    """Create chart showing team portal impact."""
    if team_df.empty:
        return go.Figure()

    # Sort by overall score
    team_df = team_df.nlargest(15, "overall_score")

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=team_df["name"],
        y=team_df["overall_score"],
        marker_color=COLORS["primary"],
        text=[f"{s:.0f}" for s in team_df["overall_score"]],
        textposition='outside',
        name="Portal Score"
    ))

    fig.update_layout(
        title=dict(text="Top 15 Portal Classes by Impact Score", font=dict(color=COLORS["text_primary"])),
        xaxis_title="Team",
        yaxis_title="Portal Impact Score",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        yaxis=dict(gridcolor=COLORS["bg_light"]),
        xaxis=dict(tickangle=45),
        margin=dict(l=50, r=50, t=50, b=100),
        height=400,
    )

    return fig


# =============================================================================
# Main Page
# =============================================================================

def main():
    # Header
    st.markdown("""
    <h1 style="color: #00C853;">📈 Win Impact</h1>
    <p style="color: #e6edf3; font-size: 1.1rem;">
        Analyze player contribution to team wins and NIL correlation
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Impact Overview",
        "🔍 Player Analysis",
        "🏆 Team Portal Impact"
    ])

    with tab1:
        render_overview_tab()

    with tab2:
        render_player_tab()

    with tab3:
        render_team_tab()


def render_overview_tab():
    """Render the overview tab with aggregate analytics."""
    nil_df = get_nil_players()

    if nil_df.empty:
        st.warning("No NIL data available. Run the On3 scraper first.")
        return

    # Summary metrics
    st.markdown("### Win Impact Summary")

    # Calculate aggregate stats
    total_players = len(nil_df)
    avg_nil = nil_df["nil_value"].mean()

    # Calculate average WAR
    wars = [calculate_win_impact(row.to_dict())["war"] for _, row in nil_df.iterrows()]
    avg_war = np.mean(wars)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Players Analyzed", f"{total_players:,}")

    with col2:
        st.metric("Avg NIL Value", format_currency(avg_nil))

    with col3:
        st.metric("Avg Win Impact", f"{avg_war:.2f} WAR")

    with col4:
        # NIL per WAR
        nil_per_war = avg_nil / avg_war if avg_war > 0 else 0
        st.metric("NIL per Win", format_currency(nil_per_war))

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Win Impact by Position")
        fig = create_position_war_chart(nil_df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### NIL vs Win Impact Correlation")
        fig = create_nil_war_scatter(nil_df)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Top impact players
    st.markdown("### Top Win Impact Players")

    war_data = []
    for _, row in nil_df.iterrows():
        impact = calculate_win_impact(row.to_dict())
        war_data.append({
            "name": row["name"],
            "position": row["position"],
            "school": row.get("school", "Unknown"),
            "nil_value": row.get("nil_value", 0),
            "war": impact["war"],
        })

    war_df = pd.DataFrame(war_data)
    top_war = war_df.nlargest(10, "war")

    display_df = top_war.copy()
    display_df["nil_value"] = display_df["nil_value"].apply(format_currency)
    display_df.columns = ["Player", "Position", "School", "NIL Value", "Win Impact (WAR)"]

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_player_tab():
    """Render the player analysis tab."""
    nil_df = get_nil_players()

    if nil_df.empty:
        st.warning("No NIL data available.")
        return

    st.markdown("### Analyze Player Win Impact")

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_player = st.selectbox(
            "Select Player",
            options=nil_df["name"].tolist(),
            key="win_impact_player"
        )

    with col2:
        st.write("")
        analyze_btn = st.button("📊 Analyze", type="primary", use_container_width=True)

    if selected_player and analyze_btn:
        player = nil_df[nil_df["name"] == selected_player].iloc[0]
        player_dict = player.to_dict()
        impact = calculate_win_impact(player_dict)

        st.divider()

        # Player card
        col1, col2 = st.columns([1, 2])

        with col1:
            st.markdown(f"""
            <div style="background: {COLORS['bg_medium']}; padding: 20px; border-radius: 10px;">
                <h2 style="color: {COLORS['primary']}; margin-bottom: 15px;">{player['name']}</h2>
                <p><strong>Position:</strong> {player['position']}</p>
                <p><strong>School:</strong> {player.get('school', 'Unknown')}</p>
                <p><strong>Stars:</strong> {'⭐' * (int(player.get('stars', 3)) if pd.notna(player.get('stars')) else 3)}</p>
                <p><strong>NIL Value:</strong> {format_currency(player.get('nil_value', 0))}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # Win Impact breakdown
            st.markdown("### Win Impact Breakdown")

            col_a, col_b, col_c, col_d = st.columns(4)

            with col_a:
                st.metric("Total WAR", f"{impact['war']:.2f}")

            with col_b:
                st.metric("Position Impact", f"{impact['position_impact']:.2f}")

            with col_c:
                st.metric("Star Multiplier", f"{impact['star_multiplier']:.1f}x")

            with col_d:
                st.metric("NIL Bonus", f"+{impact['nil_bonus']:.2f}")

            # Value per win
            nil_value = player.get('nil_value', 0)
            value_per_war = nil_value / impact['war'] if impact['war'] > 0 else 0

            st.markdown(f"""
            <div style="background: {COLORS['bg_light']}; padding: 15px; border-radius: 8px; margin-top: 15px;">
                <h4 style="color: {COLORS['primary']};">Value Analysis</h4>
                <p>This player's NIL value of <strong>{format_currency(nil_value)}</strong>
                   with a win impact of <strong>{impact['war']:.2f} WAR</strong> means
                   their effective cost per win is <strong>{format_currency(value_per_war)}</strong>.</p>
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # Transfer impact projection
        st.markdown("### Transfer Impact Projection")
        st.markdown("_How would this player impact different teams?_")

        target_school = st.selectbox(
            "Select Target School",
            options=get_school_list(),
            key="transfer_impact_school"
        )

        if target_school:
            # Get team ranking info
            team_df = get_team_rankings(year=2026)
            team_info = team_df[team_df["name"] == target_school]

            if not team_info.empty:
                team = team_info.iloc[0]

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        f"{target_school} Current Portal Score",
                        f"{team.get('overall_score', 0):.0f}"
                    )

                with col2:
                    new_score = team.get('overall_score', 0) + (impact['war'] * 10)
                    st.metric(
                        "Projected Score with Player",
                        f"{new_score:.0f}",
                        delta=f"+{impact['war'] * 10:.0f}"
                    )

                with col3:
                    st.metric(
                        "Projected Win Improvement",
                        f"+{impact['war']:.1f} wins"
                    )


def render_team_tab():
    """Render the team portal impact tab."""
    team_df = get_team_rankings(year=2026)
    portal_df = get_portal_players(year=2026)

    if team_df.empty:
        st.warning("No team ranking data available.")
        return

    st.markdown("### 2026 Portal Class Rankings")

    # Team impact chart
    fig = create_team_impact_chart(team_df)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Team details
    st.markdown("### Team Details")

    selected_team = st.selectbox(
        "Select Team for Details",
        options=team_df["name"].tolist(),
        key="team_detail"
    )

    if selected_team:
        team = team_df[team_df["name"] == selected_team].iloc[0]

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Portal Rank", f"#{int(team.get('overall_rank', 0))}")

        with col2:
            st.metric("Portal Score", f"{team.get('overall_score', 0):.0f}")

        with col3:
            st.metric("Transfers In", f"{int(team.get('transfers_in', 0))}")

        with col4:
            st.metric("Net 4-5 Stars", f"{int(team.get('four_stars_net', 0) + team.get('five_stars_net', 0)):+d}")

        st.divider()

        # Show incoming transfers for this team
        st.markdown(f"### {selected_team} Incoming Transfers")

        incoming = portal_df[
            (portal_df["destination_school"].str.contains(selected_team, case=False, na=False)) &
            (portal_df["status"] == "Committed")
        ]

        if not incoming.empty:
            display_df = incoming[["name", "position", "origin_school", "stars"]].head(10)
            display_df.columns = ["Player", "Position", "From", "Stars"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No committed transfers to {selected_team} found in the data.")


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    main()
else:
    main()
