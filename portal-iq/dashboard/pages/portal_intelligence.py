"""
Portal Intelligence Page

Streamlit page for transfer portal tracking and predictions.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Portal Intelligence | Portal IQ",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Portal Intelligence")
st.markdown("Track transfer portal activity and predict player movement.")

# Sidebar filters
st.sidebar.header("Filters")

status_filter = st.sidebar.multiselect(
    "Status",
    ["In Portal", "Committed", "Withdrawn"],
    default=["In Portal"],
)

position_filter = st.sidebar.multiselect(
    "Position",
    ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB"],
    default=[],
)

star_filter = st.sidebar.slider(
    "Minimum Stars",
    min_value=2,
    max_value=5,
    value=3,
)

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "Active Portal",
    "At-Risk Players",
    "Team Activity",
    "Predictions",
])

with tab1:
    st.subheader("Active Transfer Portal")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total in Portal", "2,847")
    with col2:
        st.metric("Committed", "1,523")
    with col3:
        st.metric("Still Available", "1,324")
    with col4:
        st.metric("4/5 Star Players", "187")

    # Sample portal data
    portal_data = pd.DataFrame({
        "Player": [
            "Mike Johnson", "Chris Davis", "Tyler Brown", "Marcus Williams",
            "Jordan Smith", "Devon Clark", "Andre Thomas", "Brandon Lee",
        ],
        "Position": ["WR", "QB", "RB", "CB", "LB", "DE", "OT", "S"],
        "Stars": [4, 5, 3, 4, 3, 4, 4, 3],
        "From": [
            "USC", "Alabama", "Michigan", "Georgia",
            "Texas", "Clemson", "Ohio State", "Oregon",
        ],
        "Entry Date": [
            "Jan 15", "Jan 12", "Jan 18", "Jan 10",
            "Jan 20", "Jan 8", "Jan 16", "Jan 14",
        ],
        "Days in Portal": [10, 13, 7, 15, 5, 17, 9, 11],
        "NIL Value": ["$850K", "$1.2M", "$320K", "$580K", "$290K", "$720K", "$450K", "$280K"],
        "Status": ["Available", "Committed", "Available", "Available", "Available", "Committed", "Available", "Available"],
    })

    st.dataframe(
        portal_data,
        use_container_width=True,
        hide_index=True,
    )

    # Portal timeline chart
    st.markdown("#### Portal Entry Timeline")
    timeline_data = pd.DataFrame({
        "Date": pd.date_range(start="2025-01-01", periods=20, freq="D"),
        "Entries": [45, 62, 78, 95, 120, 145, 132, 98, 87, 76, 65, 58, 52, 48, 42, 38, 35, 32, 28, 25],
    })

    fig = px.line(
        timeline_data,
        x="Date",
        y="Entries",
        title="Daily Portal Entries",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("At-Risk Player Analysis")

    team = st.selectbox(
        "Select Team",
        ["Alabama", "Ohio State", "Georgia", "Michigan", "Texas", "USC"],
    )

    st.markdown(f"#### Players at Risk of Entering Portal - {team}")

    # Sample at-risk data
    at_risk_data = pd.DataFrame({
        "Player": ["John Doe", "Jake Smith", "Marcus Brown", "Tyler Johnson"],
        "Position": ["WR", "RB", "CB", "LB"],
        "Year": ["SO", "JR", "SO", "SR"],
        "Depth Chart": ["2nd", "3rd", "2nd", "2nd"],
        "Snap Trend": ["-25%", "-40%", "-15%", "-10%"],
        "Portal Risk": ["78%", "85%", "62%", "55%"],
        "Risk Factors": [
            "Decreased snaps, new WR commits",
            "Lost starting job, coaching change",
            "New CB commits, limited PT",
            "Final year, backup role",
        ],
    })

    st.dataframe(
        at_risk_data,
        use_container_width=True,
        hide_index=True,
    )

    # Risk distribution
    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(
            values=[4, 8, 15, 58],
            names=["High Risk (>75%)", "Medium Risk (50-75%)", "Low Risk (25-50%)", "Minimal (<25%)"],
            title="Roster Risk Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        risk_by_position = pd.DataFrame({
            "Position": ["QB", "RB", "WR", "TE", "OL", "DL", "LB", "DB"],
            "At Risk": [1, 2, 3, 1, 2, 2, 2, 3],
        })
        fig = px.bar(
            risk_by_position,
            x="Position",
            y="At Risk",
            title="At-Risk Players by Position",
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Team Portal Activity")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Top Portal Winners (Net Talent)")
        winners_data = pd.DataFrame({
            "Team": ["Colorado", "Texas", "Oregon", "Miami", "Ohio State"],
            "Incoming": [28, 15, 12, 14, 11],
            "Outgoing": [8, 5, 4, 6, 4],
            "Net": [20, 10, 8, 8, 7],
            "Avg Stars In": [3.8, 4.1, 4.0, 3.9, 4.2],
        })
        st.dataframe(winners_data, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### Top Portal Losers (Net Talent)")
        losers_data = pd.DataFrame({
            "Team": ["Florida State", "Nebraska", "USC", "Auburn", "LSU"],
            "Incoming": [5, 6, 7, 4, 6],
            "Outgoing": [18, 14, 14, 11, 12],
            "Net": [-13, -8, -7, -7, -6],
            "Avg Stars Out": [3.6, 3.4, 3.8, 3.5, 3.7],
        })
        st.dataframe(losers_data, use_container_width=True, hide_index=True)

    # Conference breakdown
    st.markdown("#### Portal Activity by Conference")
    conf_data = pd.DataFrame({
        "Conference": ["SEC", "Big Ten", "Big 12", "ACC", "Pac-12/Other"],
        "Incoming": [145, 132, 118, 105, 98],
        "Outgoing": [128, 115, 125, 142, 88],
        "Net": [17, 17, -7, -37, 10],
    })

    fig = px.bar(
        conf_data,
        x="Conference",
        y=["Incoming", "Outgoing"],
        title="Portal Movement by Conference",
        barmode="group",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Portal Predictions")

    st.markdown("#### Predict Player Destination")

    col1, col2 = st.columns(2)

    with col1:
        player = st.selectbox(
            "Select Portal Player",
            ["Mike Johnson (WR)", "Chris Davis (QB)", "Tyler Brown (RB)"],
        )

    with col2:
        if st.button("Generate Prediction", type="primary"):
            st.success("Prediction generated!")

    # Sample prediction results
    st.markdown("#### Predicted Destinations for Mike Johnson")

    prediction_data = pd.DataFrame({
        "School": ["Oregon", "Miami", "Texas", "USC", "Colorado"],
        "Probability": [32, 24, 18, 14, 12],
        "Fit Score": [92, 88, 85, 82, 78],
        "NIL Potential": ["$950K", "$1.1M", "$1.2M", "$880K", "$750K"],
        "Position Need": ["High", "High", "Medium", "Medium", "High"],
    })

    st.dataframe(prediction_data, use_container_width=True, hide_index=True)

    # Visualization
    fig = px.bar(
        prediction_data,
        x="School",
        y="Probability",
        color="Fit Score",
        title="Destination Probability",
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig, use_container_width=True)
