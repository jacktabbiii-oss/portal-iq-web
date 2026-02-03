"""
Portal Intelligence Page

Transfer portal analytics for college football.
- Roster Flight Risk analysis
- Portal Player Search and filtering
- Portal Fit Analyzer
- Player Watchlist management
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import (
    apply_custom_css, COLORS, get_risk_color, get_risk_color_by_value,
    format_currency, render_risk_badge
)
from utils.data_loader import (
    load_sample_data, get_school_list, get_positions, get_conferences,
    get_roster_for_school, get_portal_players as get_portal_data,
    get_portal_statuses, get_team_rankings,
    get_portal_players_with_measurables, filter_by_measurables,
    format_height, get_player_measurables,
    HEIGHT_PRESETS, WEIGHT_PRESETS
)
from utils.navigation import render_sidebar, get_selected_season
from utils.nil_estimator import format_value_range, get_tier_from_value

# Page config
st.set_page_config(
    page_title="Portal Intelligence | Portal IQ",
    page_icon="🔄",
    layout="wide",
)

apply_custom_css()


# =============================================================================
# Watchlist Management
# =============================================================================

def init_watchlist():
    """Initialize watchlist in session state."""
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = {}
    if "watchlist_notes" not in st.session_state:
        st.session_state.watchlist_notes = {}


def add_to_watchlist(player_data: dict):
    """Add a player to the watchlist."""
    init_watchlist()
    player_id = f"{player_data.get('name', '')}_{player_data.get('origin_school', '')}"
    st.session_state.watchlist[player_id] = {
        "name": player_data.get("name", ""),
        "position": player_data.get("position", ""),
        "origin_school": player_data.get("origin_school", ""),
        "destination_school": player_data.get("destination_school", ""),
        "stars": player_data.get("stars", 0),
        "portaliq_value": player_data.get("portaliq_value", 0),
        "on3_nil_value": player_data.get("on3_nil_value", 0),
        "status": player_data.get("status", ""),
        "overall_rating": player_data.get("overall_rating", 0),
        "height_display": player_data.get("height_display", ""),
        "weight": player_data.get("weight", 0),
        "added_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "headshot_url": player_data.get("headshot_url", ""),
    }


def remove_from_watchlist(player_id: str):
    """Remove a player from the watchlist."""
    init_watchlist()
    if player_id in st.session_state.watchlist:
        del st.session_state.watchlist[player_id]
    if player_id in st.session_state.watchlist_notes:
        del st.session_state.watchlist_notes[player_id]


def is_in_watchlist(player_name: str, origin_school: str) -> bool:
    """Check if a player is in the watchlist."""
    init_watchlist()
    player_id = f"{player_name}_{origin_school}"
    return player_id in st.session_state.watchlist


def get_watchlist() -> dict:
    """Get the current watchlist."""
    init_watchlist()
    return st.session_state.watchlist


def update_watchlist_note(player_id: str, note: str):
    """Update the note for a watchlisted player."""
    init_watchlist()
    st.session_state.watchlist_notes[player_id] = note


def get_watchlist_note(player_id: str) -> str:
    """Get the note for a watchlisted player."""
    init_watchlist()
    return st.session_state.watchlist_notes.get(player_id, "")


# =============================================================================
# Cache Functions
# =============================================================================

@st.cache_data(ttl=300)
def get_portal_players():
    """Get cached portal player data."""
    return load_sample_data("portal_players")


@st.cache_data(ttl=300)
def get_school_roster(school: str):
    """Get cached roster for a school."""
    return get_roster_for_school(school)


# =============================================================================
# Helper Functions
# =============================================================================

def create_risk_gauge(risk_value: float, title: str = "Flight Risk") -> go.Figure:
    """Create a gauge chart for risk visualization."""
    color = get_risk_color_by_value(risk_value)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_value * 100,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'color': COLORS["text_primary"]}},
        number={'suffix': '%', 'font': {'color': color}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': COLORS["text_muted"]},
            'bar': {'color': color},
            'bgcolor': COLORS["bg_medium"],
            'bordercolor': COLORS["bg_light"],
            'steps': [
                {'range': [0, 30], 'color': 'rgba(76, 175, 80, 0.3)'},
                {'range': [30, 50], 'color': 'rgba(255, 193, 7, 0.3)'},
                {'range': [50, 70], 'color': 'rgba(255, 152, 0, 0.3)'},
                {'range': [70, 100], 'color': 'rgba(244, 67, 54, 0.3)'},
            ],
            'threshold': {
                'line': {'color': COLORS["text_primary"], 'width': 2},
                'thickness': 0.75,
                'value': risk_value * 100
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={'color': COLORS["text_secondary"]},
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def create_position_risk_chart(roster_df: pd.DataFrame) -> go.Figure:
    """Create bar chart of average flight risk by position."""
    pos_risk = roster_df.groupby("position")["flight_risk"].mean().sort_values(ascending=True)

    colors = [get_risk_color_by_value(r) for r in pos_risk.values]

    fig = go.Figure(go.Bar(
        x=pos_risk.values * 100,
        y=pos_risk.index,
        orientation='h',
        marker_color=colors,
        text=[f"{r*100:.0f}%" for r in pos_risk.values],
        textposition='outside',
    ))

    fig.update_layout(
        title=dict(text="Average Flight Risk by Position", font=dict(color=COLORS["text_primary"])),
        xaxis_title="Flight Risk %",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        xaxis=dict(gridcolor=COLORS["bg_light"], range=[0, 100]),
        margin=dict(l=20, r=80, t=50, b=50),
        height=400,
    )

    return fig


def create_fit_breakdown_chart(breakdown: dict) -> go.Figure:
    """Create radar chart for fit breakdown."""
    categories = list(breakdown.keys())
    values = list(breakdown.values())

    # Close the radar chart
    categories += [categories[0]]
    values += [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor=f"rgba(0, 200, 83, 0.3)",
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(size=8, color=COLORS["primary"]),
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                gridcolor=COLORS["bg_light"],
                tickfont=dict(color=COLORS["text_muted"]),
            ),
            angularaxis=dict(
                gridcolor=COLORS["bg_light"],
                tickfont=dict(color=COLORS["text_secondary"]),
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        showlegend=False,
        height=350,
        margin=dict(l=80, r=80, t=50, b=50),
    )

    return fig


def style_risk_cell(val):
    """Style function for risk values in dataframe."""
    if isinstance(val, (int, float)):
        color = get_risk_color_by_value(val)
        return f"background-color: {color}; color: white; font-weight: bold;"
    return ""


# =============================================================================
# Main Page
# =============================================================================

def main():
    # Render shared navigation sidebar
    render_sidebar()

    # Header - Navy/Gold branding
    st.markdown(f"""
    <h1 style="color: {COLORS['primary']};">🔄 Portal Intelligence</h1>
    <p style="color: {COLORS['text_secondary']}; font-size: 1.1rem;">
        Transfer portal analytics and flight risk monitoring
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    # Initialize watchlist
    init_watchlist()

    # Watchlist badge count
    watchlist_count = len(get_watchlist())
    watchlist_label = f"⭐ Watchlist ({watchlist_count})" if watchlist_count > 0 else "⭐ Watchlist"

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Roster Flight Risk",
        "🔍 Portal Player Search",
        "🎯 Portal Fit Analyzer",
        "📋 Team Needs Analysis",
        watchlist_label
    ])

    with tab1:
        render_flight_risk_tab()

    with tab2:
        render_portal_search_tab()

    with tab3:
        render_fit_analyzer_tab()

    with tab4:
        render_team_needs_tab()

    with tab5:
        render_watchlist_tab()


# =============================================================================
# Tab 1: Portal Activity Analysis (was Flight Risk)
# =============================================================================

def render_flight_risk_tab():
    """Render the portal activity analysis tab for a school."""
    st.markdown("### School Portal Activity Analysis")
    st.markdown("_Analyze incoming and outgoing transfer portal activity for any school_")

    # Get selected season
    selected_season = get_selected_season()
    portal_year = selected_season + 1

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        selected_school = st.selectbox(
            "Select School",
            options=get_school_list(),
            key="flight_risk_school"
        )

    with col2:
        year_filter = st.selectbox(
            "Portal Year",
            options=[2026, 2025, 2024],
            index=[2026, 2025, 2024].index(portal_year) if portal_year in [2026, 2025, 2024] else 0,
            key="activity_year"
        )

    with col3:
        st.write("")
        analyze_btn = st.button("🔍 Analyze Activity", type="primary", use_container_width=True)

    if selected_school and analyze_btn:
        with st.spinner("Analyzing portal activity..."):
            render_portal_activity_results(selected_school, year_filter)


def render_portal_activity_results(school: str, year: int):
    """Render portal activity analysis results."""
    # Get all portal players for the year
    portal_df = get_portal_data(year=year, enrich_nil=True)

    if portal_df.empty:
        st.warning("No portal data available for this year.")
        return

    st.divider()

    # Find incoming and outgoing transfers
    incoming = portal_df[
        portal_df["destination_school"].str.contains(school, case=False, na=False) &
        (portal_df["status"] == "Committed")
    ].copy()

    outgoing = portal_df[
        portal_df["origin_school"].str.contains(school, case=False, na=False)
    ].copy()

    # Get team ranking info
    team_df = get_team_rankings(year=year)
    team_info = team_df[team_df["name"].str.contains(school, case=False, na=False)]

    # Header
    st.markdown(f"## {school} - {year} Portal Activity")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    incoming_nil = incoming["portaliq_value"].sum() if not incoming.empty else 0
    outgoing_nil = outgoing["portaliq_value"].sum() if not outgoing.empty else 0
    net_nil = incoming_nil - outgoing_nil

    with col1:
        st.metric(
            "Incoming Transfers",
            len(incoming),
            delta=f"{len(incoming[incoming['stars'] >= 4]) if not incoming.empty else 0} 4/5-Stars"
        )

    with col2:
        st.metric(
            "Outgoing to Portal",
            len(outgoing),
            delta=f"{len(outgoing[outgoing['status'] == 'Committed'])} committed elsewhere",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            "Net NIL Investment",
            format_currency(net_nil),
            delta="Incoming - Outgoing"
        )

    with col4:
        if not team_info.empty:
            rank = team_info.iloc[0].get("overall_rank", "N/A")
            score = team_info.iloc[0].get("overall_score", 0)
            st.metric(
                "Portal Class Rank",
                f"#{int(rank)}" if pd.notna(rank) else "N/A",
                delta=f"Score: {score:.0f}" if pd.notna(score) else None
            )
        else:
            st.metric("Portal Class Rank", "N/A")

    st.divider()

    # Two columns for incoming/outgoing
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🟢 Incoming Transfers")
        if not incoming.empty:
            # Display incoming transfers
            display_incoming = incoming[["name", "position", "origin_school", "stars", "portaliq_value"]].copy()
            display_incoming["portaliq_value"] = display_incoming["portaliq_value"].apply(format_currency)
            display_incoming["stars"] = display_incoming["stars"].apply(
                lambda x: f"{'⭐' * int(x)}" if pd.notna(x) and x > 0 else "—"
            )
            display_incoming.columns = ["Player", "Pos", "From", "Stars", "Est. NIL"]
            display_incoming = display_incoming.sort_values("Est. NIL", ascending=False, key=lambda x: x.str.replace(r'[\$,KM]', '', regex=True).astype(float))

            st.dataframe(display_incoming.head(15), use_container_width=True, hide_index=True)

            # Position breakdown
            if len(incoming) > 0:
                pos_counts = incoming["position"].value_counts().head(5)
                st.markdown("**By Position:**")
                st.bar_chart(pos_counts)
        else:
            st.info("No committed incoming transfers yet.")

    with col2:
        st.markdown("### 🔴 Players in Portal")
        if not outgoing.empty:
            # Display outgoing transfers
            display_outgoing = outgoing[["name", "position", "status", "destination_school", "stars", "portaliq_value"]].copy()
            display_outgoing["portaliq_value"] = display_outgoing["portaliq_value"].apply(format_currency)
            display_outgoing["stars"] = display_outgoing["stars"].apply(
                lambda x: f"{'⭐' * int(x)}" if pd.notna(x) and x > 0 else "—"
            )
            display_outgoing["destination_school"] = display_outgoing["destination_school"].fillna("TBD")
            display_outgoing.columns = ["Player", "Pos", "Status", "Destination", "Stars", "Est. NIL"]

            st.dataframe(display_outgoing.head(15), use_container_width=True, hide_index=True)

            # Status breakdown
            status_counts = outgoing["status"].value_counts()
            st.markdown("**By Status:**")
            for status, count in status_counts.items():
                color = COLORS["primary"] if status == "Committed" else COLORS["risk_moderate"] if status == "Entered" else COLORS["text_muted"]
                st.markdown(f"<span style='color: {color};'>● {status}: {count}</span>", unsafe_allow_html=True)
        else:
            st.info("No players from this school in the portal.")

    st.divider()

    # NIL Impact Analysis
    st.markdown("### 💰 NIL Impact Analysis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total NIL Incoming",
            format_currency(incoming_nil),
            delta=f"Avg: {format_currency(incoming_nil / len(incoming))}" if len(incoming) > 0 else None
        )

    with col2:
        st.metric(
            "Total NIL Lost",
            format_currency(outgoing_nil),
            delta=f"Avg: {format_currency(outgoing_nil / len(outgoing))}" if len(outgoing) > 0 else None,
            delta_color="inverse"
        )

    with col3:
        # Calculate roster upgrade score
        incoming_stars = incoming["stars"].fillna(0).sum() if not incoming.empty else 0
        outgoing_stars = outgoing["stars"].fillna(0).sum() if not outgoing.empty else 0
        star_diff = incoming_stars - outgoing_stars

        st.metric(
            "Net Star Rating Change",
            f"{star_diff:+.0f}⭐",
            delta="Roster upgraded" if star_diff > 0 else "Roster downgraded" if star_diff < 0 else "Neutral"
        )

    # Position need analysis
    if not incoming.empty or not outgoing.empty:
        st.divider()
        st.markdown("### 📊 Position Group Analysis")

        # Combine position data
        positions = set()
        if not incoming.empty:
            positions.update(incoming["position"].dropna().unique())
        if not outgoing.empty:
            positions.update(outgoing["position"].dropna().unique())

        pos_analysis = []
        for pos in positions:
            inc_count = len(incoming[incoming["position"] == pos]) if not incoming.empty else 0
            out_count = len(outgoing[outgoing["position"] == pos]) if not outgoing.empty else 0
            inc_nil = incoming[incoming["position"] == pos]["portaliq_value"].sum() if not incoming.empty else 0
            out_nil = outgoing[outgoing["position"] == pos]["portaliq_value"].sum() if not outgoing.empty else 0

            pos_analysis.append({
                "Position": pos,
                "Incoming": inc_count,
                "Outgoing": out_count,
                "Net": inc_count - out_count,
                "NIL In": format_currency(inc_nil),
                "NIL Out": format_currency(out_nil),
                "Net NIL": format_currency(inc_nil - out_nil),
            })

        pos_df = pd.DataFrame(pos_analysis)
        pos_df = pos_df.sort_values("Net", ascending=False)
        st.dataframe(pos_df, use_container_width=True, hide_index=True)


# =============================================================================
# Tab 2: Portal Player Search
# =============================================================================

def render_portal_search_tab():
    """Render the portal player search tab."""
    st.markdown("### Search & Filter Portal Players")

    # Get selected season for context
    selected_season = get_selected_season()
    default_year = selected_season + 1  # Portal year is season + 1

    # Filters - Row 1
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        year_options = [2026, 2025, 2024]
        default_idx = year_options.index(default_year) if default_year in year_options else 0
        year_filter = st.selectbox(
            "Portal Year",
            options=year_options,
            index=default_idx,
            key="portal_year_filter"
        )

    with col2:
        status_filter = st.multiselect(
            "Status",
            options=get_portal_statuses(),
            default=["Entered"],
            key="portal_status_filter"
        )

    with col3:
        position_filter = st.multiselect(
            "Position",
            options=get_positions(),
            default=[],
            key="portal_pos_filter"
        )

    with col4:
        stars_filter = st.slider(
            "Star Rating",
            min_value=0,
            max_value=5,
            value=(0, 5),
            key="portal_stars_filter"
        )

    # Row 2 - Measurables filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        conference_filter = st.multiselect(
            "Origin Conference",
            options=get_conferences(),
            default=[],
            key="portal_conf_filter"
        )

    with col2:
        target_school = st.selectbox(
            "Show Fit Scores For",
            options=["None"] + get_school_list(),
            key="portal_target_school"
        )

    with col3:
        # Height filter (in feet-inches format)
        height_options = ["Any", "6'0\"+", "6'2\"+", "6'4\"+", "6'6\"+", "Under 6'0\"", "Custom"]
        height_filter = st.selectbox(
            "Height",
            options=height_options,
            key="portal_height_filter"
        )

    with col4:
        # Weight filter
        weight_options = ["Any", "200+ lbs", "225+ lbs", "250+ lbs", "280+ lbs", "300+ lbs", "Under 200 lbs", "Custom"]
        weight_filter = st.selectbox(
            "Weight",
            options=weight_options,
            key="portal_weight_filter"
        )

    # Custom measurables sliders (show if "Custom" selected)
    min_height_inches = None
    max_height_inches = None
    min_weight = None
    max_weight = None

    if height_filter == "Custom" or weight_filter == "Custom":
        col1, col2 = st.columns(2)

        with col1:
            if height_filter == "Custom":
                height_range = st.slider(
                    "Height Range (inches)",
                    min_value=60,
                    max_value=84,
                    value=(66, 80),
                    help="60\" = 5'0\", 72\" = 6'0\", 78\" = 6'6\", 84\" = 7'0\"",
                    key="portal_height_range"
                )
                min_height_inches = height_range[0]
                max_height_inches = height_range[1]

        with col2:
            if weight_filter == "Custom":
                weight_range = st.slider(
                    "Weight Range (lbs)",
                    min_value=150,
                    max_value=400,
                    value=(180, 350),
                    key="portal_weight_range"
                )
                min_weight = weight_range[0]
                max_weight = weight_range[1]

    # Parse standard height/weight filters
    if height_filter == "6'0\"+":
        min_height_inches = 72
    elif height_filter == "6'2\"+":
        min_height_inches = 74
    elif height_filter == "6'4\"+":
        min_height_inches = 76
    elif height_filter == "6'6\"+":
        min_height_inches = 78
    elif height_filter == "Under 6'0\"":
        max_height_inches = 71

    if weight_filter == "200+ lbs":
        min_weight = 200
    elif weight_filter == "225+ lbs":
        min_weight = 225
    elif weight_filter == "250+ lbs":
        min_weight = 250
    elif weight_filter == "280+ lbs":
        min_weight = 280
    elif weight_filter == "300+ lbs":
        min_weight = 300
    elif weight_filter == "Under 200 lbs":
        max_weight = 199

    st.divider()

    # Get portal players for selected year WITH MEASURABLES
    portal_df = get_portal_players_with_measurables(year=year_filter)

    # Apply filters
    filtered_df = portal_df.copy()

    if status_filter:
        filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]

    if position_filter:
        filtered_df = filtered_df[filtered_df["position"].isin(position_filter)]

    if stars_filter:
        # Handle NaN stars - treat as 0
        stars_col = filtered_df["stars"].fillna(0)
        filtered_df = filtered_df[
            (stars_col >= stars_filter[0]) &
            (stars_col <= stars_filter[1])
        ]

    # Apply measurables filters
    if min_height_inches or max_height_inches or min_weight or max_weight:
        filtered_df = filter_by_measurables(
            filtered_df,
            min_height=min_height_inches,
            max_height=max_height_inches,
            min_weight=min_weight,
            max_weight=max_weight
        )

    # Add fit scores if target school selected
    if target_school != "None":
        filtered_df = calculate_fit_scores(filtered_df, target_school)

    # Display results
    st.markdown(f"### Portal Players ({len(filtered_df)} found)")

    # Add NIL value comparison legend
    st.markdown("""
    <div style="background: {bg}; padding: 10px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 0.85rem;">
        <strong style="color: {primary};">NIL Values:</strong>
        <span style="color: {text};">
            <strong>Portal IQ</strong> = Our proprietary estimate |
            <strong>On3</strong> = On3's public valuation (if available) |
            <strong>Range</strong> = Confidence-adjusted estimate range
        </span>
    </div>
    """.format(bg=COLORS["bg_medium"], primary=COLORS["primary"], text=COLORS["text_secondary"]), unsafe_allow_html=True)

    if not filtered_df.empty:
        # Prepare display with both NIL values
        display_df = filtered_df.copy()

        # Format Portal IQ value
        display_df["portaliq_fmt"] = display_df["portaliq_value"].apply(
            lambda x: format_currency(x) if pd.notna(x) and x > 0 else "N/A"
        )

        # Format On3 value
        display_df["on3_fmt"] = display_df["on3_nil_value"].apply(
            lambda x: format_currency(x) if pd.notna(x) and x > 0 else "—"
        )

        # Format range
        display_df["range_fmt"] = display_df.apply(
            lambda r: format_value_range(r.get("value_low", 0), r.get("value_high", 0))
            if pd.notna(r.get("value_low")) and r.get("value_low", 0) > 0 else "—",
            axis=1
        )

        # Format confidence
        confidence_badges = {
            "actual": "🟢 On3",
            "high": "🔵 High",
            "medium": "🟡 Medium",
            "low": "🟠 Low"
        }
        display_df["confidence_badge"] = display_df["confidence"].apply(
            lambda x: confidence_badges.get(x, "🟠 Low")
        )

        # Format stars
        display_df["stars_fmt"] = display_df["stars"].apply(
            lambda x: f"{'⭐' * int(x)}" if pd.notna(x) and x > 0 else "—"
        )

        # Format measurables
        display_df["height_fmt"] = display_df["height_display"].fillna("—")
        display_df["weight_fmt"] = display_df["weight"].apply(
            lambda x: f"{int(x)} lbs" if pd.notna(x) and x > 0 else "—"
        )

        # Select columns for display - include measurables
        display_cols = ["name", "position", "origin_school", "height_fmt", "weight_fmt", "stars_fmt", "portaliq_fmt", "confidence_badge"]
        col_names = ["Player", "Position", "Origin School", "Height", "Weight", "Stars", "Portal IQ Est.", "Confidence"]

        if target_school != "None":
            display_cols.extend(["fit_score_fmt", "value_rating"])
            col_names.extend(["Fit Score", "Value Rating"])
            display_df["fit_score_fmt"] = display_df["fit_score"].apply(lambda x: f"{x*100:.0f}%" if pd.notna(x) else "—")
            display_df["value_rating"] = display_df.apply(
                lambda r: "🔥 Great" if r.get("value_score", 0) >= 1.5 else "✓ Good" if r.get("value_score", 0) >= 1.0 else "— Fair",
                axis=1
            )

        show_df = display_df[display_cols].copy()
        show_df.columns = col_names

        # Sort options
        sort_col = st.selectbox(
            "Sort By",
            options=["Portal IQ Est.", "Stars", "Player", "Position"],
            index=0,
            key="portal_sort"
        )

        sort_asc = st.checkbox("Ascending", value=False, key="portal_sort_asc")

        # Custom sort for Portal IQ Est. (need to sort by numeric value)
        if sort_col == "Portal IQ Est.":
            display_df = display_df.sort_values("portaliq_value", ascending=sort_asc)
            show_df = display_df[display_cols].copy()
            show_df.columns = col_names
        else:
            show_df = show_df.sort_values(sort_col, ascending=sort_asc)

        st.dataframe(show_df.head(100), use_container_width=True, hide_index=True)

        if len(filtered_df) > 100:
            st.info(f"Showing top 100 of {len(filtered_df)} players. Use filters to narrow results.")

        # Show detail for selected player
        st.divider()

        # Player details header with watchlist quick-add
        st.markdown("### Player Details")

        col_select, col_watch = st.columns([4, 1])

        with col_select:
            selected_player = st.selectbox(
                "Select player for details",
                options=filtered_df["name"].tolist()[:100],
                key="portal_detail_player"
            )

        if selected_player:
            player_row = filtered_df[filtered_df["name"] == selected_player].iloc[0]
            origin_school = player_row.get("origin_school", "")

            with col_watch:
                st.write("")  # Spacing
                if is_in_watchlist(selected_player, origin_school):
                    if st.button("⭐ Remove", key="detail_watch_btn", help="Remove from watchlist", use_container_width=True):
                        player_id = f"{selected_player}_{origin_school}"
                        remove_from_watchlist(player_id)
                        st.rerun()
                else:
                    if st.button("☆ Add to Watchlist", key="detail_watch_btn", help="Add to watchlist", use_container_width=True):
                        add_to_watchlist(player_row.to_dict())
                        st.success(f"Added {selected_player} to watchlist!")
                        st.rerun()

            render_player_detail(filtered_df, selected_player, target_school)
    else:
        st.info("No players match your filters. Try adjusting the criteria.")


def calculate_fit_scores(df: pd.DataFrame, target_school: str) -> pd.DataFrame:
    """Calculate fit scores for players against a target school."""
    df = df.copy()

    # Get target school tier
    team_df = get_team_rankings()
    target_tier = 3  # Default
    if not team_df.empty:
        target_info = team_df[team_df["name"].str.contains(target_school, case=False, na=False)]
        if not target_info.empty:
            # Higher rank = higher tier
            rank = target_info.iloc[0].get("overall_rank", 50)
            if rank <= 15:
                target_tier = 6
            elif rank <= 35:
                target_tier = 5
            elif rank <= 65:
                target_tier = 4
            else:
                target_tier = 3

    # Calculate fit scores based on multiple factors
    for idx, row in df.iterrows():
        # Positional need (simplified - could be enhanced with actual roster data)
        pos_need_base = {"QB": 0.9, "WR": 0.8, "RB": 0.7, "EDGE": 0.85, "CB": 0.8, "OT": 0.75}.get(row.get("position", ""), 0.7)

        # Tier compatibility - players from similar or lower tiers fit well
        player_stars = row.get("stars", 3) or 3
        if player_stars >= 4:
            tier_fit = 0.9 if target_tier >= 4 else 0.7
        elif player_stars >= 3:
            tier_fit = 0.85
        else:
            tier_fit = 0.7 if target_tier <= 4 else 0.5

        # Rating-based fit
        rating = row.get("overall_rating", 0.8) or 0.8
        if rating > 1:
            rating = rating / 100
        rating_fit = 0.5 + (rating * 0.5)

        # Overall fit score
        fit_score = (pos_need_base * 0.4 + tier_fit * 0.35 + rating_fit * 0.25)

        # Value score (fit per dollar)
        nil_value = row.get("portaliq_value", 100000) or 100000
        value_score = (fit_score * 100) / (nil_value / 100000)

        df.at[idx, "fit_score"] = round(fit_score, 2)
        df.at[idx, "value_score"] = round(value_score, 2)

    return df


# =============================================================================
# Headshot Management - CSV-based for bulk URL management
# =============================================================================

# Cache for custom headshots CSV
_custom_headshots_cache = None

def load_custom_headshots() -> dict:
    """Load custom headshot URLs from CSV for bulk management.

    Edit dashboard/static/custom_headshots.csv to add URLs:
    - player_name: Exact player name
    - headshot_url: Any image URL (ESPN, team site, social media, etc.)
    - source: Optional note (ESPN, Team Site, etc.)
    """
    global _custom_headshots_cache

    if _custom_headshots_cache is not None:
        return _custom_headshots_cache

    csv_path = Path(__file__).parent.parent / "static" / "custom_headshots.csv"

    if not csv_path.exists():
        _custom_headshots_cache = {}
        return _custom_headshots_cache

    try:
        df = pd.read_csv(csv_path)
        _custom_headshots_cache = {}
        for _, row in df.iterrows():
            name = str(row.get("player_name", "")).strip().lower()
            url = str(row.get("headshot_url", "")).strip()
            if name and url and url not in ["", "nan", "None"]:
                _custom_headshots_cache[name] = url
    except Exception:
        _custom_headshots_cache = {}

    return _custom_headshots_cache


def get_custom_headshot_url(player_name: str) -> str:
    """Get custom headshot URL from CSV if it exists."""
    custom = load_custom_headshots()
    name_lower = str(player_name).strip().lower()
    return custom.get(name_lower)


def get_player_headshot_html(player: pd.Series) -> str:
    """Generate HTML for player headshot with fallback chain.

    Priority:
    1. Custom URL from CSV (dashboard/static/custom_headshots.csv)
    2. On3 headshot URL (from portal data)
    3. Position-colored initials placeholder

    To add custom photos in bulk, edit custom_headshots.csv with:
    player_name,headshot_url,source
    Travis Hunter,https://espn.com/...,ESPN
    """
    name = player.get("name", "Unknown")
    position = player.get("position", "ATH")
    on3_url = player.get("headshot_url", "")

    # Position-based colors for fallback
    pos_colors = {
        "QB": "#e74c3c", "RB": "#3498db", "WR": "#9b59b6", "TE": "#1abc9c",
        "OT": "#f39c12", "OG": "#f39c12", "C": "#f39c12", "OL": "#f39c12",
        "EDGE": "#e67e22", "DT": "#e67e22", "DL": "#e67e22", "DE": "#e67e22",
        "LB": "#2ecc71", "CB": "#00C853", "S": "#00C853", "DB": "#00C853",
        "K": "#95a5a6", "P": "#95a5a6", "ATH": "#7f8c8d"
    }
    bg_color = pos_colors.get(str(position).upper(), "#7f8c8d")

    # Get initials for fallback
    name_parts = str(name).split()
    initials = "".join([p[0].upper() for p in name_parts[:2]]) if name_parts else "??"

    # 1. Check custom CSV for manual URL override
    custom_url = get_custom_headshot_url(name)

    # 2. Determine which URL to use (custom > on3)
    headshot_url = custom_url or (on3_url if on3_url and str(on3_url) not in ["", "nan", "None"] else None)

    if headshot_url:
        return f"""
        <div style="width: 120px; height: 120px; border-radius: 50%; overflow: hidden;
                    border: 3px solid {COLORS['primary']}; margin: 0 auto 15px auto;
                    background: {bg_color}; display: flex; align-items: center; justify-content: center;">
            <img src="{headshot_url}"
                 style="width: 100%; height: 100%; object-fit: cover;"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';"
            />
            <div style="display: none; width: 100%; height: 100%; align-items: center; justify-content: center;
                        font-size: 2.5rem; font-weight: bold; color: white;">{initials}</div>
        </div>
        """

    # 3. Fallback: colored circle with initials
    return f"""
    <div style="width: 120px; height: 120px; border-radius: 50%;
                background: linear-gradient(135deg, {bg_color} 0%, {bg_color}88 100%);
                border: 3px solid {COLORS['primary']}; margin: 0 auto 15px auto;
                display: flex; align-items: center; justify-content: center;
                font-size: 2.5rem; font-weight: bold; color: white;">
        {initials}
    </div>
    """


def render_player_detail(df: pd.DataFrame, player_name: str, target_school: str):
    """Render detailed player profile card with all available data."""
    player = df[df["name"] == player_name].iloc[0]

    # Get headshot HTML
    headshot_html = get_player_headshot_html(player)

    # Header with player photo and info
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['bg_medium']} 0%, {COLORS['bg_light']} 100%);
                padding: 25px; border-radius: 12px; margin-bottom: 20px; border-left: 4px solid {COLORS['primary']};">
        <div style="display: flex; align-items: center; gap: 20px;">
            <div style="flex-shrink: 0;">
                {headshot_html}
            </div>
            <div>
                <h2 style="color: {COLORS['primary']}; margin: 0 0 5px 0;">{player['name']}</h2>
                <p style="color: {COLORS['text_secondary']}; font-size: 1.1rem; margin: 0;">
                    {player.get('position', 'ATH')} | {player.get('origin_school', 'Unknown')} → {player.get('destination_school', 'TBD')}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📋 Player Profile")

        # Measurables
        height_display = player.get('height_display') or '—'
        weight = player.get('weight')
        weight_display = f"{int(weight)} lbs" if pd.notna(weight) and weight > 0 else '—'

        stars_val = player.get('stars', 0) or 0
        stars_display = '⭐' * int(stars_val) if stars_val > 0 else 'Unknown'
        rating_display = f"{player['overall_rating']:.2f}" if pd.notna(player.get('overall_rating')) else 'N/A'

        st.markdown(f"""
        <div style="background: {COLORS['bg_medium']}; padding: 20px; border-radius: 10px;">
            <table style="width: 100%; color: {COLORS['text_secondary']};">
                <tr>
                    <td style="padding: 8px 0;"><strong>Height:</strong></td>
                    <td style="padding: 8px 0; text-align: right; color: {COLORS['text_primary']}; font-size: 1.1rem;">{height_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Weight:</strong></td>
                    <td style="padding: 8px 0; text-align: right; color: {COLORS['text_primary']}; font-size: 1.1rem;">{weight_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Stars:</strong></td>
                    <td style="padding: 8px 0; text-align: right;">{stars_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Rating:</strong></td>
                    <td style="padding: 8px 0; text-align: right; color: {COLORS['text_primary']};">{rating_display}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0;"><strong>Status:</strong></td>
                    <td style="padding: 8px 0; text-align: right; color: {COLORS['primary']};">{player.get('status', 'Unknown')}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # Check measurables against position standards
        pos = player.get('position', '')
        if pos in HEIGHT_PRESETS and pd.notna(player.get('height_inches')):
            height_inches = player.get('height_inches')
            preset = HEIGHT_PRESETS[pos]
            if height_inches >= preset.get('ideal_min', preset.get('min', 0)):
                st.success(f"✓ Ideal height for {pos}")
            elif height_inches >= preset.get('min', 0):
                st.info(f"○ Meets minimum height for {pos}")
            else:
                st.warning(f"⚠ Below typical {pos} height")

    with col2:
        st.markdown("#### 💰 NIL Valuation")

        # Portal IQ estimate
        portaliq_val = player.get("portaliq_value", 0) or 0
        st.metric(
            "Portal IQ Estimate",
            format_currency(portaliq_val) if portaliq_val > 0 else "N/A",
            delta=f"Confidence: {player.get('confidence', 'low').title()}"
        )

        # On3 value (if available)
        on3_val = player.get("on3_nil_value", 0) or 0
        if on3_val > 0:
            diff = portaliq_val - on3_val
            diff_pct = (diff / on3_val * 100) if on3_val > 0 else 0
            st.metric(
                "On3 Valuation",
                format_currency(on3_val),
                delta=f"{diff_pct:+.0f}% vs Portal IQ"
            )
        else:
            st.metric("On3 Valuation", "Not Available", delta="No public data")

        # Value range
        low = player.get("value_low", 0) or 0
        high = player.get("value_high", 0) or 0
        if low > 0 and high > 0:
            st.markdown(f"**Estimated Range:** {format_value_range(low, high)}")

        # NIL Tier badge
        nil_tier = player.get("nil_tier", get_tier_from_value(portaliq_val))
        tier_colors = {
            "mega": COLORS["primary"],
            "premium": "#2196F3",
            "solid": "#4CAF50",
            "moderate": "#FF9800",
            "entry": "#9E9E9E",
        }
        st.markdown(f"""
        <div style="background: {tier_colors.get(nil_tier, COLORS['bg_light'])}22; padding: 12px; border-radius: 8px;
                    border-left: 4px solid {tier_colors.get(nil_tier, COLORS['bg_light'])}; margin-top: 10px;">
            <strong style="color: {tier_colors.get(nil_tier, COLORS['text_secondary'])};">NIL Tier: {nil_tier.upper()}</strong>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("#### 🎯 Fit Analysis")

        if target_school != "None":
            fit_score = player.get("fit_score", 0.75) or 0.75
            value_score = player.get("value_score", 1.0) or 1.0

            st.metric("Fit Score", f"{fit_score*100:.0f}%",
                     delta="Strong fit" if fit_score >= 0.8 else "Good fit" if fit_score >= 0.7 else "Moderate")
            st.metric("Value Score", f"{value_score:.2f}x",
                     delta="Great value" if value_score >= 1.5 else "Good value" if value_score >= 1.0 else "Premium")

            # Potential destinations based on fit
            st.markdown("**Potential Fits:**")
            potential_schools = get_potential_destinations(player)
            for school in potential_schools[:3]:
                st.markdown(f"• {school}")
        else:
            st.info("Select a target school above to see fit analysis")

            # Show general destination predictions
            st.markdown("**Likely Destination Tier:**")
            stars = player.get('stars', 3) or 3
            if stars >= 4:
                st.markdown("🏆 **Power 4 / Top 25**")
            elif stars >= 3:
                st.markdown("📈 **Power 4 / Strong G5**")
            else:
                st.markdown("🎯 **G5 / FCS**")


def get_potential_destinations(player: pd.Series) -> list:
    """Get potential destination schools based on player profile."""
    stars = player.get('stars', 3) or 3
    position = player.get('position', 'ATH')
    origin = player.get('origin_school', '')

    # Position-specific schools known for that position
    position_schools = {
        "QB": ["LSU", "Alabama", "Ohio State", "Georgia", "Oregon"],
        "WR": ["USC", "Ohio State", "Alabama", "Texas", "LSU"],
        "RB": ["Alabama", "Georgia", "Texas", "Penn State", "Wisconsin"],
        "OT": ["Alabama", "Notre Dame", "Ohio State", "Michigan", "Georgia"],
        "EDGE": ["Alabama", "Georgia", "Ohio State", "Michigan", "Texas"],
        "CB": ["Alabama", "LSU", "Florida", "Ohio State", "Georgia"],
        "LB": ["Alabama", "Georgia", "Penn State", "Ohio State", "Clemson"],
    }

    base_schools = position_schools.get(position, ["Alabama", "Ohio State", "Georgia", "Texas", "Oregon"])

    # Filter by star rating
    if stars >= 4:
        return base_schools[:5]
    elif stars >= 3:
        # Mix of P4 and strong G5
        return base_schools[:3] + ["Memphis", "Boise State"]
    else:
        return ["Memphis", "Boise State", "UCF", "SMU", "Tulane"]


# =============================================================================
# Tab 3: Portal Fit Analyzer
# =============================================================================

def render_fit_analyzer_tab():
    """Render the portal fit analyzer tab."""
    st.markdown("### Analyze Portal Fit")
    st.markdown("_Select a portal player and target school to see detailed fit analysis_")

    # Get selected season for context
    selected_season = get_selected_season()
    portal_year = selected_season + 1

    portal_df = get_portal_data(year=portal_year, enrich_nil=True)

    # Filter to available players
    available_players = portal_df[portal_df["status"] == "Entered"]["name"].tolist()
    if not available_players:
        available_players = portal_df["name"].tolist()

    col1, col2 = st.columns(2)

    with col1:
        selected_player = st.selectbox(
            "Portal Player",
            options=available_players[:500],  # Limit for performance
            key="fit_player"
        )

    with col2:
        target_school = st.selectbox(
            "Target School",
            options=get_school_list(),
            key="fit_school"
        )

    if st.button("🎯 Analyze Fit", type="primary", use_container_width=True):
        render_fit_analysis(selected_player, target_school, portal_df, portal_year)


def calculate_detailed_fit(player: pd.Series, target_school: str, portal_df: pd.DataFrame, year: int) -> dict:
    """Calculate detailed fit breakdown using real factors."""

    # Get target school info
    team_df = get_team_rankings(year=year)
    target_info = team_df[team_df["name"].str.contains(target_school, case=False, na=False)]

    target_tier = 3
    target_rank = 50
    if not target_info.empty:
        target_rank = target_info.iloc[0].get("overall_rank", 50)
        if pd.notna(target_rank):
            if target_rank <= 15:
                target_tier = 6
            elif target_rank <= 35:
                target_tier = 5
            elif target_rank <= 65:
                target_tier = 4
            else:
                target_tier = 3

    # Player attributes
    player_stars = player.get("stars", 3) or 3
    player_rating = player.get("overall_rating", 0.8) or 0.8
    if player_rating > 1:
        player_rating = player_rating / 100
    player_position = player.get("position", "ATH")
    player_nil = player.get("portaliq_value", 100000) or 100000
    origin_school = player.get("origin_school", "")

    # 1. Positional Need Score
    # Check how many players at this position the school is bringing in vs losing
    incoming = portal_df[
        portal_df["destination_school"].str.contains(target_school, case=False, na=False) &
        (portal_df["status"] == "Committed")
    ]
    outgoing = portal_df[
        portal_df["origin_school"].str.contains(target_school, case=False, na=False)
    ]

    pos_incoming = len(incoming[incoming["position"] == player_position])
    pos_outgoing = len(outgoing[outgoing["position"] == player_position])
    pos_net = pos_outgoing - pos_incoming  # Positive means they need players

    # High-demand positions get boost
    pos_demand = {"QB": 0.95, "WR": 0.85, "RB": 0.75, "EDGE": 0.9, "CB": 0.85, "OT": 0.8, "LB": 0.75, "S": 0.75}.get(player_position, 0.7)

    if pos_net > 0:
        positional_need = min(0.95, pos_demand + (pos_net * 0.05))
    elif pos_net < 0:
        positional_need = max(0.4, pos_demand - (abs(pos_net) * 0.1))
    else:
        positional_need = pos_demand

    # 2. Tier Match Score
    # Players from similar or higher tiers fit better at top programs
    player_tier = player.get("school_tier", 3) or 3

    if target_tier >= 5:  # Elite program
        if player_stars >= 4:
            tier_match = 0.9
        elif player_stars >= 3 and player_rating >= 0.85:
            tier_match = 0.8
        else:
            tier_match = 0.6
    elif target_tier >= 4:  # Good program
        if player_stars >= 4:
            tier_match = 0.95
        elif player_stars >= 3:
            tier_match = 0.85
        else:
            tier_match = 0.7
    else:  # Mid-tier program
        tier_match = 0.85 if player_stars <= 3 else 0.75

    # 3. NIL Budget Fit
    # Estimate if player's NIL fits school's typical budget
    if not incoming.empty:
        avg_incoming_nil = incoming["portaliq_value"].mean()
        max_incoming_nil = incoming["portaliq_value"].max()
    else:
        # Estimate based on school tier
        avg_incoming_nil = {6: 300000, 5: 200000, 4: 120000, 3: 70000, 2: 40000}.get(target_tier, 80000)
        max_incoming_nil = avg_incoming_nil * 3

    if player_nil <= avg_incoming_nil * 1.2:
        nil_fit = 0.9
    elif player_nil <= avg_incoming_nil * 2:
        nil_fit = 0.75
    elif player_nil <= max_incoming_nil:
        nil_fit = 0.6
    else:
        nil_fit = 0.4  # May be too expensive

    # 4. Production Upgrade Score
    # Based on player's rating vs typical incoming transfers
    if not incoming.empty:
        avg_incoming_rating = incoming["overall_rating"].mean()
        if pd.isna(avg_incoming_rating):
            avg_incoming_rating = 0.8
    else:
        avg_incoming_rating = 0.8

    if player_rating > avg_incoming_rating:
        production_upgrade = min(0.95, 0.7 + (player_rating - avg_incoming_rating) * 2)
    else:
        production_upgrade = max(0.5, 0.7 - (avg_incoming_rating - player_rating) * 1.5)

    # 5. Geographic Proximity (simplified - based on common transfer patterns)
    # Schools in same region tend to attract similar players
    geo_score = 0.7  # Default
    if origin_school:
        origin_lower = str(origin_school).lower()
        target_lower = target_school.lower()

        # Same conference region bonus
        sec_schools = ["alabama", "georgia", "florida", "lsu", "tennessee", "auburn", "ole miss", "texas a&m", "kentucky", "arkansas", "missouri", "vanderbilt", "south carolina", "mississippi state"]
        big10_schools = ["ohio state", "michigan", "penn state", "wisconsin", "iowa", "nebraska", "minnesota", "illinois", "indiana", "purdue", "northwestern", "maryland", "rutgers"]
        big12_schools = ["texas", "oklahoma", "baylor", "tcu", "texas tech", "kansas", "kansas state", "iowa state", "west virginia", "oklahoma state", "cincinnati", "ucf", "houston", "byu"]

        for conf_schools in [sec_schools, big10_schools, big12_schools]:
            origin_in = any(s in origin_lower for s in conf_schools)
            target_in = any(s in target_lower for s in conf_schools)
            if origin_in and target_in:
                geo_score = 0.85
                break

    # 6. Experience/Development Fit
    class_year = player.get("class_year", "")
    if "grad" in str(class_year).lower() or "senior" in str(class_year).lower():
        # Graduate transfers provide immediate impact but less development
        experience_fit = 0.85 if target_tier >= 4 else 0.75
    elif "junior" in str(class_year).lower():
        experience_fit = 0.9  # Ideal - experience + eligibility
    else:
        experience_fit = 0.75  # Younger players may need development

    return {
        "Positional Need": round(positional_need, 2),
        "Tier Match": round(tier_match, 2),
        "NIL Budget Fit": round(nil_fit, 2),
        "Production Upgrade": round(production_upgrade, 2),
        "Geographic Fit": round(geo_score, 2),
        "Development Fit": round(experience_fit, 2),
    }


def render_fit_analysis(player_name: str, target_school: str, portal_df: pd.DataFrame, year: int):
    """Render detailed fit analysis."""
    player = portal_df[portal_df["name"] == player_name].iloc[0]

    st.divider()
    st.markdown(f"## Fit Analysis: {player_name} → {target_school}")

    # Calculate real fit breakdown
    fit_breakdown = calculate_detailed_fit(player, target_school, portal_df, year)
    overall_fit = np.mean(list(fit_breakdown.values()))

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Overall Fit Score",
            f"{overall_fit*100:.0f}%",
            delta="Strong fit" if overall_fit >= 0.8 else "Good fit" if overall_fit >= 0.7 else "Moderate fit"
        )

    with col2:
        grade = "A" if overall_fit >= 0.85 else "A-" if overall_fit >= 0.8 else "B+" if overall_fit >= 0.75 else "B" if overall_fit >= 0.7 else "B-" if overall_fit >= 0.65 else "C+"
        st.metric("Fit Grade", grade)

    with col3:
        # Project NIL at new school based on tier
        team_df = get_team_rankings(year=year)
        target_info = team_df[team_df["name"].str.contains(target_school, case=False, na=False)]
        tier_mult = 1.0
        if not target_info.empty:
            rank = target_info.iloc[0].get("overall_rank", 50)
            if pd.notna(rank) and rank <= 15:
                tier_mult = 1.3
            elif pd.notna(rank) and rank <= 35:
                tier_mult = 1.15

        current_nil = player.get("portaliq_value", 100000) or 100000
        projected_nil = current_nil * tier_mult
        st.metric("Projected NIL", format_currency(projected_nil), delta=f"{(tier_mult-1)*100:+.0f}% at {target_school}" if tier_mult != 1.0 else None)

    with col4:
        # Playing time projection based on fit
        if overall_fit >= 0.8 and fit_breakdown.get("Positional Need", 0) >= 0.8:
            playing_time = "Day 1 Starter"
        elif overall_fit >= 0.7:
            playing_time = "Starter"
        elif overall_fit >= 0.6:
            playing_time = "Rotation"
        else:
            playing_time = "Depth"
        st.metric("Projected Role", playing_time)

    st.divider()

    # Player info card
    col1, col2 = st.columns([1, 2])

    with col1:
        stars_display = '⭐' * int(player['stars']) if pd.notna(player.get('stars')) and player.get('stars', 0) > 0 else 'Unknown'
        headshot_html = get_player_headshot_html(player)
        st.markdown(f"""
        <div style="background: {COLORS['bg_medium']}; padding: 20px; border-radius: 10px;">
            {headshot_html}
            <h3 style="color: {COLORS['primary']}; text-align: center;">{player['name']}</h3>
            <p><strong>Position:</strong> {player.get('position', 'N/A')}</p>
            <p><strong>From:</strong> {player.get('origin_school', 'Unknown')}</p>
            <p><strong>Stars:</strong> {stars_display}</p>
            <p><strong>Current NIL:</strong> {format_currency(player.get('portaliq_value', 0))}</p>
            <p><strong>Status:</strong> {player.get('status', 'Unknown')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### Fit Breakdown")
        fig = create_fit_breakdown_chart(fit_breakdown)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Detailed breakdown with explanations
    st.markdown("### Factor Analysis")

    col1, col2 = st.columns(2)

    sorted_factors = sorted(fit_breakdown.items(), key=lambda x: x[1], reverse=True)

    with col1:
        st.markdown("#### ✅ Strengths")
        for factor, score in sorted_factors:
            if score >= 0.75:
                explanation = get_factor_explanation(factor, score, player, target_school)
                color = COLORS["primary"]
                st.markdown(f"""
                <div style="background: {color}22; padding: 10px; border-radius: 6px; margin: 5px 0; border-left: 3px solid {color};">
                    <strong style="color: {color};">{factor}: {score*100:.0f}%</strong>
                    <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 5px 0 0 0;">{explanation}</p>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### ⚠️ Areas to Consider")
        for factor, score in sorted_factors:
            if score < 0.75:
                explanation = get_factor_explanation(factor, score, player, target_school)
                color = COLORS["risk_moderate"] if score >= 0.6 else COLORS["risk_high"]
                st.markdown(f"""
                <div style="background: {color}22; padding: 10px; border-radius: 6px; margin: 5px 0; border-left: 3px solid {color};">
                    <strong style="color: {color};">{factor}: {score*100:.0f}%</strong>
                    <p style="color: {COLORS['text_secondary']}; font-size: 0.85rem; margin: 5px 0 0 0;">{explanation}</p>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Value analysis
    st.markdown("### 💰 Value Assessment")

    col1, col2, col3 = st.columns(3)

    current_nil = player.get("portaliq_value", 100000) or 100000
    value_per_fit = (overall_fit * 100) / (current_nil / 100000)

    with col1:
        st.metric(
            "Value Score",
            f"{value_per_fit:.2f}x",
            delta="Great value" if value_per_fit >= 1.5 else "Good value" if value_per_fit >= 1.0 else "Premium price"
        )

    with col2:
        # ROI estimate
        expected_wins = overall_fit * {"QB": 1.5, "EDGE": 0.8, "WR": 0.5, "CB": 0.6, "RB": 0.4}.get(player.get("position", ""), 0.4)
        cost_per_win = current_nil / expected_wins if expected_wins > 0 else 0
        st.metric("Est. Cost per Win", format_currency(cost_per_win) if cost_per_win > 0 else "N/A")

    with col3:
        # Risk assessment
        confidence = player.get("confidence", "medium")
        risk = "Low" if confidence == "actual" else "Medium" if confidence in ["high", "medium"] else "Higher"
        st.metric("Valuation Risk", risk)


def get_factor_explanation(factor: str, score: float, player: pd.Series, target_school: str) -> str:
    """Get explanation text for a fit factor."""
    explanations = {
        "Positional Need": {
            "high": f"{target_school} has a need at {player.get('position', 'this position')} based on recent portal activity.",
            "medium": f"{player.get('position', 'This position')} is moderately needed at {target_school}.",
            "low": f"{target_school} may be deep at {player.get('position', 'this position')} already."
        },
        "Tier Match": {
            "high": f"Player's talent profile aligns well with {target_school}'s competitive level.",
            "medium": f"Reasonable talent fit, may need to prove themselves at this level.",
            "low": f"Talent level may be a mismatch for {target_school}'s expectations."
        },
        "NIL Budget Fit": {
            "high": f"Player's expected NIL fits comfortably within {target_school}'s typical range.",
            "medium": f"NIL may be at the higher end of what {target_school} typically offers.",
            "low": f"Player's NIL expectations may exceed {target_school}'s typical budget."
        },
        "Production Upgrade": {
            "high": f"Would be an immediate upgrade based on production metrics and rating.",
            "medium": f"Production level is consistent with current roster quality.",
            "low": f"May not represent a clear upgrade over current options."
        },
        "Geographic Fit": {
            "high": f"Strong regional connection, common transfer corridor.",
            "medium": f"Neutral geographic fit.",
            "low": f"Distance may be a factor in player's decision."
        },
        "Development Fit": {
            "high": f"Ideal experience level for {target_school}'s needs.",
            "medium": f"Experience level works for the program.",
            "low": f"May require more development time than ideal."
        },
    }

    level = "high" if score >= 0.75 else "medium" if score >= 0.6 else "low"
    return explanations.get(factor, {}).get(level, "Analysis not available.")


# =============================================================================
# Tab 4: Team Needs Analysis
# =============================================================================

def render_team_needs_tab():
    """Render the team needs analysis tab."""
    st.markdown("### 📋 Team Needs Analysis")
    st.markdown("_Analyze roster gaps and identify positions of need for any school_")

    # Get selected season
    selected_season = get_selected_season()
    portal_year = selected_season + 1

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_school = st.selectbox(
            "Select School to Analyze",
            options=get_school_list(),
            key="needs_school"
        )

    with col2:
        st.write("")
        analyze_btn = st.button("🔍 Analyze Roster Needs", type="primary", use_container_width=True)

    if selected_school and analyze_btn:
        render_team_needs_results(selected_school, portal_year)


def render_team_needs_results(school: str, year: int):
    """Render team needs analysis results."""
    st.divider()

    # Get portal data for analysis
    portal_df = get_portal_data(year=year, enrich_nil=True)

    if portal_df.empty:
        st.warning("No portal data available for analysis.")
        return

    # Find incoming and outgoing transfers
    incoming = portal_df[
        portal_df["destination_school"].str.contains(school, case=False, na=False) &
        (portal_df["status"] == "Committed")
    ].copy()

    outgoing = portal_df[
        portal_df["origin_school"].str.contains(school, case=False, na=False)
    ].copy()

    st.markdown(f"## {school} - Roster Needs Analysis")

    # Define position groups and ideal roster counts
    POSITION_GROUPS = {
        "Quarterback": {"positions": ["QB"], "ideal_count": 3, "scholarship_weight": 0.9},
        "Running Back": {"positions": ["RB"], "ideal_count": 4, "scholarship_weight": 0.8},
        "Wide Receiver": {"positions": ["WR"], "ideal_count": 8, "scholarship_weight": 0.85},
        "Tight End": {"positions": ["TE"], "ideal_count": 3, "scholarship_weight": 0.75},
        "Offensive Line": {"positions": ["OT", "OG", "C", "OL", "IOL"], "ideal_count": 15, "scholarship_weight": 0.8},
        "Defensive Line": {"positions": ["DT", "DE", "DL", "NT"], "ideal_count": 8, "scholarship_weight": 0.8},
        "Edge Rusher": {"positions": ["EDGE"], "ideal_count": 4, "scholarship_weight": 0.9},
        "Linebacker": {"positions": ["LB", "ILB", "OLB"], "ideal_count": 6, "scholarship_weight": 0.8},
        "Cornerback": {"positions": ["CB"], "ideal_count": 6, "scholarship_weight": 0.85},
        "Safety": {"positions": ["S", "FS", "SS"], "ideal_count": 4, "scholarship_weight": 0.8},
        "Special Teams": {"positions": ["K", "P", "LS"], "ideal_count": 3, "scholarship_weight": 0.3},
    }

    # Calculate needs by position group
    needs_analysis = []

    for group_name, group_data in POSITION_GROUPS.items():
        positions = group_data["positions"]
        ideal = group_data["ideal_count"]
        weight = group_data["scholarship_weight"]

        # Count incoming and outgoing
        inc_count = len(incoming[incoming["position"].isin(positions)]) if not incoming.empty else 0
        out_count = len(outgoing[outgoing["position"].isin(positions)]) if not outgoing.empty else 0

        # Calculate NIL values
        inc_nil = incoming[incoming["position"].isin(positions)]["portaliq_value"].sum() if not incoming.empty else 0
        out_nil = outgoing[outgoing["position"].isin(positions)]["portaliq_value"].sum() if not outgoing.empty else 0

        # Calculate star rating averages
        inc_stars = incoming[incoming["position"].isin(positions)]["stars"].mean() if not incoming.empty and len(incoming[incoming["position"].isin(positions)]) > 0 else 0
        out_stars = outgoing[outgoing["position"].isin(positions)]["stars"].mean() if not outgoing.empty and len(outgoing[outgoing["position"].isin(positions)]) > 0 else 0

        # Net movement
        net = inc_count - out_count
        net_nil = inc_nil - out_nil

        # Calculate need score (higher = more need)
        need_score = 0
        if out_count > inc_count:
            need_score += (out_count - inc_count) * 2  # Losing players
        if out_stars > inc_stars and out_count > 0:
            need_score += (out_stars - inc_stars) * 1.5  # Losing talent
        need_score *= weight  # Apply position importance

        # Determine need level
        if need_score >= 4:
            need_level = "Critical"
            need_color = COLORS["risk_critical"]
        elif need_score >= 2:
            need_level = "High"
            need_color = COLORS["risk_high"]
        elif need_score >= 1:
            need_level = "Moderate"
            need_color = COLORS["risk_moderate"]
        else:
            need_level = "Stable"
            need_color = COLORS["primary"]

        needs_analysis.append({
            "Group": group_name,
            "Incoming": inc_count,
            "Outgoing": out_count,
            "Net": net,
            "Avg Stars In": inc_stars,
            "Avg Stars Out": out_stars,
            "NIL In": inc_nil,
            "NIL Out": out_nil,
            "Net NIL": net_nil,
            "Need Score": need_score,
            "Need Level": need_level,
            "Need Color": need_color,
        })

    # Sort by need score
    needs_analysis.sort(key=lambda x: x["Need Score"], reverse=True)

    # Display summary cards
    st.markdown("### 🚨 Priority Needs")

    critical_needs = [n for n in needs_analysis if n["Need Level"] == "Critical"]
    high_needs = [n for n in needs_analysis if n["Need Level"] == "High"]

    if critical_needs or high_needs:
        priority_needs = critical_needs + high_needs

        cols = st.columns(min(len(priority_needs), 4))
        for idx, need in enumerate(priority_needs[:4]):
            with cols[idx % 4]:
                st.markdown(f"""
                <div style="background: {need['Need Color']}22; padding: 15px; border-radius: 10px;
                            border-left: 4px solid {need['Need Color']};">
                    <h4 style="color: {need['Need Color']}; margin: 0;">{need['Group']}</h4>
                    <p style="color: {COLORS['text_secondary']}; margin: 5px 0;">
                        <strong>{need['Need Level']}</strong> - Lost {need['Outgoing']}, Gained {need['Incoming']}
                    </p>
                    <p style="color: {COLORS['text_muted']}; font-size: 0.85rem; margin: 0;">
                        Net NIL: {format_currency(need['Net NIL'])}
                    </p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("No critical or high priority needs identified. Roster appears balanced.")

    st.divider()

    # Full needs breakdown table
    st.markdown("### 📊 Position Group Breakdown")

    # Prepare display dataframe
    display_data = []
    for need in needs_analysis:
        display_data.append({
            "Position Group": need["Group"],
            "Need Level": need["Need Level"],
            "Incoming": need["Incoming"],
            "Outgoing": need["Outgoing"],
            "Net": need["Net"],
            "⭐ In": f"{need['Avg Stars In']:.1f}" if need['Avg Stars In'] > 0 else "—",
            "⭐ Out": f"{need['Avg Stars Out']:.1f}" if need['Avg Stars Out'] > 0 else "—",
            "NIL Impact": format_currency(need["Net NIL"]),
        })

    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    # Portal targets recommendation
    st.markdown("### 🎯 Recommended Portal Targets")
    st.markdown("_Available portal players that match your needs_")

    # Get available portal players
    available = portal_df[portal_df["status"] == "Entered"].copy()

    if not available.empty:
        # Find top 3 need areas
        top_needs = [n for n in needs_analysis if n["Need Level"] in ["Critical", "High", "Moderate"]][:3]

        for need in top_needs:
            positions = POSITION_GROUPS[need["Group"]]["positions"]
            matches = available[available["position"].isin(positions)]

            if not matches.empty:
                st.markdown(f"#### {need['Group']} ({need['Need Level']} Need)")

                # Sort by portal IQ value and stars
                matches = matches.sort_values(["stars", "portaliq_value"], ascending=[False, False])

                display_matches = matches[["name", "position", "origin_school", "stars", "portaliq_value"]].head(5).copy()
                display_matches["stars"] = display_matches["stars"].apply(
                    lambda x: f"{'⭐' * int(x)}" if pd.notna(x) and x > 0 else "—"
                )
                display_matches["portaliq_value"] = display_matches["portaliq_value"].apply(format_currency)
                display_matches.columns = ["Player", "Position", "From", "Stars", "Est. NIL"]

                st.dataframe(display_matches, use_container_width=True, hide_index=True)
    else:
        st.info("No available portal players found for recommendations.")

    st.divider()

    # Needs chart visualization
    st.markdown("### 📈 Needs Visualization")

    # Bar chart of net changes
    fig = go.Figure()

    groups = [n["Group"] for n in needs_analysis]
    net_values = [n["Net"] for n in needs_analysis]
    colors = [COLORS["primary"] if v >= 0 else COLORS["risk_high"] for v in net_values]

    fig.add_trace(go.Bar(
        x=groups,
        y=net_values,
        marker_color=colors,
        text=net_values,
        textposition="outside",
    ))

    fig.update_layout(
        title="Net Player Movement by Position Group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text_secondary"]),
        xaxis=dict(tickangle=-45),
        yaxis=dict(gridcolor=COLORS["bg_light"], title="Net Players (In - Out)"),
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Export needs analysis
    st.divider()
    st.markdown("### 📤 Export Analysis")

    if st.button("📋 Export Needs Analysis", use_container_width=True):
        export_df = pd.DataFrame(needs_analysis)
        export_df = export_df.drop(columns=["Need Color"])
        csv = export_df.to_csv(index=False)

        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"{school.replace(' ', '_')}_needs_analysis.csv",
            mime="text/csv",
        )


# =============================================================================
# Tab 5: Watchlist
# =============================================================================

def render_watchlist_tab():
    """Render the player watchlist tab."""
    st.markdown("### ⭐ Player Watchlist")
    st.markdown("_Track your favorite portal players and add notes_")

    watchlist = get_watchlist()

    if not watchlist:
        st.info("Your watchlist is empty. Add players from the Portal Player Search tab by clicking the ⭐ button.")
        st.markdown(f"""
        <div style="background: {COLORS['bg_medium']}; padding: 30px; border-radius: 12px; text-align: center; margin-top: 20px;">
            <p style="font-size: 4rem; margin: 0;">⭐</p>
            <h3 style="color: {COLORS['primary']};">Start Building Your Watchlist</h3>
            <p style="color: {COLORS['text_secondary']};">
                Go to the <strong>Portal Player Search</strong> tab to find players and add them to your watchlist.
                Track their status, NIL values, and add your own notes.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Watchlist controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"**{len(watchlist)} players** in your watchlist")

    with col2:
        # Filter by position
        positions = list(set([p.get("position", "") for p in watchlist.values()]))
        filter_pos = st.selectbox("Filter by Position", ["All"] + positions, key="watchlist_pos_filter")

    with col3:
        # Sort options
        sort_by = st.selectbox("Sort By", ["Date Added", "NIL Value", "Stars", "Name"], key="watchlist_sort")

    st.divider()

    # Apply filters
    filtered_watchlist = watchlist.copy()
    if filter_pos != "All":
        filtered_watchlist = {k: v for k, v in filtered_watchlist.items() if v.get("position") == filter_pos}

    # Sort watchlist
    sort_key_map = {
        "Date Added": lambda x: x[1].get("added_date", ""),
        "NIL Value": lambda x: x[1].get("portaliq_value", 0),
        "Stars": lambda x: x[1].get("stars", 0),
        "Name": lambda x: x[1].get("name", ""),
    }
    sorted_items = sorted(filtered_watchlist.items(), key=sort_key_map.get(sort_by, sort_key_map["Date Added"]), reverse=(sort_by != "Name"))

    # Display watchlist cards
    for player_id, player in sorted_items:
        render_watchlist_card(player_id, player)

    st.divider()

    # Export watchlist
    st.markdown("### 📤 Export Watchlist")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📋 Export to CSV", use_container_width=True):
            export_watchlist_csv()

    with col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            if st.session_state.get("confirm_clear_watchlist"):
                st.session_state.watchlist = {}
                st.session_state.watchlist_notes = {}
                st.session_state.confirm_clear_watchlist = False
                st.rerun()
            else:
                st.session_state.confirm_clear_watchlist = True
                st.warning("Click 'Clear All' again to confirm.")


def render_watchlist_card(player_id: str, player: dict):
    """Render a single watchlist player card."""
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

        with col1:
            stars = int(player.get("stars", 0)) if player.get("stars") else 0
            stars_display = "⭐" * stars if stars > 0 else "—"
            status = player.get("status", "Unknown")
            status_color = COLORS["primary"] if status == "Committed" else COLORS["risk_moderate"] if status == "Entered" else COLORS["text_muted"]

            st.markdown(f"""
            <div style="padding: 5px 0;">
                <strong style="color: {COLORS['text_primary']}; font-size: 1.1rem;">{player.get('name', 'Unknown')}</strong>
                <span style="color: {COLORS['text_muted']};">{stars_display}</span>
                <br>
                <span style="color: {COLORS['text_secondary']};">{player.get('position', 'ATH')} | {player.get('origin_school', 'Unknown')}</span>
                <br>
                <span style="color: {status_color}; font-size: 0.85rem;">● {status}</span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            nil_val = player.get("portaliq_value", 0) or 0
            st.markdown(f"""
            <div style="text-align: center; padding: 10px 0;">
                <span style="color: {COLORS['text_muted']}; font-size: 0.8rem;">Portal IQ Est.</span><br>
                <strong style="color: {COLORS['primary']}; font-size: 1.1rem;">{format_currency(nil_val)}</strong>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            destination = player.get("destination_school", "")
            if destination and str(destination) != "nan":
                st.markdown(f"""
                <div style="text-align: center; padding: 10px 0;">
                    <span style="color: {COLORS['text_muted']}; font-size: 0.8rem;">Destination</span><br>
                    <strong style="color: {COLORS['text_primary']};">{destination}</strong>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px 0;">
                    <span style="color: {COLORS['text_muted']}; font-size: 0.8rem;">Destination</span><br>
                    <span style="color: {COLORS['text_muted']};">TBD</span>
                </div>
                """, unsafe_allow_html=True)

        with col4:
            added = player.get("added_date", "Unknown")
            st.markdown(f"""
            <div style="text-align: center; padding: 10px 0;">
                <span style="color: {COLORS['text_muted']}; font-size: 0.8rem;">Added</span><br>
                <span style="color: {COLORS['text_secondary']}; font-size: 0.85rem;">{added}</span>
            </div>
            """, unsafe_allow_html=True)

        with col5:
            if st.button("🗑️", key=f"remove_{player_id}", help="Remove from watchlist"):
                remove_from_watchlist(player_id)
                st.rerun()

        # Note section (collapsible)
        with st.expander("📝 Add Note", expanded=False):
            current_note = get_watchlist_note(player_id)
            new_note = st.text_area(
                "Notes",
                value=current_note,
                key=f"note_{player_id}",
                placeholder="Add your notes about this player...",
                label_visibility="collapsed"
            )
            if new_note != current_note:
                update_watchlist_note(player_id, new_note)

        st.markdown(f"<hr style='border-color: {COLORS['bg_light']}; margin: 10px 0;'>", unsafe_allow_html=True)


def export_watchlist_csv():
    """Export watchlist to CSV and trigger download."""
    watchlist = get_watchlist()

    if not watchlist:
        st.warning("Watchlist is empty.")
        return

    # Convert to DataFrame
    rows = []
    for player_id, player in watchlist.items():
        row = {
            "Name": player.get("name", ""),
            "Position": player.get("position", ""),
            "Origin School": player.get("origin_school", ""),
            "Destination": player.get("destination_school", "TBD"),
            "Stars": player.get("stars", 0),
            "Portal IQ Value": player.get("portaliq_value", 0),
            "On3 Value": player.get("on3_nil_value", 0),
            "Status": player.get("status", ""),
            "Rating": player.get("overall_rating", 0),
            "Height": player.get("height_display", ""),
            "Weight": player.get("weight", 0),
            "Added Date": player.get("added_date", ""),
            "Notes": get_watchlist_note(player_id),
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Convert to CSV
    csv = df.to_csv(index=False)

    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"portal_iq_watchlist_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    main()
else:
    main()
