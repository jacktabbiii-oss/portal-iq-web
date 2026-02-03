"""
Win Impact Page - Portal IQ Proprietary Analytics

Advanced player impact analysis using Portal IQ's proprietary algorithms:
- WAR (Wins Above Replacement) based on 6 factors
- Team Portal Impact Scoring
- Transfer Value Analysis
- Impact Projections
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
    get_nil_players, get_portal_players, get_team_rankings, get_school_list,
    get_portal_players_with_measurables
)
from utils.navigation import render_sidebar, get_selected_season
from utils.win_impact_calculator import (
    calculate_player_war, calculate_team_portal_score, analyze_transfer_value,
    project_team_improvement, enrich_with_war, get_school_tier
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

def create_position_war_chart(df: pd.DataFrame) -> go.Figure:
    """Create bar chart showing average WAR by position using Portal IQ algorithm."""
    if "portaliq_war" not in df.columns:
        df = enrich_with_war(df)

    pos_avg = df.groupby("position").agg({
        "portaliq_war": ["mean", "count"],
        "nil_value": "mean"
    }).reset_index()
    pos_avg.columns = ["position", "avg_war", "player_count", "avg_nil"]
    pos_avg = pos_avg[pos_avg["player_count"] >= 5]  # Filter small samples
    pos_avg = pos_avg.sort_values("avg_war", ascending=True)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=pos_avg["avg_war"],
        y=pos_avg["position"],
        orientation='h',
        marker_color=COLORS["primary"],
        text=[f"{w:.2f}" for w in pos_avg["avg_war"]],
        textposition='outside',
        textfont=dict(color=COLORS["text_secondary"]),
        name="Avg WAR",
        hovertemplate="<b>%{y}</b><br>Avg WAR: %{x:.2f}<br>Players: %{customdata}<extra></extra>",
        customdata=pos_avg["player_count"]
    ))

    fig.update_layout(
        title=dict(
            text="Portal IQ Average WAR by Position",
            font=dict(color=COLORS["text_primary"])
        ),
        xaxis_title="Wins Above Replacement (WAR)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        xaxis=dict(gridcolor=COLORS["bg_light"]),
        margin=dict(l=20, r=80, t=50, b=50),
        height=400,
    )

    return fig


def create_war_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """Create histogram of WAR distribution."""
    if "portaliq_war" not in df.columns:
        df = enrich_with_war(df)

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=df["portaliq_war"],
        nbinsx=30,
        marker_color=COLORS["primary"],
        opacity=0.8,
        name="Players"
    ))

    fig.update_layout(
        title=dict(
            text="WAR Distribution Across All Players",
            font=dict(color=COLORS["text_primary"])
        ),
        xaxis_title="Wins Above Replacement (WAR)",
        yaxis_title="Number of Players",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        xaxis=dict(gridcolor=COLORS["bg_light"]),
        yaxis=dict(gridcolor=COLORS["bg_light"]),
        height=350,
    )

    return fig


def create_nil_war_scatter(df: pd.DataFrame) -> go.Figure:
    """Create scatter plot of NIL value vs WAR."""
    if "portaliq_war" not in df.columns:
        df = enrich_with_war(df)

    # Sample if too many points
    plot_df = df.sample(min(500, len(df))) if len(df) > 500 else df.copy()

    # Ensure we have a school column for hover data
    if "school" not in plot_df.columns:
        plot_df["school"] = plot_df.get("destination_school", plot_df.get("origin_school", "Unknown"))

    # Build hover_data with columns that exist
    hover_cols = ["name"]
    if "school" in plot_df.columns:
        hover_cols.append("school")

    fig = px.scatter(
        plot_df,
        x="portaliq_war",
        y="nil_value",
        color="position",
        hover_data=hover_cols,
        title="NIL Value vs Win Impact",
        labels={"portaliq_war": "Portal IQ WAR", "nil_value": "NIL Value ($)"}
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
        height=450,
    )

    return fig


def create_team_impact_chart(teams_data: list) -> go.Figure:
    """Create bar chart for team portal scores."""
    if not teams_data:
        return go.Figure()

    teams_df = pd.DataFrame(teams_data)
    teams_df = teams_df.nlargest(20, "portal_score")

    fig = go.Figure()

    # Add bars with grade-based coloring
    colors = []
    for grade in teams_df["grade"]:
        if grade in ["A+", "A"]:
            colors.append(COLORS["primary"])
        elif grade in ["B+", "B"]:
            colors.append(COLORS["chart_2"])
        elif grade in ["C+", "C"]:
            colors.append(COLORS["chart_4"])
        else:
            colors.append(COLORS["text_muted"])

    fig.add_trace(go.Bar(
        x=teams_df["team"],
        y=teams_df["portal_score"],
        marker_color=colors,
        text=[f"{s:.0f} ({g})" for s, g in zip(teams_df["portal_score"], teams_df["grade"])],
        textposition='outside',
        hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<br>WAR Added: %{customdata:.2f}<extra></extra>",
        customdata=teams_df["war_added"]
    ))

    fig.update_layout(
        title=dict(
            text="Portal IQ Team Impact Scores (Top 20)",
            font=dict(color=COLORS["text_primary"])
        ),
        xaxis_title="Team",
        yaxis_title="Portal IQ Score",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        yaxis=dict(gridcolor=COLORS["bg_light"]),
        xaxis=dict(tickangle=45),
        margin=dict(l=50, r=50, t=50, b=100),
        height=450,
    )

    return fig


# =============================================================================
# Main Page
# =============================================================================

def main():
    # Render shared navigation sidebar
    render_sidebar()

    # Header - Navy/Gold branding
    st.markdown(f"""
    <h1 style="color: {COLORS['primary']};">📈 Win Impact</h1>
    <p style="color: {COLORS['text_secondary']}; font-size: 1.1rem;">
        Portal IQ's proprietary player impact analysis powered by advanced WAR algorithms
    </p>
    """, unsafe_allow_html=True)

    # Algorithm info expander
    with st.expander("ℹ️ About Portal IQ's WAR Algorithm"):
        st.markdown(f"""
        <div style="color: {COLORS['text_secondary']};">
        <p><strong>Portal IQ WAR (Wins Above Replacement)</strong> is our proprietary algorithm that considers:</p>
        <ul>
            <li><strong>Position Value & Scarcity</strong> - QBs and EDGE rushers have highest impact</li>
            <li><strong>Recruiting Profile</strong> - Star rating plus recruiting rating bonuses</li>
            <li><strong>NIL Market Signal</strong> - Market valuation as indicator of perceived value</li>
            <li><strong>Destination School Tier</strong> - Elite programs maximize player potential</li>
            <li><strong>Physical Measurables</strong> - Height/weight fit for position</li>
            <li><strong>Experience Factor</strong> - Juniors typically peak, freshmen developing</li>
        </ul>
        <p>Unlike basic portal rankings, our algorithm creates a holistic view of true on-field impact.</p>
        </div>
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
    selected_season = get_selected_season()
    portal_year = selected_season + 1

    with st.spinner("Loading player data and calculating WAR..."):
        # Try to get players with measurables for better WAR calculation
        try:
            nil_df = get_portal_players_with_measurables(year=portal_year)
        except Exception:
            nil_df = get_nil_players()

        if nil_df.empty:
            st.warning("No player data available. Check data sources.")
            return

        # Enrich with Portal IQ WAR
        nil_df = enrich_with_war(nil_df)

    # Summary metrics
    st.markdown("### Win Impact Summary")

    total_players = len(nil_df)
    avg_nil = nil_df["nil_value"].mean() if "nil_value" in nil_df.columns else 0
    avg_war = nil_df["portaliq_war"].mean()
    total_war = nil_df["portaliq_war"].sum()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Players Analyzed", f"{total_players:,}")

    with col2:
        st.metric("Avg Portal IQ WAR", f"{avg_war:.2f}")

    with col3:
        st.metric("Total WAR Pool", f"{total_war:.1f}")

    with col4:
        nil_per_war = avg_nil / avg_war if avg_war > 0 else 0
        st.metric("Avg NIL per WAR", format_currency(nil_per_war))

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### WAR by Position")
        fig = create_position_war_chart(nil_df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### NIL vs Win Impact Correlation")
        fig = create_nil_war_scatter(nil_df)
        st.plotly_chart(fig, use_container_width=True)

    # WAR distribution
    st.markdown("### WAR Distribution")
    fig = create_war_distribution_chart(nil_df)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Top impact players
    st.markdown("### Top Win Impact Players")

    top_war = nil_df.nlargest(15, "portaliq_war")

    display_data = []
    for _, row in top_war.iterrows():
        display_data.append({
            "Player": row["name"],
            "Position": row["position"],
            "School": row.get("school") or row.get("destination_school", "Unknown"),
            "NIL Value": format_currency(row.get("nil_value", 0)),
            "Portal IQ WAR": f"{row['portaliq_war']:.2f}",
            "Confidence": row.get("war_confidence", "medium").title()
        })

    display_df = pd.DataFrame(display_data)
    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_player_tab():
    """Render the player analysis tab with detailed WAR breakdown."""
    selected_season = get_selected_season()
    portal_year = selected_season + 1

    # Load data
    try:
        nil_df = get_portal_players_with_measurables(year=portal_year)
    except Exception:
        nil_df = get_nil_players()

    if nil_df.empty:
        st.warning("No player data available.")
        return

    st.markdown("### Analyze Player Win Impact")

    # Quick search for players
    player_search = st.text_input(
        "🔍 Search Player",
        placeholder="Type player name (e.g., 'Jeremiah Smith')...",
        key="win_impact_player_search"
    )

    # Filter player list based on search
    player_names = nil_df["name"].dropna().unique().tolist()
    if player_search:
        filtered_players = [p for p in player_names if player_search.lower() in p.lower()]
    else:
        filtered_players = sorted(player_names)[:500]

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_player = st.selectbox(
            "Select Player",
            options=filtered_players if filtered_players else sorted(player_names)[:100],
            key="win_impact_player"
        )

    with col2:
        st.write("")
        analyze_btn = st.button("📊 Analyze Impact", type="primary", use_container_width=True)

    if selected_player and analyze_btn:
        player_row = nil_df[nil_df["name"] == selected_player]
        if player_row.empty:
            st.error("Player not found")
            return

        player = player_row.iloc[0]

        # Calculate detailed WAR
        war_result = calculate_player_war(
            position=player.get("position"),
            stars=player.get("stars"),
            rating=player.get("overall_rating"),
            nil_value=player.get("portaliq_value") or player.get("nil_value", 0),
            destination_school=player.get("destination_school") or player.get("school"),
            height=player.get("height_inches"),
            weight=player.get("weight"),
            year=player.get("year"),
            is_predicted_nil=player.get("is_predicted", True)
        )

        st.divider()

        # Player card
        col1, col2 = st.columns([1, 2])

        with col1:
            stars_val = int(player.get("stars", 3)) if pd.notna(player.get("stars")) else 3
            school = player.get("destination_school") or player.get("school", "Unknown")

            st.markdown(f"""
            <div style="background: {COLORS['bg_medium']}; padding: 20px; border-radius: 10px; border-left: 4px solid {COLORS['primary']};">
                <h2 style="color: {COLORS['primary']}; margin-bottom: 15px;">{player['name']}</h2>
                <p style="color: {COLORS['text_secondary']}; margin: 5px 0;"><strong>Position:</strong> {player['position']}</p>
                <p style="color: {COLORS['text_secondary']}; margin: 5px 0;"><strong>School:</strong> {school}</p>
                <p style="color: {COLORS['text_secondary']}; margin: 5px 0;"><strong>Stars:</strong> {'⭐' * stars_val}</p>
                <p style="color: {COLORS['text_secondary']}; margin: 5px 0;"><strong>NIL Value:</strong> {format_currency(player.get('nil_value', 0) or player.get('portaliq_value', 0))}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            # WAR breakdown
            st.markdown("### Portal IQ WAR Breakdown")

            breakdown = war_result["breakdown"]

            cols = st.columns(4)
            with cols[0]:
                st.metric("Total WAR", f"{war_result['war']:.2f}")
            with cols[1]:
                st.metric("WAR Range", f"{war_result['war_low']:.2f} - {war_result['war_high']:.2f}")
            with cols[2]:
                st.metric("Confidence", war_result['confidence'].title())
            with cols[3]:
                st.metric("School Tier", breakdown['school_tier'].title())

            # Detailed breakdown
            st.markdown("#### Factor Breakdown")

            factor_cols = st.columns(3)
            with factor_cols[0]:
                st.markdown(f"""
                <div style="background: {COLORS['bg_light']}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin: 0;">Base WAR (Position)</p>
                    <p style="color: {COLORS['text_primary']}; font-size: 1.2rem; margin: 0; font-weight: bold;">{breakdown['base_war']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background: {COLORS['bg_light']}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin: 0;">Position Scarcity</p>
                    <p style="color: {COLORS['text_primary']}; font-size: 1.2rem; margin: 0; font-weight: bold;">×{breakdown['position_scarcity']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

            with factor_cols[1]:
                st.markdown(f"""
                <div style="background: {COLORS['bg_light']}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin: 0;">Star Multiplier</p>
                    <p style="color: {COLORS['text_primary']}; font-size: 1.2rem; margin: 0; font-weight: bold;">×{breakdown['star_multiplier']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background: {COLORS['bg_light']}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin: 0;">School Multiplier</p>
                    <p style="color: {COLORS['text_primary']}; font-size: 1.2rem; margin: 0; font-weight: bold;">×{breakdown['school_multiplier']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

            with factor_cols[2]:
                st.markdown(f"""
                <div style="background: {COLORS['bg_light']}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin: 0;">Measurables Factor</p>
                    <p style="color: {COLORS['text_primary']}; font-size: 1.2rem; margin: 0; font-weight: bold;">×{breakdown['measurables_factor']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div style="background: {COLORS['bg_light']}; padding: 10px; border-radius: 8px; margin: 5px 0;">
                    <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin: 0;">NIL Market Bonus</p>
                    <p style="color: {COLORS['primary']}; font-size: 1.2rem; margin: 0; font-weight: bold;">+{breakdown['nil_bonus']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # Transfer Value Analysis
        st.markdown("### Transfer Value Analysis")

        nil_val = player.get("portaliq_value") or player.get("nil_value", 0)
        value_analysis = analyze_transfer_value(
            player_war=war_result["war"],
            nil_value=nil_val,
            position=player.get("position", "ATH")
        )

        val_cols = st.columns(4)
        with val_cols[0]:
            st.metric("Cost per WAR", format_currency(value_analysis["cost_per_war"]))
        with val_cols[1]:
            st.metric("Fair Value/WAR", format_currency(value_analysis["fair_value_per_war"]))
        with val_cols[2]:
            rating_color = COLORS["primary"] if "value" in value_analysis["value_rating"] else COLORS["risk_high"]
            st.markdown(f"""
            <div style="text-align: center;">
                <p style="color: {COLORS['text_muted']}; font-size: 0.8rem; margin-bottom: 5px;">Value Rating</p>
                <p style="color: {rating_color}; font-size: 1.2rem; font-weight: bold; margin: 0;">{value_analysis['value_rating'].replace('_', ' ').title()}</p>
            </div>
            """, unsafe_allow_html=True)
        with val_cols[3]:
            st.metric("Market Comparison", value_analysis["market_comparison"])

        st.info(f"**ROI Projection:** {value_analysis['roi_projection']}")

        st.divider()

        # Transfer Impact Projection
        st.markdown("### Transfer Impact Projection")
        st.markdown("_How would this player impact different teams?_")

        target_school = st.selectbox(
            "Select Target School",
            options=get_school_list(),
            key="transfer_impact_school"
        )

        if target_school:
            # Get team info
            tier_name, tier_data = get_school_tier(target_school)

            # Project improvement
            projection = project_team_improvement(
                player_war=war_result["war"],
                team_tier=tier_name
            )

            proj_cols = st.columns(4)

            with proj_cols[0]:
                st.metric(f"{target_school.split()[0]} Tier", tier_name.title())

            with proj_cols[1]:
                st.metric("Current Win Baseline", f"{projection['current_baseline']:.0f} wins")

            with proj_cols[2]:
                st.metric(
                    "Projected Improvement",
                    f"+{projection['projected_wins_added']:.1f} wins",
                    delta=f"to {projection['new_projected_wins']:.1f} total"
                )

            with proj_cols[3]:
                st.metric("Playoff Impact", projection["playoff_impact"])

            if projection["diminishing_factor"] < 1:
                st.caption(f"_Note: Diminishing returns factor of {projection['diminishing_factor']:.0%} applied for already-competitive team._")


def render_team_tab():
    """Render the team portal impact tab with proprietary scoring."""
    selected_season = get_selected_season()
    portal_year = selected_season + 1

    st.markdown(f"### {portal_year} Portal IQ Team Impact Rankings")

    with st.spinner("Calculating team portal impact scores..."):
        # Load portal data
        portal_df = get_portal_players(year=portal_year)

        if portal_df.empty:
            st.warning("No portal data available.")
            return

        # Get unique destination schools
        schools = portal_df["destination_school"].dropna().unique()

        # Calculate Portal IQ score for each team
        team_scores = []

        for school in schools:
            if not school or len(str(school)) < 2:
                continue

            incoming = portal_df[
                (portal_df["destination_school"] == school) &
                (portal_df["status"] == "Committed")
            ]

            if len(incoming) < 1:
                continue

            outgoing = portal_df[
                (portal_df["origin_school"].str.contains(str(school).split()[0], case=False, na=False))
            ]

            score_result = calculate_team_portal_score(
                incoming_players=incoming,
                outgoing_players=outgoing,
                team_name=school
            )

            team_scores.append({
                "team": school,
                **score_result
            })

        if not team_scores:
            st.warning("No team data to display.")
            return

        # Sort by portal score
        team_scores = sorted(team_scores, key=lambda x: x["portal_score"], reverse=True)

    # Top teams chart
    fig = create_team_impact_chart(team_scores)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Team details selector
    st.markdown("### Team Details")

    # Quick search for teams
    team_search = st.text_input(
        "🔍 Search Team",
        placeholder="Type team name...",
        key="team_detail_search"
    )

    team_names = [t["team"] for t in team_scores]
    if team_search:
        filtered_teams = [t for t in team_names if team_search.lower() in t.lower()]
    else:
        filtered_teams = team_names

    selected_team = st.selectbox(
        "Select Team for Detailed Analysis",
        options=filtered_teams if filtered_teams else team_names,
        key="team_detail_select"
    )

    if selected_team:
        team_data = next((t for t in team_scores if t["team"] == selected_team), None)

        if team_data:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                grade_color = COLORS["primary"] if team_data["grade"] in ["A+", "A", "B+"] else COLORS["text_secondary"]
                st.markdown(f"""
                <div style="text-align: center; background: {COLORS['bg_medium']}; padding: 15px; border-radius: 10px;">
                    <p style="color: {COLORS['text_muted']}; margin: 0; font-size: 0.9rem;">Portal Grade</p>
                    <p style="color: {grade_color}; font-size: 2.5rem; font-weight: bold; margin: 0;">{team_data['grade']}</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.metric("Portal IQ Score", f"{team_data['portal_score']:.1f}")

            with col3:
                st.metric("WAR Added", f"+{team_data['war_added']:.2f}")

            with col4:
                st.metric("Net WAR", f"{team_data['net_war']:+.2f}")

            # Detailed breakdown
            st.markdown("#### Detailed Breakdown")

            breakdown = team_data["breakdown"]

            detail_cols = st.columns(4)
            with detail_cols[0]:
                st.metric("Transfers In", breakdown["transfers_in"])
            with detail_cols[1]:
                st.metric("Avg WAR/Transfer", f"{team_data['avg_war_per_transfer']:.2f}")
            with detail_cols[2]:
                st.metric("Position Balance", f"{breakdown['position_balance']:.0%}")
            with detail_cols[3]:
                st.metric("Star Quality", f"{breakdown['star_quality']:.2f}")

            # Star distribution
            st.markdown("#### Transfer Quality Distribution")
            star_dist = breakdown["star_distribution"]

            star_cols = st.columns(4)
            with star_cols[0]:
                st.metric("5-Star Transfers", star_dist.get(5, 0))
            with star_cols[1]:
                st.metric("4-Star Transfers", star_dist.get(4, 0))
            with star_cols[2]:
                st.metric("3-Star Transfers", star_dist.get(3, 0))
            with star_cols[3]:
                st.metric("2-Star Transfers", star_dist.get(2, 0))

            st.divider()

            # Show incoming transfers
            st.markdown(f"#### {selected_team} Incoming Transfers")

            incoming = portal_df[
                (portal_df["destination_school"] == selected_team) &
                (portal_df["status"] == "Committed")
            ]

            if not incoming.empty:
                # Enrich with WAR
                incoming = enrich_with_war(incoming, school_col="destination_school")

                display_cols = ["name", "position", "origin_school", "stars", "portaliq_war"]
                display_df = incoming[display_cols].copy()
                display_df.columns = ["Player", "Position", "From", "Stars", "Portal IQ WAR"]
                display_df = display_df.sort_values("Portal IQ WAR", ascending=False)
                display_df["Portal IQ WAR"] = display_df["Portal IQ WAR"].apply(lambda x: f"{x:.2f}")

                st.dataframe(display_df.head(15), use_container_width=True, hide_index=True)
            else:
                st.info(f"No committed transfers to {selected_team} found.")


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    main()
else:
    main()
