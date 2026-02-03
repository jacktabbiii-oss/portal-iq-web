"""
Draft Tracker Page

Streamlit page for NFL draft projections and analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Draft Tracker | Portal IQ",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Draft Tracker")
st.markdown("Project NFL draft outcomes for college football players.")

# Sidebar filters
st.sidebar.header("Filters")

position_filter = st.sidebar.selectbox(
    "Position",
    ["All", "QB", "RB", "WR", "TE", "OT", "OG", "C", "EDGE", "DT", "LB", "CB", "S"],
)

round_filter = st.sidebar.slider(
    "Projected Round",
    min_value=1,
    max_value=7,
    value=(1, 3),
)

conference_filter = st.sidebar.multiselect(
    "Conference",
    ["SEC", "Big Ten", "Big 12", "ACC", "Pac-12", "Other"],
    default=["SEC", "Big Ten"],
)

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "Draft Board",
    "Player Lookup",
    "Comparisons",
    "Historical",
])

with tab1:
    st.subheader("2025 NFL Draft Big Board")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Projected 1st Rounders", "32")
    with col2:
        st.metric("Top QB Prospect", "Shedeur Sanders")
    with col3:
        st.metric("Top Edge Prospect", "Abdul Carter")
    with col4:
        st.metric("Days to Draft", "98")

    # Big board
    big_board = pd.DataFrame({
        "Rank": range(1, 21),
        "Player": [
            "Travis Hunter", "Abdul Carter", "Cam Ward", "Tetairoa McMillan",
            "Mason Graham", "Will Campbell", "Shedeur Sanders", "Kelvin Banks Jr.",
            "Malaki Starks", "Mykel Williams", "Luther Burden III", "Derrick Harmon",
            "Ashton Jeanty", "Colston Loveland", "Jalon Walker", "Nick Singleton",
            "Benjamin Morrison", "Nic Scourton", "Tyler Warren", "Quinshon Judkins"
        ],
        "Position": [
            "CB/WR", "EDGE", "QB", "WR", "DT", "OT", "QB", "OT",
            "S", "EDGE", "WR", "DT", "RB", "TE", "LB", "RB",
            "CB", "EDGE", "TE", "RB"
        ],
        "School": [
            "Colorado", "Penn State", "Miami", "Arizona", "Michigan", "LSU",
            "Colorado", "Texas", "Georgia", "Georgia", "Missouri", "Oregon",
            "Boise State", "Michigan", "Georgia", "Penn State", "Notre Dame",
            "Texas A&M", "Penn State", "Ohio State"
        ],
        "Grade": [98, 95, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76],
        "Proj. Pick": list(range(1, 21)),
    })

    st.dataframe(
        big_board,
        use_container_width=True,
        hide_index=True,
    )

    # Position breakdown
    st.markdown("#### First Round Projection by Position")

    position_counts = pd.DataFrame({
        "Position": ["EDGE", "CB", "WR", "OT", "QB", "DT", "RB", "LB", "S", "TE"],
        "Count": [5, 4, 4, 4, 3, 3, 3, 2, 2, 2],
    })

    fig = px.bar(
        position_counts,
        x="Position",
        y="Count",
        title="Projected First Round Picks by Position",
        color="Count",
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Player Draft Projection")

    col1, col2 = st.columns([2, 1])

    with col1:
        player_search = st.text_input("Search Player", placeholder="Enter player name...")
        selected_player = st.selectbox(
            "Or Select from Top Prospects",
            ["Travis Hunter", "Cam Ward", "Shedeur Sanders", "Abdul Carter", "Tetairoa McMillan"],
        )

    with col2:
        if st.button("Generate Projection", type="primary"):
            st.success("Projection generated!")

    # Player projection details
    st.markdown(f"#### Draft Projection: {selected_player}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Draft Probability", "99%")
        st.metric("Projected Pick", "#1")
        st.metric("Draft Grade", "98/100")

    with col2:
        st.metric("Projected Round", "1st")
        st.metric("Position Rank", "#1 CB/WR")
        st.metric("Combine Invite", "Yes")

    with col3:
        st.metric("Rookie Contract", "$42M")
        st.metric("Career Earnings", "$150M+")
        st.metric("Pro Bowl Prob", "85%")

    # Comparable players
    st.markdown("#### Historical Comparisons")
    comps = pd.DataFrame({
        "Player": ["Charles Woodson", "Champ Bailey", "Deion Sanders"],
        "Draft Year": [1998, 1999, 1989],
        "Draft Pick": [4, 7, 5],
        "Similarity": ["92%", "88%", "85%"],
        "Career": ["HOF", "HOF", "HOF"],
    })
    st.dataframe(comps, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Player Comparisons")

    col1, col2 = st.columns(2)

    with col1:
        player1 = st.selectbox("Player 1", ["Cam Ward", "Shedeur Sanders", "Jalen Milroe"], key="p1")

    with col2:
        player2 = st.selectbox("Player 2", ["Shedeur Sanders", "Cam Ward", "Jalen Milroe"], key="p2")

    # Comparison radar chart
    categories = ["Arm Strength", "Accuracy", "Mobility", "Decision Making", "Leadership", "Clutch"]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=[85, 88, 92, 84, 90, 88],
        theta=categories,
        fill='toself',
        name=player1
    ))

    fig.add_trace(go.Scatterpolar(
        r=[82, 90, 78, 88, 92, 85],
        theta=categories,
        fill='toself',
        name=player2
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title=f"{player1} vs {player2} Comparison"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Stats comparison
    st.markdown("#### Statistical Comparison")
    stats_comp = pd.DataFrame({
        "Metric": ["Pass Yards", "TDs", "INTs", "Completion %", "QBR", "Rush Yards"],
        player1: ["3,847", "32", "7", "68.5%", "88.4", "312"],
        player2: ["3,621", "29", "5", "71.2%", "85.7", "245"],
    })
    st.dataframe(stats_comp, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("Historical Draft Data")

    # School draft history
    st.markdown("#### Most NFL Draft Picks (2020-2024)")

    school_history = pd.DataFrame({
        "School": ["Alabama", "Ohio State", "Georgia", "LSU", "Clemson", "Michigan", "Notre Dame", "Penn State"],
        "Total Picks": [52, 48, 45, 38, 35, 32, 28, 27],
        "1st Rounders": [14, 12, 13, 9, 8, 7, 5, 6],
        "Avg Pick": [48, 52, 45, 62, 58, 68, 85, 72],
    })

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            school_history,
            x="School",
            y="Total Picks",
            title="Draft Picks by School (2020-2024)",
            color="1st Rounders",
            color_continuous_scale="Reds",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Position value over time
        position_value = pd.DataFrame({
            "Year": [2020, 2021, 2022, 2023, 2024],
            "QB": [2, 3, 1, 4, 2],
            "EDGE": [4, 5, 6, 3, 5],
            "CB": [5, 4, 3, 5, 6],
            "WR": [6, 4, 5, 7, 4],
        })

        fig = px.line(
            position_value,
            x="Year",
            y=["QB", "EDGE", "CB", "WR"],
            title="First Round Picks by Position",
        )
        st.plotly_chart(fig, use_container_width=True)

    # Conference breakdown
    st.markdown("#### Draft Picks by Conference (2024)")
    conf_picks = pd.DataFrame({
        "Conference": ["SEC", "Big Ten", "ACC", "Big 12", "Pac-12", "Other"],
        "Picks": [65, 48, 32, 28, 35, 52],
    })

    fig = px.pie(
        conf_picks,
        values="Picks",
        names="Conference",
        title="2024 Draft Picks by Conference",
    )
    st.plotly_chart(fig, use_container_width=True)
