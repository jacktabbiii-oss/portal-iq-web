"""Styling utilities for Portal IQ Dashboard.

Navy blue and gold theme matching Portal IQ branding.
Compass logo with football helmet - professional sports analytics look.
"""

import streamlit as st

# Color palette - Portal IQ Ultra Modern Design System
# Based on Figma designs - darker navy with bright gold
COLORS = {
    # Primary colors - Bright Gold accent (from Figma)
    "primary": "#F5BF03",         # Portal Gold (bright yellow-gold)
    "primary_dark": "#D4A503",    # Darker gold for hover
    "primary_light": "#FFD32A",   # Lighter gold

    # Background colors - Ultra dark navy theme
    "bg_dark": "#0F1629",         # Primary Dark (darkest)
    "bg_medium": "#141D2F",       # Medium dark
    "bg_light": "#1A2744",        # Card/surface background
    "bg_card": "#1E2D47",         # Elevated card backgrounds
    "bg_input": "#0D1220",        # Input field backgrounds

    # Text colors - High contrast
    "text_primary": "#FFFFFF",     # Pure white for headings
    "text_secondary": "#B8C4D4",   # Light gray for body text
    "text_muted": "#6B7A8F",       # Muted for labels
    "text_gold": "#F5BF03",        # Gold text for highlights

    # Tier colors (NIL)
    "tier_mega": "#F5BF03",        # Gold (Mega deals)
    "tier_premium": "#A855F7",     # Purple
    "tier_solid": "#3B82F6",       # Blue
    "tier_moderate": "#22C55E",    # Green
    "tier_entry": "#6B7A8F",       # Gray

    # Risk colors
    "risk_critical": "#EF4444",    # Red
    "risk_high": "#F97316",        # Orange
    "risk_moderate": "#EAB308",    # Yellow
    "risk_low": "#22C55E",         # Green

    # Status colors
    "status_active": "#22C55E",    # Green - In Portal
    "status_committed": "#3B82F6", # Blue - Committed
    "status_withdrawn": "#6B7A8F", # Gray - Withdrawn

    # Chart colors
    "chart_1": "#F5BF03",          # Gold
    "chart_2": "#3B82F6",          # Blue
    "chart_3": "#A855F7",          # Purple
    "chart_4": "#F97316",          # Orange
    "chart_5": "#EF4444",          # Red
    "chart_6": "#22C55E",          # Green
    "chart_7": "#06B6D4",          # Cyan

    # Borders and accents
    "border": "#2A3A54",           # Subtle border
    "border_gold": "#F5BF03",      # Gold border for focus/highlight
    "glow_gold": "rgba(245, 191, 3, 0.3)",  # Gold glow effect
}


def get_tier_color(tier: str) -> str:
    """Get color for NIL tier."""
    tier_colors = {
        "mega": COLORS["tier_mega"],
        "premium": COLORS["tier_premium"],
        "solid": COLORS["tier_solid"],
        "moderate": COLORS["tier_moderate"],
        "entry": COLORS["tier_entry"],
    }
    return tier_colors.get(tier.lower(), COLORS["tier_entry"])


def get_risk_color(risk_level: str) -> str:
    """Get color for risk level."""
    risk_colors = {
        "critical": COLORS["risk_critical"],
        "high": COLORS["risk_high"],
        "moderate": COLORS["risk_moderate"],
        "low": COLORS["risk_low"],
    }
    return risk_colors.get(risk_level.lower(), COLORS["risk_moderate"])


def get_risk_color_by_value(risk_value: float) -> str:
    """Get color based on risk probability value."""
    if risk_value >= 0.7:
        return COLORS["risk_critical"]
    elif risk_value >= 0.5:
        return COLORS["risk_high"]
    elif risk_value >= 0.3:
        return COLORS["risk_moderate"]
    else:
        return COLORS["risk_low"]


def apply_custom_css():
    """Apply custom CSS styling to the Streamlit app - Ultra Modern Design."""
    st.markdown(f"""
    <style>
        /* ============================================= */
        /* PORTAL IQ ULTRA MODERN DESIGN SYSTEM         */
        /* Dark Navy + Bright Gold Theme                */
        /* ============================================= */

        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        /* Base styles */
        html, body, [data-testid="stAppViewContainer"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        /* Main app background */
        .stApp {{
            background: linear-gradient(180deg, {COLORS['bg_dark']} 0%, #0A0F1A 100%);
        }}

        /* Sidebar styling - matches Figma */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['bg_medium']};
            border-right: 1px solid {COLORS['border']};
        }}

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
            color: {COLORS['text_secondary']};
        }}

        /* Headers - white with Inter font */
        h1 {{
            color: {COLORS['text_primary']} !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            font-size: 2rem !important;
            letter-spacing: -0.02em;
        }}

        h2 {{
            color: {COLORS['text_primary']} !important;
            font-weight: 600 !important;
            font-size: 1.5rem !important;
        }}

        h3, h4, h5, h6 {{
            color: {COLORS['text_primary']} !important;
            font-weight: 600 !important;
        }}

        /* Regular text */
        p, span, label {{
            color: {COLORS['text_secondary']} !important;
            font-family: 'Inter', sans-serif !important;
        }}

        /* Markdown content */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] span {{
            color: {COLORS['text_secondary']} !important;
            line-height: 1.7;
        }}

        [data-testid="stMarkdownContainer"] ul,
        [data-testid="stMarkdownContainer"] ol {{
            color: {COLORS['text_secondary']} !important;
        }}

        [data-testid="stMarkdownContainer"] li {{
            color: {COLORS['text_secondary']} !important;
            margin-bottom: 6px;
        }}

        /* Bold text = white */
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stMarkdownContainer"] b {{
            color: {COLORS['text_primary']} !important;
            font-weight: 600;
        }}

        /* Emphasized text = gold */
        [data-testid="stMarkdownContainer"] em {{
            color: {COLORS['primary']} !important;
            font-style: normal;
        }}

        /* ============================================= */
        /* METRIC CARDS - Portal IQ Style               */
        /* ============================================= */

        [data-testid="stMetricValue"] {{
            color: {COLORS['primary']} !important;
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            font-family: 'Inter', sans-serif !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: {COLORS['text_muted']} !important;
            font-size: 0.85rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }}

        [data-testid="stMetricDelta"] {{
            font-weight: 600 !important;
        }}

        [data-testid="stMetricDelta"][data-testid="stMetricDeltaPositive"] {{
            color: {COLORS['status_active']} !important;
        }}

        [data-testid="stMetricDelta"][data-testid="stMetricDeltaNegative"] {{
            color: {COLORS['risk_critical']} !important;
        }}

        /* ============================================= */
        /* BUTTONS - Gold Primary Style                 */
        /* ============================================= */

        .stButton > button {{
            background-color: {COLORS['primary']} !important;
            color: {COLORS['bg_dark']} !important;
            border: none !important;
            border-radius: 50px !important;
            padding: 12px 28px !important;
            font-weight: 600 !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.2s ease !important;
            text-transform: none;
        }}

        .stButton > button:hover {{
            background-color: {COLORS['primary_light']} !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 20px {COLORS['glow_gold']};
        }}

        .stButton > button:active {{
            transform: translateY(0);
        }}

        /* Secondary/Ghost button */
        .stButton > button[kind="secondary"],
        .ghost-button > button {{
            background-color: transparent !important;
            color: {COLORS['primary']} !important;
            border: 2px solid {COLORS['primary']} !important;
        }}

        .stButton > button[kind="secondary"]:hover {{
            background-color: rgba(245, 191, 3, 0.1) !important;
        }}

        /* ============================================= */
        /* INPUT FIELDS - Dark with Gold Focus          */
        /* ============================================= */

        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {{
            background-color: {COLORS['bg_input']} !important;
            color: {COLORS['text_primary']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 50px !important;
            padding: 12px 20px !important;
            font-family: 'Inter', sans-serif !important;
        }}

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {{
            border-color: {COLORS['primary']} !important;
            box-shadow: 0 0 0 3px {COLORS['glow_gold']} !important;
            outline: none !important;
        }}

        .stTextInput > div > div > input::placeholder {{
            color: {COLORS['text_muted']} !important;
        }}

        /* Selectbox and dropdowns */
        [data-testid="stSelectbox"] > div > div {{
            background-color: {COLORS['bg_light']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 12px !important;
        }}

        [data-baseweb="select"] > div {{
            background-color: {COLORS['bg_light']} !important;
            border-color: {COLORS['border']} !important;
            border-radius: 12px !important;
        }}

        [data-baseweb="select"] > div:focus-within {{
            border-color: {COLORS['primary']} !important;
            box-shadow: 0 0 0 3px {COLORS['glow_gold']} !important;
        }}

        /* Dropdown menu */
        [data-baseweb="menu"] {{
            background-color: {COLORS['bg_card']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 12px !important;
        }}

        [data-baseweb="menu"] li {{
            color: {COLORS['text_secondary']} !important;
        }}

        [data-baseweb="menu"] li:hover {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['primary']} !important;
        }}

        [data-baseweb="select"] [data-baseweb="tag"] {{
            background-color: {COLORS['primary']} !important;
            color: {COLORS['bg_dark']} !important;
            border-radius: 20px !important;
        }}

        /* Multiselect */
        .stMultiSelect > div > div {{
            background-color: {COLORS['bg_light']} !important;
            border-radius: 12px !important;
        }}

        /* Slider - gold track */
        .stSlider > div > div > div > div {{
            background-color: {COLORS['primary']} !important;
        }}

        .stSlider [data-baseweb="slider"] [role="slider"] {{
            background-color: {COLORS['primary']} !important;
            border-color: {COLORS['primary']} !important;
        }}

        /* ============================================= */
        /* TABS - Modern Pill Style                     */
        /* ============================================= */

        .stTabs [data-baseweb="tab-list"] {{
            background-color: {COLORS['bg_light']};
            border-radius: 50px;
            padding: 6px;
            gap: 4px;
            border: 1px solid {COLORS['border']};
        }}

        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            color: {COLORS['text_muted']};
            border-radius: 50px;
            padding: 10px 24px;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            color: {COLORS['text_primary']};
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {COLORS['primary']} !important;
            color: {COLORS['bg_dark']} !important;
            font-weight: 600;
        }}

        /* ============================================= */
        /* DATA TABLES - Modern Dark Style              */
        /* ============================================= */

        [data-testid="stDataFrame"] {{
            background-color: {COLORS['bg_light']};
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid {COLORS['border']};
        }}

        .stDataFrame thead tr th {{
            background-color: {COLORS['bg_card']} !important;
            color: {COLORS['text_muted']} !important;
            font-weight: 500 !important;
            text-transform: uppercase !important;
            font-size: 0.75rem !important;
            letter-spacing: 0.05em !important;
            padding: 14px 16px !important;
        }}

        .stDataFrame tbody tr td {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['text_secondary']} !important;
            padding: 14px 16px !important;
            border-bottom: 1px solid {COLORS['border']} !important;
        }}

        .stDataFrame tbody tr:hover td {{
            background-color: {COLORS['bg_card']} !important;
        }}

        /* Table general */
        table, th, td {{
            color: {COLORS['text_secondary']} !important;
        }}

        th {{
            color: {COLORS['text_muted']} !important;
            font-weight: 500 !important;
            text-transform: uppercase;
            font-size: 0.75rem;
        }}

        /* ============================================= */
        /* EXPANDERS                                    */
        /* ============================================= */

        .streamlit-expanderHeader {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['text_primary']} !important;
            border-radius: 12px !important;
            border: 1px solid {COLORS['border']} !important;
        }}

        .streamlit-expanderHeader:hover {{
            border-color: {COLORS['primary']} !important;
        }}

        .streamlit-expanderHeader p {{
            color: {COLORS['text_primary']} !important;
            font-weight: 500;
        }}

        .streamlit-expanderContent {{
            background-color: {COLORS['bg_light']};
            border-radius: 0 0 12px 12px;
            border: 1px solid {COLORS['border']};
            border-top: none;
        }}

        .streamlit-expanderContent p,
        .streamlit-expanderContent li {{
            color: {COLORS['text_secondary']} !important;
        }}

        /* ============================================= */
        /* ALERTS & MESSAGES                            */
        /* ============================================= */

        [data-testid="stAlert"] {{
            background-color: {COLORS['bg_light']} !important;
            border-radius: 12px !important;
            border-left: 4px solid !important;
        }}

        [data-testid="stAlert"] p {{
            color: {COLORS['text_secondary']} !important;
        }}

        .stSuccess {{
            border-left-color: {COLORS['status_active']} !important;
        }}

        .stInfo {{
            border-left-color: {COLORS['chart_2']} !important;
        }}

        .stWarning {{
            border-left-color: {COLORS['risk_moderate']} !important;
        }}

        .stError {{
            border-left-color: {COLORS['risk_critical']} !important;
        }}

        /* Caption text */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {COLORS['text_muted']} !important;
            font-size: 0.8rem !important;
        }}

        /* ============================================= */
        /* CARDS - Modern Glass Style                   */
        /* ============================================= */

        .card {{
            background: {COLORS['bg_light']};
            padding: 24px;
            border-radius: 16px;
            border: 1px solid {COLORS['border']};
            margin: 12px 0;
            transition: all 0.2s ease;
        }}

        .card:hover {{
            border-color: {COLORS['primary']};
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        }}

        .card-highlight {{
            border-color: {COLORS['primary']};
            box-shadow: 0 0 20px {COLORS['glow_gold']};
        }}

        /* Stat Cards */
        .stat-card {{
            background: {COLORS['bg_light']};
            padding: 20px 24px;
            border-radius: 12px;
            border: 1px solid {COLORS['border']};
            text-align: center;
        }}

        .stat-card-value {{
            color: {COLORS['primary']} !important;
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
        }}

        .stat-card-label {{
            color: {COLORS['text_muted']} !important;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 4px;
        }}

        /* ============================================= */
        /* BADGES - Tier & Status                       */
        /* ============================================= */

        .tier-badge {{
            padding: 6px 16px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: inline-block;
        }}

        .tier-mega {{
            background-color: {COLORS['tier_mega']};
            color: {COLORS['bg_dark']};
        }}

        .tier-premium {{
            background-color: {COLORS['tier_premium']};
            color: #fff;
        }}

        .tier-solid {{
            background-color: {COLORS['tier_solid']};
            color: #fff;
        }}

        .tier-moderate {{
            background-color: {COLORS['tier_moderate']};
            color: #fff;
        }}

        .tier-entry {{
            background-color: {COLORS['tier_entry']};
            color: #fff;
        }}

        /* Status badges */
        .status-badge {{
            padding: 4px 12px;
            border-radius: 50px;
            font-weight: 500;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}

        .status-active {{
            background-color: rgba(34, 197, 94, 0.2);
            color: {COLORS['status_active']};
            border: 1px solid {COLORS['status_active']};
        }}

        .status-committed {{
            background-color: rgba(59, 130, 246, 0.2);
            color: {COLORS['status_committed']};
            border: 1px solid {COLORS['status_committed']};
        }}

        .status-withdrawn {{
            background-color: rgba(107, 122, 143, 0.2);
            color: {COLORS['status_withdrawn']};
            border: 1px solid {COLORS['status_withdrawn']};
        }}

        /* Risk badges */
        .risk-badge {{
            padding: 4px 12px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.7rem;
            text-transform: uppercase;
        }}

        .risk-critical {{
            background-color: rgba(239, 68, 68, 0.2);
            color: {COLORS['risk_critical']};
        }}

        .risk-high {{
            background-color: rgba(249, 115, 22, 0.2);
            color: {COLORS['risk_high']};
        }}

        .risk-moderate {{
            background-color: rgba(234, 179, 8, 0.2);
            color: {COLORS['risk_moderate']};
        }}

        .risk-low {{
            background-color: rgba(34, 197, 94, 0.2);
            color: {COLORS['risk_low']};
        }}

        /* Confidence badges */
        .confidence-high {{
            background-color: rgba(34, 197, 94, 0.15);
            color: {COLORS['status_active']};
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        /* Divider */
        hr {{
            border-color: {COLORS['bg_light']};
        }}

        /* Plotly charts - dark theme */
        .js-plotly-plot .plotly .modebar {{
            background-color: transparent !important;
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: {COLORS['bg_dark']};
        }}

        ::-webkit-scrollbar-thumb {{
            background: {COLORS['bg_light']};
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['primary']};
        }}

        /* Loading spinner */
        .stSpinner > div {{
            border-color: {COLORS['primary']} transparent transparent transparent;
        }}

        /* Toast messages */
        .stToast {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            border-left: 4px solid {COLORS['primary']};
        }}

        /* Multiselect */
        .stMultiSelect [data-baseweb="tag"] {{
            background-color: {COLORS['primary']};
            color: {COLORS['bg_dark']};
        }}

        /* Progress bar */
        .stProgress > div > div > div {{
            background-color: {COLORS['primary']};
        }}

        /* Alert boxes */
        .stAlert {{
            background-color: {COLORS['bg_medium']};
            border-radius: 8px;
        }}

        /* ============================================= */
        /* CHAT INTERFACE - AI Assistant Style          */
        /* ============================================= */

        [data-testid="stChatMessage"] {{
            background-color: {COLORS['bg_light']} !important;
            border-radius: 16px !important;
            border: 1px solid {COLORS['border']} !important;
            margin: 8px 0 !important;
        }}

        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] li,
        [data-testid="stChatMessage"] span {{
            color: {COLORS['text_secondary']} !important;
            line-height: 1.7 !important;
        }}

        [data-testid="stChatMessage"] strong {{
            color: {COLORS['text_primary']} !important;
        }}

        /* Chat input */
        [data-testid="stChatInput"] {{
            background-color: {COLORS['bg_input']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 50px !important;
        }}

        [data-testid="stChatInput"]:focus-within {{
            border-color: {COLORS['primary']} !important;
            box-shadow: 0 0 0 3px {COLORS['glow_gold']} !important;
        }}

        /* Code blocks */
        [data-testid="stMarkdownContainer"] code {{
            background-color: {COLORS['bg_card']} !important;
            color: {COLORS['primary']} !important;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.9em;
        }}

        [data-testid="stMarkdownContainer"] pre {{
            background-color: {COLORS['bg_card']} !important;
            color: {COLORS['text_secondary']} !important;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid {COLORS['border']};
        }}

        /* Blockquotes */
        [data-testid="stMarkdownContainer"] blockquote {{
            border-left: 3px solid {COLORS['primary']} !important;
            padding-left: 16px;
            color: {COLORS['text_muted']} !important;
            margin: 16px 0;
        }}

        /* Links */
        [data-testid="stMarkdownContainer"] a {{
            color: {COLORS['primary']} !important;
            text-decoration: none;
        }}

        [data-testid="stMarkdownContainer"] a:hover {{
            color: {COLORS['primary_light']} !important;
            text-decoration: underline;
        }}

        /* ============================================= */
        /* FORMS                                        */
        /* ============================================= */

        [data-testid="stForm"] {{
            background-color: {COLORS['bg_light']};
            padding: 24px;
            border-radius: 16px;
            border: 1px solid {COLORS['border']};
        }}

        /* Download button */
        .stDownloadButton > button {{
            background-color: transparent !important;
            color: {COLORS['primary']} !important;
            border: 2px solid {COLORS['primary']} !important;
            border-radius: 50px !important;
        }}

        .stDownloadButton > button:hover {{
            background-color: {COLORS['primary']} !important;
            color: {COLORS['bg_dark']} !important;
        }}

        /* ============================================= */
        /* PLAYER ROW COMPONENT                         */
        /* ============================================= */

        .player-row {{
            display: flex;
            align-items: center;
            padding: 16px 20px;
            background: {COLORS['bg_light']};
            border-radius: 12px;
            border: 1px solid {COLORS['border']};
            margin: 8px 0;
            transition: all 0.2s ease;
        }}

        .player-row:hover {{
            border-color: {COLORS['primary']};
            background: {COLORS['bg_card']};
        }}

        .player-avatar {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: 2px solid {COLORS['primary']};
            margin-right: 16px;
            object-fit: cover;
        }}

        .player-avatar-initials {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: {COLORS['bg_card']};
            border: 2px solid {COLORS['primary']};
            display: flex;
            align-items: center;
            justify-content: center;
            color: {COLORS['primary']};
            font-weight: 600;
            font-size: 1rem;
            margin-right: 16px;
        }}

        .player-info {{
            flex: 1;
        }}

        .player-name {{
            color: {COLORS['text_primary']};
            font-weight: 600;
            font-size: 1rem;
        }}

        .player-team {{
            color: {COLORS['text_muted']};
            font-size: 0.85rem;
        }}

        .player-value {{
            color: {COLORS['primary']};
            font-weight: 700;
            font-size: 1.25rem;
        }}

        /* ============================================= */
        /* WAR GAUGE COMPONENT                          */
        /* ============================================= */

        .war-gauge {{
            width: 200px;
            height: 200px;
            position: relative;
        }}

        .war-gauge-value {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}

        .war-gauge-number {{
            color: {COLORS['primary']};
            font-size: 3rem;
            font-weight: 700;
            line-height: 1;
        }}

        .war-gauge-label {{
            color: {COLORS['text_muted']};
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }}

        /* ============================================= */
        /* NAVIGATION - Sidebar Style                   */
        /* ============================================= */

        /* Hide default Streamlit page navigation */
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        /* Navigation items */
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
            background: transparent !important;
            border-radius: 12px !important;
            padding: 12px 16px !important;
            margin: 4px 0 !important;
            border-left: 3px solid transparent !important;
            transition: all 0.2s ease !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
            background: {COLORS['bg_light']} !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {{
            background: {COLORS['bg_light']} !important;
            border-left-color: {COLORS['primary']} !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p {{
            color: {COLORS['text_muted']} !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover p {{
            color: {COLORS['text_primary']} !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p {{
            color: {COLORS['primary']} !important;
            font-weight: 600 !important;
        }}

        /* Sidebar header */
        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 0 !important;
        }}

        [data-testid="stSidebarContent"] {{
            padding: 1rem !important;
        }}

        /* Sidebar section headers */
        .sidebar-section {{
            color: {COLORS['text_muted']};
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-top: 24px;
            margin-bottom: 8px;
            padding-left: 16px;
        }}

        /* ============================================= */
        /* SCROLLBAR - Modern Dark Style                */
        /* ============================================= */

        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: {COLORS['bg_dark']};
        }}

        ::-webkit-scrollbar-thumb {{
            background: {COLORS['border']};
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS['primary']};
        }}

        /* ============================================= */
        /* PROGRESS & LOADING                           */
        /* ============================================= */

        .stProgress > div > div > div {{
            background-color: {COLORS['primary']} !important;
        }}

        .stSpinner > div {{
            border-color: {COLORS['primary']} transparent transparent transparent !important;
        }}

        /* ============================================= */
        /* DIVIDERS & SEPARATORS                        */
        /* ============================================= */

        hr {{
            border-color: {COLORS['border']} !important;
            margin: 24px 0 !important;
        }}

        /* ============================================= */
        /* GLOBAL TEXT & TYPOGRAPHY                     */
        /* ============================================= */

        body, .main, .block-container {{
            color: {COLORS['text_secondary']} !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }}

        /* Headers */
        h1 {{
            font-size: 2rem !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
            margin-bottom: 8px !important;
        }}
        h2 {{
            font-size: 1.5rem !important;
            font-weight: 600 !important;
            margin-bottom: 8px !important;
        }}
        h3 {{
            font-size: 1.25rem !important;
            font-weight: 600 !important;
        }}
        h4 {{
            font-size: 1rem !important;
            font-weight: 600 !important;
        }}

        /* Body text */
        p, li, span {{
            font-size: 0.95rem !important;
            line-height: 1.6 !important;
        }}

        /* Small/muted text */
        small, .small, .muted {{
            font-size: 0.8rem !important;
            color: {COLORS['text_muted']} !important;
        }}

        /* Gold highlight text */
        .gold, .highlight {{
            color: {COLORS['primary']} !important;
        }}

        /* Metric deltas */
        [data-testid="stMetricDelta"] svg {{
            fill: currentColor !important;
        }}

        /* ============================================= */
        /* PLOTLY CHARTS - Dark Theme                   */
        /* ============================================= */

        .js-plotly-plot .plotly .modebar {{
            background-color: transparent !important;
        }}

        .js-plotly-plot .plotly .modebar-btn {{
            color: {COLORS['text_muted']} !important;
        }}

        .js-plotly-plot .plotly .modebar-btn:hover {{
            color: {COLORS['primary']} !important;
        }}

        /* ============================================= */
        /* TOAST NOTIFICATIONS                          */
        /* ============================================= */

        .stToast {{
            background-color: {COLORS['bg_card']} !important;
            color: {COLORS['text_primary']} !important;
            border-left: 4px solid {COLORS['primary']} !important;
            border-radius: 12px !important;
        }}

        /* ============================================= */
        /* COLUMN LAYOUT SPACING                        */
        /* ============================================= */

        [data-testid="column"] {{
            padding: 0 8px !important;
        }}

        /* ============================================= */
        /* CUSTOM UTILITY CLASSES                       */
        /* ============================================= */

        .text-gold {{ color: {COLORS['primary']} !important; }}
        .text-white {{ color: {COLORS['text_primary']} !important; }}
        .text-muted {{ color: {COLORS['text_muted']} !important; }}
        .bg-card {{ background: {COLORS['bg_light']} !important; }}
        .border-gold {{ border-color: {COLORS['primary']} !important; }}
        .glow-gold {{ box-shadow: 0 0 20px {COLORS['glow_gold']} !important; }}

    </style>
    """, unsafe_allow_html=True)


def render_tier_badge(tier: str) -> str:
    """Render HTML for a tier badge."""
    tier_lower = tier.lower()
    return f'<span class="tier-badge tier-{tier_lower}">{tier.upper()}</span>'


def render_risk_badge(risk_level: str) -> str:
    """Render HTML for a risk badge."""
    risk_lower = risk_level.lower()
    return f'<span class="risk-badge risk-{risk_lower}">{risk_level.title()}</span>'


def render_status_badge(status: str) -> str:
    """Render HTML for a status badge (Active, Committed, Withdrawn)."""
    status_lower = status.lower().replace(" ", "-")
    status_map = {
        "in-portal": "active",
        "active": "active",
        "committed": "committed",
        "withdrawn": "withdrawn",
        "entered": "active",
    }
    badge_class = status_map.get(status_lower, "active")
    return f'<span class="status-badge status-{badge_class}">{status.title()}</span>'


def render_confidence_badge(confidence: str) -> str:
    """Render HTML for a confidence badge."""
    return f'<span class="confidence-high">● {confidence.upper()}</span>'


def render_player_row(name: str, team: str, position: str, value: float, initials: str = None) -> str:
    """Render HTML for a player row component."""
    if initials is None:
        initials = "".join([n[0] for n in name.split()[:2]]).upper()

    value_str = format_currency(value)

    return f'''
    <div class="player-row">
        <div class="player-avatar-initials">{initials}</div>
        <div class="player-info">
            <div class="player-name">{name}</div>
            <div class="player-team">{team} • {position}</div>
        </div>
        <div class="player-value">{value_str}</div>
    </div>
    '''


def render_stat_card(value: str, label: str, trend: str = None) -> str:
    """Render HTML for a stat card component."""
    trend_html = ""
    if trend:
        trend_color = COLORS['status_active'] if trend.startswith('+') else COLORS['risk_critical']
        trend_html = f'<div style="color: {trend_color}; font-size: 0.85rem; font-weight: 500;">{trend}</div>'

    return f'''
    <div class="stat-card">
        <div class="stat-card-value">{value}</div>
        <div class="stat-card-label">{label}</div>
        {trend_html}
    </div>
    '''


def format_currency(value: float) -> str:
    """Format value as currency."""
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.0f}K"
    else:
        return f"${value:,.0f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value * 100:.1f}%"


def format_number(value: float) -> str:
    """Format large numbers with K/M suffix."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return f"{value:,.0f}"


# =============================================
# PLOTLY CHART THEMING
# =============================================

def get_plotly_layout(title: str = None, height: int = 400) -> dict:
    """Get Plotly layout dict matching Portal IQ theme."""
    layout = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": COLORS["bg_light"],
        "font": {
            "family": "Inter, sans-serif",
            "color": COLORS["text_secondary"],
        },
        "title": {
            "text": title,
            "font": {
                "size": 18,
                "color": COLORS["text_primary"],
            },
            "x": 0,
        } if title else None,
        "xaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickfont": {"color": COLORS["text_muted"]},
        },
        "yaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickfont": {"color": COLORS["text_muted"]},
        },
        "height": height,
        "margin": {"l": 40, "r": 20, "t": 60 if title else 20, "b": 40},
    }
    return layout


def get_chart_colors() -> list:
    """Get chart color palette."""
    return [
        COLORS["chart_1"],
        COLORS["chart_2"],
        COLORS["chart_3"],
        COLORS["chart_4"],
        COLORS["chart_5"],
        COLORS["chart_6"],
        COLORS["chart_7"],
    ]
