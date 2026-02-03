"""
NIL Valuator Page

Streamlit page for NIL valuation functionality.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="NIL Valuator | Portal IQ",
    page_icon="💰",
    layout="wide",
)

st.title("💰 NIL Valuator")
st.markdown("Get market valuations for college football players.")

# Sidebar filters
st.sidebar.header("Filters")

position = st.sidebar.selectbox(
    "Position",
    ["All", "QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB", "K", "P"],
)

school_tier = st.sidebar.selectbox(
    "School Tier",
    ["All", "Blue Blood", "Elite", "Power Brand", "P4 Mid", "G5 Strong", "G5"],
)

nil_tier = st.sidebar.selectbox(
    "NIL Tier",
    ["All", "Mega ($1M+)", "Premium ($500K+)", "Solid ($100K+)", "Moderate ($25K+)", "Entry"],
)

# Main content
tab1, tab2, tab3 = st.tabs(["Player Lookup", "Leaderboard", "Analytics"])

with tab1:
    st.subheader("Player Valuation")

    col1, col2 = st.columns([2, 1])

    with col1:
        player_name = st.text_input("Player Name", placeholder="Enter player name...")
        player_school = st.selectbox(
            "School",
            ["Alabama", "Ohio State", "Georgia", "Michigan", "Texas", "USC", "Other..."],
        )
        player_position = st.selectbox(
            "Position",
            ["QB", "RB", "WR", "TE", "OT", "OG", "C", "DE", "DT", "LB", "CB", "S"],
        )

    with col2:
        social_followers = st.number_input(
            "Social Media Followers",
            min_value=0,
            max_value=10000000,
            value=50000,
            step=1000,
        )
        engagement_rate = st.slider(
            "Engagement Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
        )
        recruiting_stars = st.select_slider(
            "Recruiting Stars",
            options=[2, 3, 4, 5],
            value=3,
        )

    if st.button("Calculate Valuation", type="primary"):
        # Placeholder calculation - would use actual model
        base_value = {
            "QB": 500000, "RB": 200000, "WR": 180000, "TE": 120000,
            "OT": 100000, "OG": 80000, "C": 70000, "DE": 150000,
            "DT": 100000, "LB": 130000, "CB": 160000, "S": 120000,
        }.get(player_position, 100000)

        school_mult = 2.0 if player_school in ["Alabama", "Ohio State", "Georgia"] else 1.5
        social_value = social_followers * 0.05
        star_mult = 0.8 + (recruiting_stars * 0.1)

        valuation = (base_value * school_mult * star_mult) + social_value

        st.success(f"Estimated NIL Valuation: **${valuation:,.0f}**")

        # Show breakdown
        st.markdown("#### Valuation Breakdown")
        breakdown_data = {
            "Component": ["Base Position Value", "School Multiplier", "Star Rating", "Social Media"],
            "Value": [f"${base_value:,}", f"{school_mult}x", f"{star_mult:.1f}x", f"${social_value:,.0f}"],
        }
        st.table(pd.DataFrame(breakdown_data))

with tab2:
    st.subheader("NIL Leaderboard")

    # Sample leaderboard data
    leaderboard_data = pd.DataFrame({
        "Rank": range(1, 11),
        "Player": [
            "Travis Hunter", "Arch Manning", "Jeremiah Smith", "Carson Beck",
            "Cam Ward", "Tetairoa McMillan", "Will Howard", "Ollie Gordon II",
            "Quinshon Judkins", "Jalen Milroe"
        ],
        "School": [
            "Colorado", "Texas", "Ohio State", "Georgia",
            "Miami", "Arizona", "Ohio State", "Oklahoma State",
            "Ohio State", "Alabama"
        ],
        "Position": ["CB/WR", "QB", "WR", "QB", "QB", "WR", "QB", "RB", "RB", "QB"],
        "NIL Value": [
            "$4.8M", "$3.5M", "$2.8M", "$2.5M", "$2.3M",
            "$2.1M", "$1.9M", "$1.8M", "$1.7M", "$1.6M"
        ],
        "Tier": ["Mega"] * 5 + ["Premium"] * 5,
    })

    st.dataframe(
        leaderboard_data,
        use_container_width=True,
        hide_index=True,
    )

with tab3:
    st.subheader("NIL Analytics")

    col1, col2 = st.columns(2)

    with col1:
        # NIL by position chart
        position_data = pd.DataFrame({
            "Position": ["QB", "WR", "RB", "EDGE", "CB", "OT", "LB", "TE"],
            "Avg NIL ($K)": [850, 420, 380, 350, 320, 280, 260, 220],
        })

        fig = px.bar(
            position_data,
            x="Position",
            y="Avg NIL ($K)",
            title="Average NIL by Position",
            color="Avg NIL ($K)",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # NIL by school tier
        tier_data = pd.DataFrame({
            "Tier": ["Blue Blood", "Elite", "Power Brand", "P4 Mid", "G5 Strong", "G5"],
            "Avg NIL ($K)": [620, 380, 220, 140, 80, 45],
        })

        fig = px.bar(
            tier_data,
            x="Tier",
            y="Avg NIL ($K)",
            title="Average NIL by School Tier",
            color="Avg NIL ($K)",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig, use_container_width=True)

    # NIL distribution
    st.markdown("#### NIL Distribution")
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=[50, 75, 100, 120, 150, 180, 200, 250, 300, 400, 500, 800, 1000, 1500, 2000, 3000],
        nbinsx=20,
        name="Players",
    ))
    fig.update_layout(
        title="Distribution of NIL Valuations",
        xaxis_title="NIL Value ($K)",
        yaxis_title="Number of Players",
    )
    st.plotly_chart(fig, use_container_width=True)
