"""Shared navigation component for Portal IQ Dashboard.

Navy blue and gold branding with compass logo.
"""

import streamlit as st
from pathlib import Path
from utils.data_loader import get_database_stats

# Brand colors
BRAND_GOLD = "#D4AF37"
BRAND_NAVY = "#152238"
BRAND_NAVY_LIGHT = "#1e3a5f"


def get_selected_season() -> int:
    """Get the currently selected season from session state."""
    if "selected_season" not in st.session_state:
        st.session_state.selected_season = 2025  # Current season
    return st.session_state.selected_season


def render_sidebar():
    """Render the sidebar with navigation and info. Call this from every page."""
    with st.sidebar:
        # Logo - Portal IQ branding
        logo_path = Path(__file__).parent.parent / "static" / "logo.png"

        if logo_path.exists():
            st.image(str(logo_path), use_container_width=True)
        else:
            # Fallback: Text-based logo with gold styling
            st.markdown(f"""
            <div style="text-align: center; padding: 20px 10px 15px 10px;">
                <div style="display: inline-flex; align-items: center; gap: 10px;">
                    <div style="width: 45px; height: 45px; background: linear-gradient(135deg, {BRAND_GOLD} 0%, #B8962E 100%);
                                border-radius: 50%; display: flex; align-items: center; justify-content: center;
                                box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);">
                        <span style="font-size: 1.4rem;">🧭</span>
                    </div>
                    <div>
                        <h1 style="color: #ffffff; font-size: 1.5rem; margin: 0; font-weight: 700; letter-spacing: 1px;">
                            PORTAL IQ
                        </h1>
                        <p style="color: {BRAND_GOLD}; font-size: 0.65rem; margin: 0; letter-spacing: 2px; text-transform: uppercase;">
                            Transfer Intelligence
                        </p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Navigation - styled buttons with navy/gold theme
        st.markdown(f"""
        <style>
        /* Hide default Streamlit page links */
        [data-testid="stSidebarNav"] {{display: none;}}

        /* Custom nav button styling - Navy theme */
        .nav-link {{
            display: block;
            padding: 12px 16px;
            margin: 4px 0;
            background: {BRAND_NAVY_LIGHT};
            border-radius: 8px;
            color: #c9d6e3 !important;
            text-decoration: none !important;
            font-size: 0.95rem;
            font-weight: 500;
            transition: all 0.2s ease;
            border-left: 3px solid transparent;
        }}
        .nav-link:hover {{
            background: #2c5282;
            border-left-color: {BRAND_GOLD};
            color: {BRAND_GOLD} !important;
        }}
        .nav-link.active {{
            background: {BRAND_NAVY};
            border-left-color: {BRAND_GOLD};
            color: {BRAND_GOLD} !important;
        }}
        .nav-section {{
            color: {BRAND_GOLD};
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            padding: 15px 16px 8px 16px;
            font-weight: 600;
        }}
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

        # Data status - compact with navy theme
        st.markdown('<div class="nav-section">Data Status</div>', unsafe_allow_html=True)

        stats = get_database_stats()
        st.markdown(f"""
        <div style="padding: 8px 16px; font-size: 0.85rem;">
            <p style="margin: 3px 0; color: #a8b8c8;">
                <span style="color: #ffffff;">{stats.get('total_players', 0):,}</span> players tracked
            </p>
            <p style="margin: 3px 0; color: #a8b8c8;">
                Updated: <span style="color: #c9d6e3;">{stats.get('last_updated', 'N/A')}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Footer - fixed at bottom with navy/gold branding
        st.markdown(f"""
        <div style="position: fixed; bottom: 0; left: 0; width: inherit; max-width: inherit;
                    padding: 15px; background: linear-gradient(to top, #0f1a2e 0%, transparent 100%);
                    text-align: center;">
            <p style="color: #a8b8c8; font-size: 0.7rem; margin: 0;">
                <strong style="color: {BRAND_GOLD};">Elite Sports Solutions</strong> © 2026
            </p>
        </div>
        """, unsafe_allow_html=True)
