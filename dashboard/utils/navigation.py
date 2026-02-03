"""Shared navigation component for Portal IQ Dashboard."""

import streamlit as st
from utils.data_loader import get_database_stats


def get_selected_season() -> int:
    """Get the currently selected season from session state."""
    if "selected_season" not in st.session_state:
        st.session_state.selected_season = 2025  # Current season
    return st.session_state.selected_season


def render_sidebar():
    """Render the sidebar with navigation and info. Call this from every page."""
    with st.sidebar:
        # Logo - clean and minimal
        st.markdown("""
        <div style="text-align: center; padding: 15px 0 10px 0;">
            <h1 style="color: #00C853; font-size: 1.8rem; margin: 0; font-weight: 700;">🏈 Portal IQ</h1>
        </div>
        """, unsafe_allow_html=True)

        # Navigation - styled buttons
        st.markdown("""
        <style>
        /* Hide default Streamlit page links */
        [data-testid="stSidebarNav"] {display: none;}

        /* Custom nav button styling */
        .nav-link {
            display: block;
            padding: 12px 16px;
            margin: 4px 0;
            background: #21262d;
            border-radius: 8px;
            color: #e6edf3 !important;
            text-decoration: none !important;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.2s ease;
            border-left: 3px solid transparent;
        }
        .nav-link:hover {
            background: #30363d;
            border-left-color: #00C853;
            color: #00C853 !important;
        }
        .nav-link.active {
            background: #161b22;
            border-left-color: #00C853;
            color: #00C853 !important;
        }
        .nav-section {
            color: #8b949e;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            padding: 15px 16px 8px 16px;
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="nav-section">Main Menu</div>', unsafe_allow_html=True)

        # Navigation using page_link with better spacing
        st.page_link("app.py", label="🏠  Home", use_container_width=True)
        st.page_link("pages/nil_valuator.py", label="💰  NIL Valuator", use_container_width=True)
        st.page_link("pages/portal_intelligence.py", label="🔄  Portal Intelligence", use_container_width=True)
        st.page_link("pages/win_impact.py", label="📈  Win Impact", use_container_width=True)
        st.page_link("pages/ai_assistant.py", label="🤖  AI Assistant", use_container_width=True)

        # Season selector
        st.markdown('<div class="nav-section">Season</div>', unsafe_allow_html=True)

        season_options = {
            2025: "2025-26 (Current)",
            2024: "2024-25",
            2023: "2023-24"
        }

        selected = st.selectbox(
            "View Season",
            options=list(season_options.keys()),
            format_func=lambda x: season_options[x],
            index=0,
            key="season_selector",
            label_visibility="collapsed"
        )

        if selected != st.session_state.get("selected_season", 2025):
            st.session_state.selected_season = selected
            st.rerun()

        # Data status - compact
        st.markdown('<div class="nav-section">Data Status</div>', unsafe_allow_html=True)

        stats = get_database_stats()
        st.markdown(f"""
        <div style="padding: 8px 16px; font-size: 0.85rem;">
            <p style="margin: 3px 0; color: #8b949e;">
                <span style="color: #e6edf3;">{stats.get('total_players', 0):,}</span> players tracked
            </p>
            <p style="margin: 3px 0; color: #8b949e;">
                Updated: <span style="color: #e6edf3;">{stats.get('last_updated', 'N/A')}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Footer - fixed at bottom
        st.markdown("""
        <div style="position: fixed; bottom: 0; left: 0; width: inherit; max-width: inherit;
                    padding: 15px; background: linear-gradient(to top, #0d1117 0%, transparent 100%);
                    text-align: center;">
            <p style="color: #6e7681; font-size: 0.7rem; margin: 0;">
                <strong style="color: #00C853;">Elite Sports Solutions</strong> © 2025
            </p>
        </div>
        """, unsafe_allow_html=True)
