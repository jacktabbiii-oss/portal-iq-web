"""
AI Assistant Page

AI-powered chat assistant for Portal IQ using Claude.
- Answer questions about players, NIL valuations, portal data
- Provide insights and recommendations
- Natural language queries
- Chat archive feature
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from anthropic import Anthropic

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import apply_custom_css, COLORS, format_currency
from utils.data_loader import (
    get_nil_players, get_portal_players, get_team_rankings,
    get_database_stats, search_players
)
from utils.navigation import render_sidebar

# Page config
st.set_page_config(
    page_title="AI Assistant | Portal IQ",
    page_icon="🤖",
    layout="wide",
)

apply_custom_css()


# =============================================================================
# AI Client Setup
# =============================================================================

@st.cache_resource
def get_anthropic_client():
    """Get Anthropic client with API key."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def get_data_context() -> str:
    """Build context string from current data for the AI."""
    context_parts = []

    # Database stats
    stats = get_database_stats()
    context_parts.append(f"""
DATABASE OVERVIEW:
- Total NIL Players: {stats.get('nil_valuations', 0):,}
- Portal Entries: {stats.get('portal_players', 0):,}
- Teams Tracked: {stats.get('schools', 0)}
- Last Updated: {stats.get('last_updated', 'Unknown')}
""")

    # Top NIL players
    nil_df = get_nil_players()
    if not nil_df.empty:
        top_nil = nil_df.nlargest(10, "nil_value")
        nil_list = "\n".join([
            f"  - {row['name']} ({row['position']}, {row.get('school', 'Unknown')}): ${row['nil_value']:,.0f}"
            for _, row in top_nil.iterrows()
        ])
        context_parts.append(f"""
TOP 10 NIL VALUATIONS:
{nil_list}
""")

    # Top portal classes
    team_df = get_team_rankings(year=2026)
    if not team_df.empty:
        top_teams = team_df.nlargest(10, "overall_score")
        team_list = "\n".join([
            f"  - {row['name']}: Score {row['overall_score']:.0f}, {int(row.get('transfers_in', 0))} transfers in"
            for _, row in top_teams.iterrows()
        ])
        context_parts.append(f"""
TOP 10 PORTAL CLASSES (2026):
{team_list}
""")

    # Portal status breakdown
    portal_df = get_portal_players(year=2026)
    if not portal_df.empty:
        status_counts = portal_df["status"].value_counts().to_dict()
        context_parts.append(f"""
2026 PORTAL STATUS:
- Entered: {status_counts.get('Entered', 0):,}
- Committed: {status_counts.get('Committed', 0):,}
- Expected: {status_counts.get('Expected', 0):,}
- Withdrawn: {status_counts.get('Withdrawn', 0):,}
""")

    return "\n".join(context_parts)


def get_player_info(player_name: str) -> str:
    """Get detailed info about a specific player."""
    results = search_players(player_name)
    if results.empty:
        return f"No player found matching '{player_name}'"

    info_parts = []
    for _, row in results.iterrows():
        source = row.get("data_source", "unknown")
        info = f"""
PLAYER: {row['name']}
- Position: {row.get('position', 'Unknown')}
- School: {row.get('school', row.get('origin_school', 'Unknown'))}
- NIL Value: ${row.get('nil_value', 0):,.0f}
- Stars: {row.get('stars', 'N/A')}
- Source: {source}
"""
        if source == "transfer_portal":
            info += f"""- Portal Status: {row.get('status', 'Unknown')}
- From: {row.get('origin_school', 'Unknown')}
- To: {row.get('destination_school', 'TBD')}
"""
        info_parts.append(info)

    return "\n".join(info_parts[:3])  # Limit to top 3 matches


SYSTEM_PROMPT = """You are the Portal IQ AI Assistant, an expert on college football transfer portal and NIL (Name, Image, Likeness) valuations.

You have access to real-time data from On3 including:
- NIL valuations for top college football players
- Transfer portal entries and commitments (2024-2026)
- Team portal class rankings
- Player recruiting ratings and stats

Your role is to:
1. Answer questions about specific players, their NIL values, and portal status
2. Provide insights on team portal classes and recruiting
3. Explain NIL valuation factors and market trends
4. Help users find players that match specific criteria
5. Offer analysis on transfer impact and win projections

Be concise but informative. Use specific data when available. If you don't have data on something, say so clearly.

Current data context will be provided with each message."""


def chat_with_claude(client: Anthropic, messages: list, user_message: str) -> str:
    """Send message to Claude and get response."""
    # Build context
    data_context = get_data_context()

    # Check if user is asking about a specific player
    player_context = ""
    words = user_message.lower().split()
    # Simple heuristic: if message contains capitalized words that might be names
    potential_names = [w for w in user_message.split() if w[0].isupper() and len(w) > 2]
    if potential_names:
        for name in potential_names[:2]:  # Check first 2 potential names
            player_info = get_player_info(name)
            if "No player found" not in player_info:
                player_context += player_info

    full_context = f"""
{data_context}

{f"PLAYER LOOKUP RESULTS:{player_context}" if player_context else ""}
"""

    # Build messages for API
    api_messages = []
    for msg in messages:
        api_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    # Add user message with context
    api_messages.append({
        "role": "user",
        "content": f"[DATA CONTEXT]\n{full_context}\n\n[USER QUESTION]\n{user_message}"
    })

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=api_messages
        )
        return response.content[0].text
    except Exception as e:
        return f"Error communicating with AI: {str(e)}"


# =============================================================================
# Main Page
# =============================================================================

def main():
    # Render shared navigation sidebar
    render_sidebar()

    # Header
    st.markdown("""
    <h1 style="color: #00C853;">🤖 AI Assistant</h1>
    <p style="color: #e6edf3; font-size: 1.1rem;">
        Ask questions about players, NIL valuations, and the transfer portal
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    # Check for API key
    client = get_anthropic_client()

    if not client:
        st.error("""
        **Anthropic API Key Required**

        Set the `ANTHROPIC_API_KEY` environment variable to enable the AI assistant.

        For Railway deployment, add it to your environment variables.
        """)

        # Show demo mode
        st.markdown("### Demo Mode")
        st.info("Without an API key, here are some example questions you could ask:")

        examples = [
            "Who are the top 5 highest NIL valued players?",
            "Tell me about Arch Manning's NIL valuation",
            "Which teams have the best 2026 portal classes?",
            "What quarterbacks are currently in the portal?",
            "How does NIL value correlate with recruiting stars?",
        ]

        for ex in examples:
            st.markdown(f"- *{ex}*")

        return

    # Initialize chat history and archives
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "archived_chats" not in st.session_state:
        st.session_state.archived_chats = []

    if "current_chat_title" not in st.session_state:
        st.session_state.current_chat_title = None

    # Quick actions
    st.markdown("### Quick Questions")
    col1, col2, col3, col4 = st.columns(4)

    quick_questions = [
        ("Top NIL Players", "Who are the top 5 highest NIL valued players right now?"),
        ("Best Portal Classes", "Which teams have the best 2026 transfer portal classes?"),
        ("Available QBs", "What quarterbacks are currently available in the portal?"),
        ("NIL Trends", "What are the current NIL market trends for college football?"),
    ]

    for i, (label, question) in enumerate(quick_questions):
        col = [col1, col2, col3, col4][i]
        with col:
            if st.button(label, key=f"quick_{i}", use_container_width=True):
                st.session_state.pending_question = question

    st.divider()

    # Chat container
    chat_container = st.container()

    # Display chat history
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]

            if role == "user":
                st.markdown(f"""
                <div style="background: {COLORS['bg_medium']}; padding: 15px; border-radius: 10px; margin: 10px 0;">
                    <strong style="color: {COLORS['primary']};">You:</strong>
                    <p style="color: {COLORS['text_primary']}; margin: 5px 0 0 0;">{content}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: {COLORS['bg_light']}; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 3px solid {COLORS['primary']};">
                    <strong style="color: {COLORS['primary']};">🤖 Portal IQ:</strong>
                    <p style="color: {COLORS['text_secondary']}; margin: 5px 0 0 0;">{content}</p>
                </div>
                """, unsafe_allow_html=True)

    # Handle pending quick question
    if "pending_question" in st.session_state:
        question = st.session_state.pending_question
        del st.session_state.pending_question

        # Add to history
        st.session_state.messages.append({"role": "user", "content": question})

        # Get response
        with st.spinner("Thinking..."):
            response = chat_with_claude(client, st.session_state.messages[:-1], question)
            st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

    # Chat input
    st.markdown("### Ask a Question")

    col1, col2 = st.columns([5, 1])

    with col1:
        user_input = st.text_input(
            "Your question",
            placeholder="e.g., Tell me about Sam Leavitt's NIL value and portal status...",
            key="chat_input",
            label_visibility="collapsed"
        )

    with col2:
        send_btn = st.button("Send", type="primary", use_container_width=True)

    if send_btn and user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Get AI response
        with st.spinner("Thinking..."):
            response = chat_with_claude(client, st.session_state.messages[:-1], user_input)
            st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

    # Chat management buttons
    if st.session_state.messages:
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📥 Archive Chat", key="archive_chat", use_container_width=True):
                # Create archive entry
                first_msg = st.session_state.messages[0]["content"] if st.session_state.messages else "Empty chat"
                title = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg

                archive_entry = {
                    "id": len(st.session_state.archived_chats),
                    "title": title,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "messages": st.session_state.messages.copy()
                }
                st.session_state.archived_chats.insert(0, archive_entry)  # Add to front
                st.session_state.messages = []
                st.toast("Chat archived!", icon="✅")
                st.rerun()

        with col2:
            if st.button("🗑️ Clear Chat", key="clear_chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()

    # Sidebar with data summary and archives
    with st.sidebar:
        st.markdown("### 📊 Data Available")

        stats = get_database_stats()
        st.markdown(f"""
        - **NIL Players:** {stats.get('nil_valuations', 0):,}
        - **Portal Entries:** {stats.get('portal_players', 0):,}
        - **Teams:** {stats.get('schools', 0)}
        """)

        st.divider()

        st.markdown("### 💡 Example Questions")
        st.markdown("""
        - "Who has the highest NIL value?"
        - "Tell me about [Player Name]"
        - "Best portal pickups for LSU?"
        - "Compare QB NIL values"
        - "Which 5-stars are in the portal?"
        """)

        # Archived chats section
        if st.session_state.archived_chats:
            st.divider()
            st.markdown("### 📁 Archived Chats")

            for i, archive in enumerate(st.session_state.archived_chats):
                with st.expander(f"📄 {archive['title'][:30]}...", expanded=False):
                    st.caption(f"Saved: {archive['timestamp']}")
                    st.caption(f"{len(archive['messages'])} messages")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("↩️ Restore", key=f"restore_{i}", use_container_width=True):
                            # Archive current chat first if it has messages
                            if st.session_state.messages:
                                first_msg = st.session_state.messages[0]["content"]
                                title = first_msg[:50] + "..." if len(first_msg) > 50 else first_msg
                                current_archive = {
                                    "id": len(st.session_state.archived_chats),
                                    "title": title,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "messages": st.session_state.messages.copy()
                                }
                                st.session_state.archived_chats.insert(0, current_archive)

                            # Restore selected chat
                            st.session_state.messages = archive['messages'].copy()
                            # Remove from archives
                            st.session_state.archived_chats = [
                                a for j, a in enumerate(st.session_state.archived_chats)
                                if j != i + (1 if st.session_state.messages else 0)
                            ]
                            st.toast("Chat restored!", icon="✅")
                            st.rerun()

                    with col2:
                        if st.button("🗑️ Delete", key=f"delete_{i}", use_container_width=True):
                            st.session_state.archived_chats = [
                                a for j, a in enumerate(st.session_state.archived_chats)
                                if j != i
                            ]
                            st.toast("Archive deleted", icon="🗑️")
                            st.rerun()

            # Clear all archives button
            if len(st.session_state.archived_chats) > 1:
                st.divider()
                if st.button("🗑️ Clear All Archives", key="clear_all_archives"):
                    st.session_state.archived_chats = []
                    st.toast("All archives cleared", icon="🗑️")
                    st.rerun()


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    main()
else:
    main()
