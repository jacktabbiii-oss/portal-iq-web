"""Styling utilities for Portal IQ Dashboard.

Navy blue and gold theme matching Portal IQ branding.
Compass logo with football helmet - professional sports analytics look.
"""

import streamlit as st

# Color palette - Portal IQ Navy & Gold Branding
COLORS = {
    # Primary colors - Gold accent
    "primary": "#D4AF37",         # Gold (main accent)
    "primary_dark": "#B8962E",    # Darker gold
    "primary_light": "#E8C547",   # Lighter gold

    # Background colors - Navy blue theme
    "bg_dark": "#0f1a2e",         # Darkest navy
    "bg_medium": "#152238",       # Medium navy
    "bg_light": "#1e3a5f",        # Lighter navy (cards, hover)
    "bg_card": "#1a2d4d",         # Card backgrounds

    # Text colors - IMPROVED CONTRAST for readability
    "text_primary": "#ffffff",     # Pure white
    "text_secondary": "#e8eef4",   # Much lighter for better readability
    "text_muted": "#a8b8c8",       # Brighter muted - was too dark
    "text_gold": "#D4AF37",        # Gold text for highlights

    # Tier colors (NIL) - Updated for navy theme
    "tier_mega": "#FFD700",        # Bright Gold
    "tier_premium": "#9C27B0",     # Purple
    "tier_solid": "#4A90D9",       # Blue
    "tier_moderate": "#5CB85C",    # Green
    "tier_entry": "#a8b8c8",       # Brighter muted gray for readability

    # Risk colors
    "risk_critical": "#E74C3C",    # Red
    "risk_high": "#F39C12",        # Orange
    "risk_moderate": "#F1C40F",    # Yellow
    "risk_low": "#27AE60",         # Green

    # Chart colors - Navy theme palette
    "chart_1": "#D4AF37",          # Gold
    "chart_2": "#4A90D9",          # Blue
    "chart_3": "#9C27B0",          # Purple
    "chart_4": "#F39C12",          # Orange
    "chart_5": "#E74C3C",          # Red
    "chart_6": "#1ABC9C",          # Teal

    # Additional navy accents
    "navy_accent": "#2c5282",      # Accent navy
    "border": "#2d4a6f",           # Border color
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
    """Apply custom CSS styling to the Streamlit app."""
    st.markdown(f"""
    <style>
        /* Main app background */
        .stApp {{
            background-color: {COLORS['bg_dark']};
        }}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['bg_medium']};
            border-right: 1px solid {COLORS['bg_light']};
        }}

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
            color: {COLORS['text_secondary']};
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS['text_primary']} !important;
        }}

        /* Regular text - IMPROVED for readability */
        p, span, label {{
            color: {COLORS['text_secondary']} !important;
        }}

        /* Markdown content - ensure good contrast */
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] span {{
            color: {COLORS['text_secondary']} !important;
            line-height: 1.6;
        }}

        /* Lists in markdown */
        [data-testid="stMarkdownContainer"] ul,
        [data-testid="stMarkdownContainer"] ol {{
            color: {COLORS['text_secondary']} !important;
        }}

        [data-testid="stMarkdownContainer"] li {{
            color: {COLORS['text_secondary']} !important;
            margin-bottom: 4px;
        }}

        /* Strong/bold text should be white */
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stMarkdownContainer"] b {{
            color: {COLORS['text_primary']} !important;
            font-weight: 600;
        }}

        /* Emphasized text */
        [data-testid="stMarkdownContainer"] em {{
            color: {COLORS['primary_light']} !important;
        }}

        /* Metric styling */
        [data-testid="stMetricValue"] {{
            color: {COLORS['primary']} !important;
            font-size: 2rem !important;
        }}

        [data-testid="stMetricLabel"] {{
            color: {COLORS['text_secondary']} !important;
        }}

        [data-testid="stMetricDelta"] {{
            color: {COLORS['primary_light']} !important;
        }}

        /* Button styling */
        .stButton > button {{
            background-color: {COLORS['primary']};
            color: {COLORS['bg_dark']};
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            transition: all 0.3s ease;
        }}

        .stButton > button:hover {{
            background-color: {COLORS['primary_light']};
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
        }}

        /* Secondary button */
        .stButton > button[kind="secondary"] {{
            background-color: transparent;
            color: {COLORS['primary']};
            border: 2px solid {COLORS['primary']};
        }}

        /* Input fields */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['text_primary']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 8px;
        }}

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {{
            border-color: {COLORS['primary']} !important;
            box-shadow: 0 0 0 2px rgba(212, 175, 55, 0.25);
        }}

        /* Selectbox and dropdowns */
        [data-testid="stSelectbox"] {{
            background-color: transparent;
        }}

        [data-testid="stSelectbox"] > div > div {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['text_primary']} !important;
        }}

        /* Dropdown menu items */
        [data-baseweb="menu"] {{
            background-color: {COLORS['bg_medium']} !important;
        }}

        [data-baseweb="menu"] li {{
            color: {COLORS['text_secondary']} !important;
        }}

        [data-baseweb="menu"] li:hover {{
            background-color: {COLORS['bg_light']} !important;
        }}

        /* BaseWeb select */
        [data-baseweb="select"] > div {{
            background-color: {COLORS['bg_light']} !important;
            border-color: {COLORS['border']} !important;
        }}

        [data-baseweb="select"] [data-baseweb="tag"] {{
            background-color: {COLORS['primary']} !important;
            color: #000 !important;
        }}

        /* Multiselect dropdown */
        .stMultiSelect > div > div {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['text_primary']} !important;
        }}

        /* Slider */
        .stSlider > div > div > div > div {{
            background-color: {COLORS['primary']};
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {COLORS['bg_medium']};
            border-radius: 10px;
            padding: 5px;
            gap: 5px;
        }}

        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            color: {COLORS['text_secondary']};
            border-radius: 8px;
            padding: 10px 20px;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {COLORS['primary']};
            color: {COLORS['bg_dark']};
        }}

        /* DataFrame/Table styling - IMPROVED contrast */
        [data-testid="stDataFrame"] {{
            background-color: {COLORS['bg_medium']};
            border-radius: 10px;
            overflow: hidden;
        }}

        .stDataFrame thead tr th {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['text_primary']} !important;
            font-weight: 600 !important;
        }}

        .stDataFrame tbody tr td {{
            background-color: {COLORS['bg_medium']} !important;
            color: {COLORS['text_secondary']} !important;
        }}

        .stDataFrame tbody tr:hover td {{
            background-color: {COLORS['bg_light']} !important;
        }}

        /* Table text should be readable */
        table, th, td {{
            color: {COLORS['text_secondary']} !important;
        }}

        th {{
            color: {COLORS['text_primary']} !important;
            font-weight: 600 !important;
        }}

        /* Expander - IMPROVED */
        .streamlit-expanderHeader {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']} !important;
            border-radius: 8px;
        }}

        .streamlit-expanderHeader p {{
            color: {COLORS['text_primary']} !important;
            font-weight: 500;
        }}

        .streamlit-expanderContent {{
            background-color: {COLORS['bg_medium']};
            border-radius: 0 0 8px 8px;
        }}

        .streamlit-expanderContent p,
        .streamlit-expanderContent li {{
            color: {COLORS['text_secondary']} !important;
        }}

        /* Info/Warning/Success boxes - ensure text is readable */
        [data-testid="stAlert"] p {{
            color: {COLORS['text_secondary']} !important;
        }}

        .stInfo, .stWarning, .stSuccess, .stError {{
            color: {COLORS['text_secondary']} !important;
        }}

        /* Caption text - was too faint */
        .stCaption, [data-testid="stCaptionContainer"] {{
            color: {COLORS['text_muted']} !important;
        }}

        /* Cards */
        .card {{
            background: linear-gradient(135deg, {COLORS['bg_dark']} 0%, {COLORS['bg_medium']} 100%);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid {COLORS['bg_light']};
            margin: 10px 0;
        }}

        .card-highlight {{
            border-color: {COLORS['primary']};
        }}

        /* Tier badges */
        .tier-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-block;
        }}

        .tier-mega {{
            background-color: {COLORS['tier_mega']};
            color: #000;
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

        /* Risk badges */
        .risk-badge {{
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: 500;
            font-size: 0.8rem;
        }}

        .risk-critical {{
            background-color: {COLORS['risk_critical']};
            color: #fff;
        }}

        .risk-high {{
            background-color: {COLORS['risk_high']};
            color: #000;
        }}

        .risk-moderate {{
            background-color: {COLORS['risk_moderate']};
            color: #000;
        }}

        .risk-low {{
            background-color: {COLORS['risk_low']};
            color: #fff;
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

        /* Chat messages - IMPROVED readability */
        [data-testid="stChatMessage"] {{
            background-color: {COLORS['bg_medium']} !important;
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

        /* Code blocks in chat/markdown */
        [data-testid="stMarkdownContainer"] code {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['primary_light']} !important;
            padding: 2px 6px;
            border-radius: 4px;
        }}

        [data-testid="stMarkdownContainer"] pre {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['text_secondary']} !important;
            padding: 12px;
            border-radius: 8px;
        }}

        /* Blockquotes */
        [data-testid="stMarkdownContainer"] blockquote {{
            border-left: 3px solid {COLORS['primary']} !important;
            padding-left: 15px;
            color: {COLORS['text_muted']} !important;
        }}

        /* Links should be gold */
        [data-testid="stMarkdownContainer"] a {{
            color: {COLORS['primary']} !important;
        }}

        [data-testid="stMarkdownContainer"] a:hover {{
            color: {COLORS['primary_light']} !important;
        }}

        /* Form styling */
        [data-testid="stForm"] {{
            background-color: {COLORS['bg_medium']};
            padding: 20px;
            border-radius: 10px;
            border: 1px solid {COLORS['bg_light']};
        }}

        /* Download button */
        .stDownloadButton > button {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['primary']};
            border: 2px solid {COLORS['primary']};
        }}

        .stDownloadButton > button:hover {{
            background-color: {COLORS['primary']};
            color: {COLORS['bg_dark']};
        }}

        /* ============================================= */
        /* NAVIGATION STYLING                           */
        /* ============================================= */

        /* Hide default Streamlit page navigation */
        [data-testid="stSidebarNav"] {{
            display: none !important;
        }}

        /* Style page_link buttons as nav items */
        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {{
            background: {COLORS['bg_light']} !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
            margin: 4px 0 !important;
            border-left: 3px solid transparent !important;
            transition: all 0.2s ease !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {{
            background: {COLORS['navy_accent']} !important;
            border-left-color: {COLORS['primary']} !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {{
            background: {COLORS['bg_medium']} !important;
            border-left-color: {COLORS['primary']} !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] p {{
            color: {COLORS['text_secondary']} !important;
            font-weight: 500 !important;
            font-size: 0.95rem !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover p {{
            color: {COLORS['primary']} !important;
        }}

        [data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] p {{
            color: {COLORS['primary']} !important;
        }}

        /* Sidebar header/logo area */
        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 0 !important;
        }}

        /* Sidebar overall padding */
        [data-testid="stSidebarContent"] {{
            padding: 1rem 0.75rem !important;
        }}

        /* ============================================= */
        /* GLOBAL TEXT READABILITY OVERRIDES            */
        /* ============================================= */

        /* Ensure ALL text has minimum readability */
        body, .main, .block-container {{
            color: {COLORS['text_secondary']} !important;
        }}

        /* Force better contrast on any remaining elements */
        div[data-testid] p:not([style*="color"]),
        div[data-testid] span:not([style*="color"]),
        div[data-testid] li:not([style*="color"]) {{
            color: {COLORS['text_secondary']} !important;
        }}

        /* Minimum font size for readability */
        p, li, span, td {{
            font-size: 0.95rem !important;
            line-height: 1.5 !important;
        }}

        /* Headers should stand out more */
        h1 {{ font-size: 2.2rem !important; font-weight: 700 !important; }}
        h2 {{ font-size: 1.8rem !important; font-weight: 600 !important; }}
        h3 {{ font-size: 1.4rem !important; font-weight: 600 !important; }}
        h4 {{ font-size: 1.2rem !important; font-weight: 600 !important; }}

        /* Small text should not be too small */
        small, .small {{
            font-size: 0.85rem !important;
            color: {COLORS['text_muted']} !important;
        }}

        /* Ensure metric deltas are visible */
        [data-testid="stMetricDelta"] svg {{
            fill: {COLORS['primary_light']} !important;
        }}
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
