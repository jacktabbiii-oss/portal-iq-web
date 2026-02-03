"""
Portal IQ Streamlit Dashboard

Main dashboard application for Portal IQ.
"""

import streamlit as st

st.set_page_config(
    page_title="Portal IQ",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main dashboard application."""
    st.title("🏈 Portal IQ")
    st.markdown(
        """
        **AI-powered transfer portal and NIL intelligence platform for college football.**

        Built by Elite Sports Solutions.
        """
    )

    st.divider()

    # Dashboard overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Active Portal Players",
            value="2,847",
            delta="+127 this week",
        )

    with col2:
        st.metric(
            label="NIL Valuations",
            value="$1.2B",
            delta="+$45M",
        )

    with col3:
        st.metric(
            label="Draft Prospects",
            value="892",
            delta="+23",
        )

    with col4:
        st.metric(
            label="Schools Tracked",
            value="134",
            delta="All FBS",
        )

    st.divider()

    # Quick links to pages
    st.subheader("Quick Navigation")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            ### 💰 NIL Valuator
            Get market valuations for any college football player based on
            performance, social media presence, school, and position.

            ### 🎯 Portal Intelligence
            Track transfer portal entries, predict likely destinations,
            and identify at-risk players on your roster.
            """
        )

    with col2:
        st.markdown(
            """
            ### 📊 Draft Tracker
            Project NFL draft outcomes for college players with comparisons
            to historical picks and career value estimates.

            ### 🏟️ Roster Builder
            Optimize your roster with AI-powered recommendations for
            portal targets within your NIL budget.
            """
        )

    st.divider()

    # Recent activity
    st.subheader("Recent Portal Activity")

    # Sample data - would be replaced with real data
    recent_data = {
        "Player": ["John Smith", "Mike Johnson", "David Williams", "Chris Brown", "James Wilson"],
        "Position": ["QB", "WR", "EDGE", "RB", "CB"],
        "From": ["Alabama", "USC", "Georgia", "Ohio State", "Clemson"],
        "To": ["Texas", "---", "Oregon", "---", "Miami"],
        "NIL Value": ["$2.5M", "$850K", "$1.2M", "$650K", "$720K"],
        "Status": ["Committed", "In Portal", "Committed", "In Portal", "Committed"],
    }

    st.dataframe(
        recent_data,
        use_container_width=True,
        hide_index=True,
    )

    # Footer
    st.divider()
    st.markdown(
        """
        <div style='text-align: center; color: gray;'>
        Portal IQ v1.0.0 | Elite Sports Solutions | Data updated hourly
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
