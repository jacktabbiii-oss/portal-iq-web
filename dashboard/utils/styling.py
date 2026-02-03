"""Styling utilities for Portal IQ Dashboard.

Dark theme with green (#00C853) and white accents on dark gray (#1a1a2e) background.
"""

import streamlit as st

# Color palette
COLORS = {
    # Primary colors
    "primary": "#00C853",  # Green
    "primary_dark": "#00A844",
    "primary_light": "#69F0AE",

    # Background colors
    "bg_dark": "#1a1a2e",
    "bg_medium": "#2a2a4a",
    "bg_light": "#3a3a5a",

    # Text colors
    "text_primary": "#ffffff",
    "text_secondary": "#cccccc",
    "text_muted": "#888888",

    # Tier colors (NIL)
    "tier_mega": "#FFD700",      # Gold
    "tier_premium": "#9C27B0",   # Purple
    "tier_solid": "#2196F3",     # Blue
    "tier_moderate": "#4CAF50",  # Green
    "tier_entry": "#9E9E9E",     # Gray

    # Risk colors
    "risk_critical": "#F44336",  # Red
    "risk_high": "#FF9800",      # Orange
    "risk_moderate": "#FFC107",  # Yellow
    "risk_low": "#4CAF50",       # Green

    # Chart colors
    "chart_1": "#00C853",
    "chart_2": "#2196F3",
    "chart_3": "#9C27B0",
    "chart_4": "#FF9800",
    "chart_5": "#F44336",
    "chart_6": "#00BCD4",
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

        /* Regular text */
        p, span, label {{
            color: {COLORS['text_secondary']};
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
            box-shadow: 0 4px 12px rgba(0, 200, 83, 0.3);
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
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['bg_light']};
            border-radius: 8px;
        }}

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {{
            border-color: {COLORS['primary']};
            box-shadow: 0 0 0 2px rgba(0, 200, 83, 0.2);
        }}

        /* Selectbox */
        [data-testid="stSelectbox"] {{
            background-color: {COLORS['bg_medium']};
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

        /* DataFrame/Table styling */
        [data-testid="stDataFrame"] {{
            background-color: {COLORS['bg_medium']};
            border-radius: 10px;
            overflow: hidden;
        }}

        .stDataFrame thead tr th {{
            background-color: {COLORS['bg_light']} !important;
            color: {COLORS['text_primary']} !important;
        }}

        .stDataFrame tbody tr td {{
            background-color: {COLORS['bg_medium']} !important;
            color: {COLORS['text_secondary']} !important;
        }}

        .stDataFrame tbody tr:hover td {{
            background-color: {COLORS['bg_light']} !important;
        }}

        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            border-radius: 8px;
        }}

        .streamlit-expanderContent {{
            background-color: {COLORS['bg_medium']};
            border-radius: 0 0 8px 8px;
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
