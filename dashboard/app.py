"""
Portal IQ Dashboard - Main Application

AI-Powered Transfer Portal & NIL Intelligence Platform
Multi-page Streamlit application for college football analytics.
"""

import streamlit as st
from datetime import datetime

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title="Portal IQ",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://elitesportssolutions.com/support",
        "Report a bug": "https://elitesportssolutions.com/bugs",
        "About": "Portal IQ - AI-Powered Transfer Portal & NIL Intelligence by Elite Sports Solutions"
    }
)

# Import utilities after page config
from utils.styling import apply_custom_css, COLORS
from utils.api_client import PortalIQClient
from utils.data_loader import get_database_stats, get_nil_players, get_portal_players, get_team_rankings
from utils.navigation import render_sidebar


# =============================================================================
# Custom CSS
# =============================================================================

apply_custom_css()


# =============================================================================
# Session State Initialization
# =============================================================================

if "api_client" not in st.session_state:
    st.session_state.api_client = PortalIQClient()

if "selected_school" not in st.session_state:
    st.session_state.selected_school = None

if "current_season" not in st.session_state:
    st.session_state.current_season = 2025


# =============================================================================
# Sidebar (imported from utils.navigation)
# =============================================================================


# =============================================================================
# Main Page Content
# =============================================================================

def render_main_page():
    """Render the main Portal IQ landing page."""

    # Header
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <h1 style="font-size: 3.5rem; color: #00C853; margin-bottom: 10px;">
            🏈 Portal IQ
        </h1>
        <p style="font-size: 1.5rem; color: #ccc; margin-bottom: 30px;">
            AI-Powered Transfer Portal & NIL Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Quick Stats
    st.markdown("### 📊 Platform Overview")

    stats = get_database_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Players",
            value=f"{stats.get('total_players', 12500):,}",
            delta="Updated daily"
        )

    with col2:
        st.metric(
            label="Portal Entries",
            value=f"{stats.get('portal_players', 2100):,}",
            delta=f"+{stats.get('new_portal_today', 45)} today"
        )

    with col3:
        st.metric(
            label="NIL Valuations",
            value=f"{stats.get('nil_valuations', 8500):,}",
            delta="Real-time"
        )

    with col4:
        st.metric(
            label="Models Updated",
            value=stats.get('models_updated', 'Jan 15, 2025'),
            delta="v2.3.1"
        )

    st.divider()

    # Feature Cards
    st.markdown("### 🚀 Explore Our Tools")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
                    padding: 30px; border-radius: 15px; border: 1px solid #00C853;
                    margin: 10px 0; height: 200px;">
            <h3 style="color: #00C853; margin-bottom: 15px;">💰 NIL Valuator</h3>
            <p style="color: #e6edf3;">
                Real On3 NIL valuations plus our custom algorithm. Compare players,
                analyze value breakdowns, and track market trends.
            </p>
            <p style="color: #00C853; margin-top: 20px;">→ Predict player market value</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
                    padding: 30px; border-radius: 15px; border: 1px solid #00C853;
                    margin: 10px 0; height: 200px;">
            <h3 style="color: #00C853; margin-bottom: 15px;">📈 Win Impact</h3>
            <p style="color: #e6edf3;">
                Understand how much value a player adds to their team. Win impact
                directly correlates to NIL valuation and transfer market value.
            </p>
            <p style="color: #00C853; margin-top: 20px;">→ Player value analytics</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
                    padding: 30px; border-radius: 15px; border: 1px solid #00C853;
                    margin: 10px 0; height: 200px;">
            <h3 style="color: #00C853; margin-bottom: 15px;">🔄 Portal Intelligence</h3>
            <p style="color: #e6edf3;">
                14,000+ transfer portal entries across 3 years. Track commitments,
                analyze team rankings, and find the best portal targets.
            </p>
            <p style="color: #00C853; margin-top: 20px;">→ Transfer portal analytics</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
                    padding: 30px; border-radius: 15px; border: 1px solid #00C853;
                    margin: 10px 0; height: 200px;">
            <h3 style="color: #00C853; margin-bottom: 15px;">🤖 AI Assistant</h3>
            <p style="color: #e6edf3;">
                Chat with Claude AI about players, NIL values, and portal activity.
                Get instant insights and recommendations powered by real data.
            </p>
            <p style="color: #00C853; margin-top: 20px;">→ Ask anything about the portal</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Recent Activity - Real Data
    st.markdown("### 📈 Live Data")

    col1, col2, col3 = st.columns(3)

    # Get real data
    nil_df = get_nil_players()
    portal_df = get_portal_players(year=2026)
    team_df = get_team_rankings(year=2026)

    with col1:
        st.markdown("#### 🔥 Top NIL Players")
        if not nil_df.empty:
            top_nil = nil_df.nlargest(5, "nil_value")
            for _, row in top_nil.iterrows():
                val = f"${row['nil_value']:,.0f}" if row['nil_value'] else "N/A"
                school = str(row['school'])[:15] if row.get('school') else "Unknown"
                st.markdown(f"**{row['name']}** ({row['position']}) - {val}")
        else:
            st.info("Load NIL data to see top players")

    with col2:
        st.markdown("#### 🚨 Recent Portal Activity")
        if not portal_df.empty:
            recent = portal_df[portal_df["status"] == "Entered"].head(5)
            if recent.empty:
                recent = portal_df.head(5)
            for _, row in recent.iterrows():
                stars = int(row['stars']) if row.get('stars') else 3
                school = str(row.get('origin_school', 'Unknown'))[:15]
                st.markdown(f"{'⭐' * stars} **{row['name']}** ({row['position']}) from {school}")
        else:
            st.info("Load portal data to see entries")

    with col3:
        st.markdown("#### 🏆 Top Portal Classes (2026)")
        if not team_df.empty:
            top_teams = team_df.nlargest(5, "overall_score") if "overall_score" in team_df.columns else team_df.head(5)
            for _, row in top_teams.iterrows():
                score = f"{row['overall_score']:.0f}" if row.get('overall_score') else "N/A"
                st.markdown(f"**{row['name']}** - Score: {score}")
        else:
            st.info("Load team rankings to see top classes")


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point."""
    render_sidebar()
    render_main_page()


if __name__ == "__main__":
    main()
