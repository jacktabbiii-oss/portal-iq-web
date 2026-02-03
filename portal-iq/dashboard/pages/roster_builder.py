"""
Roster Builder Page

Streamlit page for roster optimization and planning.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Roster Builder | Portal IQ",
    page_icon="🏟️",
    layout="wide",
)

st.title("🏟️ Roster Builder")
st.markdown("Optimize your roster with AI-powered recommendations.")

# Sidebar - Team Selection
st.sidebar.header("Team Selection")

team = st.sidebar.selectbox(
    "Select Your Team",
    ["Alabama", "Ohio State", "Georgia", "Michigan", "Texas", "USC", "Oregon", "Penn State"],
)

budget = st.sidebar.number_input(
    "NIL Budget ($)",
    min_value=1000000,
    max_value=50000000,
    value=10000000,
    step=500000,
    format="%d",
)

max_additions = st.sidebar.slider(
    "Max Portal Additions",
    min_value=1,
    max_value=20,
    value=8,
)

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "Current Roster",
    "Position Needs",
    "Portal Targets",
    "Optimization",
])

with tab1:
    st.subheader(f"{team} Current Roster")

    # Roster summary
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Players", "85")
    with col2:
        st.metric("Avg Star Rating", "3.8")
    with col3:
        st.metric("Returning Starters", "14")
    with col4:
        st.metric("Portal Losses", "8")

    # Roster breakdown
    st.markdown("#### Roster by Position Group")

    roster_breakdown = pd.DataFrame({
        "Position Group": ["Quarterbacks", "Running Backs", "Wide Receivers", "Tight Ends", "Offensive Line", "Defensive Line", "Linebackers", "Defensive Backs", "Specialists"],
        "Count": [3, 4, 9, 3, 15, 10, 8, 11, 4],
        "Scholarships": [3, 4, 8, 3, 15, 10, 8, 10, 3],
        "Avg Stars": [4.3, 3.8, 3.9, 3.5, 3.7, 3.8, 3.6, 3.9, 3.0],
        "Starters Returning": [1, 1, 2, 1, 4, 3, 2, 2, 2],
    })

    st.dataframe(roster_breakdown, use_container_width=True, hide_index=True)

    # Roster visualization
    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(
            roster_breakdown,
            values="Count",
            names="Position Group",
            title="Roster Composition",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            roster_breakdown,
            x="Position Group",
            y="Avg Stars",
            title="Average Talent by Position",
            color="Avg Stars",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Position Needs Analysis")

    # Needs overview
    needs_data = pd.DataFrame({
        "Position": ["CB", "EDGE", "WR", "OT", "RB", "LB", "S", "TE"],
        "Current Depth": [3, 4, 7, 4, 3, 6, 4, 2],
        "Ideal Depth": [5, 5, 9, 5, 4, 7, 5, 3],
        "Need": [2, 1, 2, 1, 1, 1, 1, 1],
        "Priority": ["Critical", "High", "High", "Medium", "Medium", "Medium", "Low", "Low"],
        "Available in Portal": [45, 38, 82, 28, 65, 52, 41, 22],
    })

    st.dataframe(needs_data, use_container_width=True, hide_index=True)

    # Priority visualization
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Current Depth",
        x=needs_data["Position"],
        y=needs_data["Current Depth"],
        marker_color="lightblue",
    ))

    fig.add_trace(go.Bar(
        name="Ideal Depth",
        x=needs_data["Position"],
        y=needs_data["Ideal Depth"],
        marker_color="darkblue",
    ))

    fig.update_layout(
        title="Current vs Ideal Depth Chart",
        barmode="group",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Departures impact
    st.markdown("#### Impact of Departures")

    departures = pd.DataFrame({
        "Player": ["John Smith", "Mike Davis", "Chris Wilson"],
        "Position": ["CB", "WR", "EDGE"],
        "Stars": [4, 4, 3],
        "Impact": ["Starter Lost", "Key Contributor", "Rotation Player"],
        "Replacement Priority": ["Critical", "High", "Medium"],
    })

    st.dataframe(departures, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Portal Target Board")

    # Target filters
    col1, col2, col3 = st.columns(3)

    with col1:
        target_position = st.multiselect(
            "Position",
            ["CB", "EDGE", "WR", "OT", "RB", "LB", "S", "TE"],
            default=["CB", "WR"],
        )

    with col2:
        min_stars = st.select_slider(
            "Minimum Stars",
            options=[2, 3, 4, 5],
            value=3,
        )

    with col3:
        max_nil = st.number_input(
            "Max NIL ($)",
            min_value=100000,
            max_value=5000000,
            value=1000000,
            step=100000,
        )

    # Target board
    targets = pd.DataFrame({
        "Player": ["Marcus Johnson", "Tyler Williams", "Devon Brown", "Andre Clark", "Jordan Lee"],
        "Position": ["CB", "CB", "WR", "WR", "EDGE"],
        "From": ["Oregon", "USC", "Michigan", "Texas", "Penn State"],
        "Stars": [4, 4, 4, 3, 4],
        "NIL Ask": ["$850K", "$720K", "$650K", "$450K", "$780K"],
        "Fit Score": [94, 91, 88, 86, 85],
        "Win Impact": [0.8, 0.7, 0.6, 0.4, 0.7],
        "Available": ["Yes", "Yes", "Yes", "Yes", "Yes"],
    })

    st.dataframe(targets, use_container_width=True, hide_index=True)

    # Target comparison
    st.markdown("#### Target Comparison")

    fig = px.scatter(
        targets,
        x="NIL Ask",
        y="Win Impact",
        color="Position",
        size="Fit Score",
        hover_data=["Player", "From"],
        title="Value vs Win Impact",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Roster Optimization")

    st.markdown(f"**Budget:** ${budget:,} | **Max Additions:** {max_additions}")

    # Optimization settings
    col1, col2 = st.columns(2)

    with col1:
        strategy = st.radio(
            "Optimization Strategy",
            ["Maximize Wins", "Best Value", "Fill Needs", "Balanced"],
        )

    with col2:
        constraints = st.multiselect(
            "Constraints",
            ["Must fill CB need", "At least 1 QB", "No more than 3 from same school"],
            default=["Must fill CB need"],
        )

    if st.button("Run Optimization", type="primary"):
        st.success("Optimization complete!")

        # Results
        st.markdown("#### Recommended Additions")

        optimized = pd.DataFrame({
            "Priority": [1, 2, 3, 4, 5],
            "Player": ["Marcus Johnson", "Tyler Williams", "Devon Brown", "Andre Clark", "Sam Thomas"],
            "Position": ["CB", "CB", "WR", "WR", "EDGE"],
            "NIL Cost": ["$850K", "$720K", "$650K", "$450K", "$680K"],
            "Win Impact": [0.8, 0.7, 0.6, 0.4, 0.6],
            "ROI Score": [94, 97, 92, 89, 88],
        })

        st.dataframe(optimized, use_container_width=True, hide_index=True)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Cost", "$3.35M")
        with col2:
            st.metric("Budget Remaining", f"${budget - 3350000:,}")
        with col3:
            st.metric("Projected Win Impact", "+3.1 Wins")
        with col4:
            st.metric("Needs Filled", "4/5")

        # Win projection
        st.markdown("#### Season Projection")

        col1, col2 = st.columns(2)

        with col1:
            current_wins = 8
            projected_wins = 11.1

            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=projected_wins,
                delta={"reference": current_wins, "position": "top"},
                title={"text": "Projected Wins"},
                gauge={
                    "axis": {"range": [0, 15]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 6], "color": "lightcoral"},
                        {"range": [6, 9], "color": "lightyellow"},
                        {"range": [9, 12], "color": "lightgreen"},
                        {"range": [12, 15], "color": "green"},
                    ],
                },
            ))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            projections = pd.DataFrame({
                "Outcome": ["Playoff", "NY6 Bowl", "10+ Wins", "Bowl Eligible"],
                "Before": ["15%", "35%", "45%", "85%"],
                "After": ["55%", "75%", "82%", "95%"],
                "Change": ["+40%", "+40%", "+37%", "+10%"],
            })
            st.dataframe(projections, use_container_width=True, hide_index=True)
