"""
Portal Intelligence Page

Transfer portal analytics for college football.
- Roster Flight Risk analysis
- Portal Player Search and filtering
- Portal Fit Analyzer
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
    apply_custom_css, COLORS, get_risk_color, get_risk_color_by_value,
    format_currency, render_risk_badge
)
from utils.api_client import get_api_client
from utils.data_loader import (
    load_sample_data, get_school_list, get_positions, get_conferences,
    get_roster_for_school, get_portal_players as get_portal_data,
    get_portal_statuses
)

# Page config
st.set_page_config(
    page_title="Portal Intelligence | Portal IQ",
    page_icon="🔄",
    layout="wide",
)

apply_custom_css()


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
    # Header
    st.markdown("""
    <h1 style="color: #00C853;">🔄 Portal Intelligence</h1>
    <p style="color: #e6edf3; font-size: 1.1rem;">
        Transfer portal analytics and flight risk monitoring
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Roster Flight Risk",
        "🔍 Portal Player Search",
        "🎯 Portal Fit Analyzer"
    ])

    with tab1:
        render_flight_risk_tab()

    with tab2:
        render_portal_search_tab()

    with tab3:
        render_fit_analyzer_tab()


# =============================================================================
# Tab 1: Roster Flight Risk
# =============================================================================

def render_flight_risk_tab():
    """Render the roster flight risk analysis tab."""
    st.markdown("### Select School for Flight Risk Analysis")

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_school = st.selectbox(
            "School",
            options=get_school_list(),
            key="flight_risk_school"
        )

    with col2:
        st.write("")
        analyze_btn = st.button("🔍 Analyze Roster", type="primary", use_container_width=True)

    if selected_school and analyze_btn:
        with st.spinner("Analyzing roster flight risk..."):
            render_flight_risk_results(selected_school)


def render_flight_risk_results(school: str):
    """Render flight risk analysis results."""
    roster_df = get_school_roster(school)

    st.divider()

    # Summary metrics
    st.markdown(f"## {school} - Flight Risk Analysis")

    high_risk = roster_df[roster_df["flight_risk"] >= 0.5]
    critical_risk = roster_df[roster_df["flight_risk"] >= 0.7]

    # Calculate estimated production/wins at risk
    total_risk_value = high_risk["nil_value"].sum()
    estimated_wins_at_risk = len(critical_risk) * 0.3 + len(high_risk[high_risk["flight_risk"] < 0.7]) * 0.15

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Roster Size",
            len(roster_df),
            delta=f"{len(roster_df[roster_df['is_starter']])} starters"
        )

    with col2:
        st.metric(
            "High Risk Players",
            len(high_risk),
            delta=f"{len(critical_risk)} critical",
            delta_color="inverse"
        )

    with col3:
        st.metric(
            "Est. Wins at Risk",
            f"{estimated_wins_at_risk:.1f}",
            delta="If players transfer"
        )

    with col4:
        st.metric(
            "Retention Budget Needed",
            format_currency(total_risk_value * 0.3),
            delta="To secure high-risk players"
        )

    st.divider()

    # Critical retention targets
    if not critical_risk.empty:
        st.markdown("### 🚨 Critical Retention Targets")
        st.markdown("_These players have >70% flight risk and should be prioritized for retention_")

        for _, player in critical_risk.iterrows():
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.markdown(f"**{player['name']}** - {player['position']}")
            with col2:
                st.markdown(f"Risk: {player['flight_risk']*100:.0f}%")
            with col3:
                st.markdown(f"NIL: {format_currency(player['nil_value'])}")
            with col4:
                st.markdown(f"Rating: {player['overall_rating']:.2f}")

        st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Team Risk Overview")
        avg_risk = roster_df["flight_risk"].mean()
        fig = create_risk_gauge(avg_risk, "Average Team Flight Risk")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Risk by Position")
        fig = create_position_risk_chart(roster_df)
        st.plotly_chart(fig, use_container_width=True)

    # Full roster table
    st.markdown("### Full Roster Flight Risk")

    # Prepare display dataframe
    display_df = roster_df[["name", "position", "class_year", "flight_risk", "nil_value", "overall_rating", "is_starter"]].copy()
    display_df["flight_risk_pct"] = display_df["flight_risk"].apply(lambda x: f"{x*100:.0f}%")
    display_df["nil_value_fmt"] = display_df["nil_value"].apply(format_currency)
    display_df["risk_level"] = display_df["flight_risk"].apply(
        lambda x: "Critical" if x >= 0.7 else "High" if x >= 0.5 else "Moderate" if x >= 0.3 else "Low"
    )

    # Sort by flight risk
    display_df = display_df.sort_values("flight_risk", ascending=False)

    # Display with color coding
    display_cols = ["name", "position", "class_year", "risk_level", "flight_risk_pct", "nil_value_fmt", "overall_rating"]
    display_df_show = display_df[display_cols].copy()
    display_df_show.columns = ["Player", "Position", "Class", "Risk Level", "Risk %", "NIL Value", "Rating"]

    st.dataframe(
        display_df_show,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Risk Level": st.column_config.TextColumn(
                "Risk Level",
                help="Flight risk classification"
            ),
            "Risk %": st.column_config.TextColumn(
                "Risk %",
                help="Probability of entering portal"
            ),
        }
    )


# =============================================================================
# Tab 2: Portal Player Search
# =============================================================================

def render_portal_search_tab():
    """Render the portal player search tab."""
    st.markdown("### Search & Filter Portal Players")

    # Filters - Row 1
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        year_filter = st.selectbox(
            "Portal Year",
            options=[2026, 2025, 2024],
            index=0,
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
            min_value=2,
            max_value=5,
            value=(2, 5),
            key="portal_stars_filter"
        )

    # Row 2
    col1, col2 = st.columns(2)

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

    st.divider()

    # Get portal players for selected year
    portal_df = get_portal_data(year=year_filter)

    # Apply filters
    filtered_df = portal_df.copy()

    if status_filter:
        filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]

    if position_filter:
        filtered_df = filtered_df[filtered_df["position"].isin(position_filter)]

    if stars_filter:
        filtered_df = filtered_df[
            (filtered_df["stars"] >= stars_filter[0]) &
            (filtered_df["stars"] <= stars_filter[1])
        ]

    # Add fit scores if target school selected
    if target_school != "None":
        # Calculate demo fit scores
        np.random.seed(hash(target_school) % 1000)
        filtered_df["fit_score"] = np.random.uniform(0.6, 0.95, len(filtered_df)).round(2)
        filtered_df["value_score"] = (filtered_df["fit_score"] * 100 / (filtered_df["nil_value"] / 100000)).round(2)

    # Display results
    st.markdown(f"### Portal Players ({len(filtered_df)} found)")

    if not filtered_df.empty:
        # Prepare display
        display_cols = ["name", "position", "origin_school", "stars", "overall_rating", "nil_value"]

        if target_school != "None":
            display_cols.extend(["fit_score", "value_score"])

        display_df = filtered_df[display_cols].copy()
        display_df["nil_value"] = display_df["nil_value"].apply(format_currency)

        col_names = ["Player", "Position", "Origin School", "Stars", "Rating", "Est. NIL"]
        if target_school != "None":
            col_names.extend(["Fit Score", "Value Score"])

        display_df.columns = col_names

        # Sort options
        sort_col = st.selectbox(
            "Sort By",
            options=col_names,
            index=col_names.index("Rating") if "Rating" in col_names else 0,
            key="portal_sort"
        )

        sort_asc = st.checkbox("Ascending", value=False, key="portal_sort_asc")
        display_df = display_df.sort_values(sort_col, ascending=sort_asc)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # Show detail for selected player
        st.divider()
        st.markdown("### Player Details")

        selected_player = st.selectbox(
            "Select player for details",
            options=filtered_df["name"].tolist(),
            key="portal_detail_player"
        )

        if selected_player:
            player = filtered_df[filtered_df["name"] == selected_player].iloc[0]

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div style="background: {COLORS['bg_medium']}; padding: 20px; border-radius: 10px;">
                    <h3 style="color: {COLORS['primary']};">{player['name']}</h3>
                    <p>Position: {player['position']}</p>
                    <p>Origin: {player['origin_school']}</p>
                    <p>Stars: {'⭐' * int(player['stars']) if player.get('stars') else 'N/A'}</p>
                    <p>Rating: {player['overall_rating']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.metric("Estimated NIL Value", format_currency(player["nil_value"]))
                st.metric("Portal Entry", player.get("portal_entry_date", "Dec 2024"))

            with col3:
                if target_school != "None":
                    st.metric("Fit Score", f"{player.get('fit_score', 0.75)*100:.0f}%")
                    st.metric("Value Score", f"{player.get('value_score', 1.0):.2f}")
    else:
        st.info("No players match your filters. Try adjusting the criteria.")


# =============================================================================
# Tab 3: Portal Fit Analyzer
# =============================================================================

def render_fit_analyzer_tab():
    """Render the portal fit analyzer tab."""
    st.markdown("### Analyze Portal Fit")
    st.markdown("_Select a portal player and target school to see detailed fit analysis_")

    col1, col2 = st.columns(2)

    portal_df = get_portal_data()

    with col1:
        selected_player = st.selectbox(
            "Portal Player",
            options=portal_df["name"].tolist(),
            key="fit_player"
        )

    with col2:
        target_school = st.selectbox(
            "Target School",
            options=get_school_list(),
            key="fit_school"
        )

    if st.button("🎯 Analyze Fit", type="primary", use_container_width=True):
        render_fit_analysis(selected_player, target_school, portal_df)


def render_fit_analysis(player_name: str, target_school: str, portal_df: pd.DataFrame):
    """Render detailed fit analysis."""
    player = portal_df[portal_df["name"] == player_name].iloc[0]

    st.divider()
    st.markdown(f"## Fit Analysis: {player_name} → {target_school}")

    # Generate fit breakdown
    np.random.seed(hash(player_name + target_school) % 1000)

    fit_breakdown = {
        "Positional Need": np.random.uniform(0.6, 0.95),
        "Production Upgrade": np.random.uniform(0.5, 0.9),
        "Tier Match": np.random.uniform(0.65, 0.95),
        "NIL Budget Fit": np.random.uniform(0.5, 0.85),
        "Geographic Proximity": np.random.uniform(0.4, 0.95),
        "Scheme Fit": np.random.uniform(0.55, 0.9),
    }

    overall_fit = np.mean(list(fit_breakdown.values()))

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Overall Fit Score",
            f"{overall_fit*100:.0f}%",
            delta="Good fit" if overall_fit >= 0.7 else "Moderate fit"
        )

    with col2:
        grade = "A" if overall_fit >= 0.85 else "B+" if overall_fit >= 0.75 else "B" if overall_fit >= 0.65 else "C"
        st.metric("Fit Grade", grade)

    with col3:
        projected_nil = player["nil_value"] * (1.2 if "Alabama" in target_school or "Ohio State" in target_school else 1.0)
        st.metric("Projected NIL", format_currency(projected_nil))

    with col4:
        playing_time = "Starter" if overall_fit >= 0.7 else "Rotation" if overall_fit >= 0.5 else "Depth"
        st.metric("Projected Role", playing_time)

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Fit Breakdown")
        fig = create_fit_breakdown_chart(fit_breakdown)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### Fit Categories")

        for category, score in sorted(fit_breakdown.items(), key=lambda x: x[1], reverse=True):
            color = COLORS["primary"] if score >= 0.7 else COLORS["risk_moderate"] if score >= 0.5 else COLORS["risk_high"]
            st.markdown(f"""
            <div style="margin: 10px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: {COLORS['text_secondary']};">{category}</span>
                    <span style="color: {color}; font-weight: bold;">{score*100:.0f}%</span>
                </div>
                <div style="background: {COLORS['bg_light']}; border-radius: 5px; height: 10px;">
                    <div style="background: {color}; width: {score*100}%; height: 100%; border-radius: 5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # Strengths and Concerns
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Strengths")
        strengths = [k for k, v in fit_breakdown.items() if v >= 0.7]
        for s in strengths:
            st.markdown(f"- {s} ({fit_breakdown[s]*100:.0f}%)")
        if not strengths:
            st.markdown("- No standout strengths identified")

    with col2:
        st.markdown("### ⚠️ Concerns")
        concerns = [k for k, v in fit_breakdown.items() if v < 0.6]
        for c in concerns:
            st.markdown(f"- {c} ({fit_breakdown[c]*100:.0f}%)")
        if not concerns:
            st.markdown("- No major concerns identified")

    st.divider()

    # Comparable Transfers
    st.markdown("### Comparable Past Transfers")

    comparables = pd.DataFrame([
        {"Player": "Similar Transfer 1", "Origin": "School A", "Destination": target_school,
         "Fit Score": 0.78, "Outcome": "Started 12 games, All-Conference"},
        {"Player": "Similar Transfer 2", "Origin": "School B", "Destination": target_school,
         "Fit Score": 0.72, "Outcome": "Started 8 games, solid contributor"},
        {"Player": "Similar Transfer 3", "Origin": "School C", "Destination": "Similar School",
         "Fit Score": 0.68, "Outcome": "Rotation player, transferred again"},
    ])

    st.dataframe(comparables, use_container_width=True, hide_index=True)


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    main()
else:
    main()
