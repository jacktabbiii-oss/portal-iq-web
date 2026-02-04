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
from utils.navigation import render_sidebar, get_selected_season
from utils.auth import require_auth, show_user_menu, require_subscription


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

    # Header - Navy/Gold branding
    st.markdown(f"""
    <div style="text-align: center; padding: 40px 0;">
        <div style="display: inline-flex; align-items: center; gap: 15px; margin-bottom: 15px;">
            <div style="width: 70px; height: 70px; background: linear-gradient(135deg, {COLORS['primary']} 0%, #B8962E 100%);
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;
                        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.35);">
                <span style="font-size: 2rem;">🧭</span>
            </div>
            <h1 style="font-size: 3.5rem; color: #ffffff; margin: 0; font-weight: 700; letter-spacing: 2px;">
                PORTAL <span style="color: {COLORS['primary']};">IQ</span>
            </h1>
        </div>
        <p style="font-size: 1.3rem; color: {COLORS['text_secondary']}; margin-bottom: 10px;">
            AI-Powered Transfer Portal & NIL Intelligence
        </p>
        <p style="font-size: 0.9rem; color: {COLORS['primary']}; letter-spacing: 3px; text-transform: uppercase;">
            Elite Sports Solutions
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

    # Feature Cards - Navy/Gold theme with clickable navigation
    st.markdown(f"### <span style='color: {COLORS['primary']};'>🚀</span> Explore Our Tools", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # NIL Valuator Card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_medium']} 100%);
                        padding: 25px; border-radius: 15px; border: 1px solid {COLORS['primary']};
                        margin: 10px 0; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.1);">
                <h3 style="color: {COLORS['primary']}; margin-bottom: 10px;">💰 NIL Valuator</h3>
                <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                    Real On3 NIL valuations plus our custom algorithm. Compare players,
                    analyze value breakdowns, and track market trends.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/nil_valuator.py", label="→ Open NIL Valuator", icon="💰", use_container_width=True)

        # Win Impact Card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_medium']} 100%);
                        padding: 25px; border-radius: 15px; border: 1px solid {COLORS['primary']};
                        margin: 10px 0; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.1);">
                <h3 style="color: {COLORS['primary']}; margin-bottom: 10px;">📈 Win Impact</h3>
                <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                    Understand how much value a player adds to their team. Win impact
                    directly correlates to NIL valuation and transfer market value.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/win_impact.py", label="→ Open Win Impact", icon="📈", use_container_width=True)

    with col2:
        # Portal Intelligence Card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_medium']} 100%);
                        padding: 25px; border-radius: 15px; border: 1px solid {COLORS['primary']};
                        margin: 10px 0; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.1);">
                <h3 style="color: {COLORS['primary']}; margin-bottom: 10px;">🔄 Portal Intelligence</h3>
                <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                    14,000+ transfer portal entries across 3 years. Track commitments,
                    analyze team rankings, and find the best portal targets.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/portal_intelligence.py", label="→ Open Portal Intelligence", icon="🔄", use_container_width=True)

        # AI Assistant Card
        with st.container():
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_medium']} 100%);
                        padding: 25px; border-radius: 15px; border: 1px solid {COLORS['primary']};
                        margin: 10px 0; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.1);">
                <h3 style="color: {COLORS['primary']}; margin-bottom: 10px;">🤖 AI Assistant</h3>
                <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                    Chat with Claude AI about players, NIL values, and portal activity.
                    Get instant insights and recommendations powered by real data.
                </p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/ai_assistant.py", label="→ Open AI Assistant", icon="🤖", use_container_width=True)

    st.divider()

    # Recent Activity - Real Data
    selected_season = get_selected_season()
    portal_year = selected_season + 1  # Portal year is season + 1 (2025 season = 2026 portal)

    st.markdown(f"### 📈 Live Data ({selected_season}-{selected_season + 1} Season)")

    col1, col2, col3 = st.columns(3)

    # Get real data
    nil_df = get_nil_players()
    portal_df = get_portal_players(year=portal_year)
    team_df = get_team_rankings(year=portal_year)

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
        st.markdown(f"#### 🏆 Top Portal Classes ({portal_year})")
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
    # Auth temporarily disabled for demo
    # show_user_menu()  # Show user info in sidebar when logged in
    # user = require_auth()  # Shows login form if not authenticated
    # if not user:
    #     return  # Stop here - login form is displayed
    # if not require_subscription():  # Check for active Stripe subscription
    #     return  # Stop here - paywall message is displayed

    render_main_page()


if __name__ == "__main__":
    main()
