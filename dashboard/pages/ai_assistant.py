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
    get_database_stats, search_players, get_portal_players_with_measurables,
    get_positions, get_school_list
)
from utils.navigation import render_sidebar
from utils.win_impact_calculator import (
    calculate_player_war, calculate_team_portal_score, enrich_with_war,
    get_school_tier as get_school_tier_info  # Returns (tier_name, tier_data)
)
from utils.nil_estimator import (
    estimate_nil_value, get_tier_from_value,
    get_school_tier as get_school_tier_num  # Returns int (1-6)
)

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
    """Build comprehensive context string from ALL available data for the AI."""
    context_parts = []

    # Database stats
    stats = get_database_stats()
    context_parts.append(f"""
=== PORTAL IQ DATABASE OVERVIEW ===
- Total Players with NIL Values: {stats.get('nil_valuations', 0):,}
- Transfer Portal Entries: {stats.get('portal_players', 0):,}
- Teams Tracked: {stats.get('schools', 0)}
- Actual On3 NIL Values: {stats.get('actual_nil_values', 0):,}
- Predicted NIL Values: {stats.get('predicted_nil_values', 0):,}
- Last Updated: {stats.get('last_updated', 'Unknown')}
""")

    # Top NIL players with Portal IQ analysis
    nil_df = get_nil_players()
    if not nil_df.empty:
        # Enrich with WAR
        try:
            nil_df = enrich_with_war(nil_df, school_col="school")
        except Exception:
            nil_df["portaliq_war"] = 0

        top_nil = nil_df.nlargest(15, "nil_value")
        nil_list = []
        for _, row in top_nil.iterrows():
            war_val = row.get('portaliq_war', 0)
            confidence = row.get('valuation_source', 'Unknown')
            nil_list.append(
                f"  - {row['name']} ({row['position']}, {row.get('school', 'Unknown')}): "
                f"${row['nil_value']:,.0f} | WAR: {war_val:.2f} | Source: {confidence}"
            )
        context_parts.append(f"""
=== TOP 15 NIL VALUATIONS (with Portal IQ WAR) ===
{chr(10).join(nil_list)}
""")

        # Position breakdown
        position_stats = nil_df.groupby("position").agg({
            "nil_value": ["mean", "count"],
            "portaliq_war": "mean"
        }).round(2)
        position_stats.columns = ["avg_nil", "count", "avg_war"]
        position_stats = position_stats.sort_values("avg_nil", ascending=False)

        pos_list = []
        for pos, row in position_stats.head(10).iterrows():
            pos_list.append(f"  - {pos}: Avg NIL ${row['avg_nil']:,.0f}, Avg WAR {row['avg_war']:.2f}, Count: {int(row['count'])}")
        context_parts.append(f"""
=== POSITION MARKET ANALYSIS ===
{chr(10).join(pos_list)}
""")

    # Top portal classes with Portal IQ scoring
    team_df = get_team_rankings(year=2026)
    portal_df = get_portal_players(year=2026)

    if not team_df.empty:
        team_list = []
        for _, row in team_df.nlargest(15, "overall_score").iterrows():
            team_name = row['name']

            # Get incoming transfers for this team
            incoming = portal_df[
                portal_df["destination_school"].str.contains(str(team_name).split()[0], case=False, na=False) &
                (portal_df["status"] == "Committed")
            ] if not portal_df.empty else pd.DataFrame()

            tier, _ = get_school_tier_info(team_name)

            team_list.append(
                f"  - {team_name} ({tier}): On3 Score {row['overall_score']:.0f}, "
                f"Transfers In: {int(row.get('transfers_in', 0))}, "
                f"5★ Net: {int(row.get('five_stars_net', 0)):+d}, "
                f"4★ Net: {int(row.get('four_stars_net', 0)):+d}"
            )
        context_parts.append(f"""
=== TOP 15 PORTAL CLASSES (2026) ===
{chr(10).join(team_list)}
""")

    # Portal status and available players
    if not portal_df.empty:
        status_counts = portal_df["status"].value_counts().to_dict()

        # Get available players by position
        available = portal_df[portal_df["status"].isin(["Entered", "Expected"])]
        if not available.empty:
            avail_by_pos = available["position"].value_counts().head(8).to_dict()
            avail_pos_str = ", ".join([f"{pos}: {cnt}" for pos, cnt in avail_by_pos.items()])
        else:
            avail_pos_str = "N/A"

        context_parts.append(f"""
=== 2026 PORTAL STATUS ===
- Entered (Available): {status_counts.get('Entered', 0):,}
- Committed: {status_counts.get('Committed', 0):,}
- Expected: {status_counts.get('Expected', 0):,}
- Withdrawn: {status_counts.get('Withdrawn', 0):,}
Available by Position: {avail_pos_str}
""")

        # Top available players (not committed)
        available_with_nil = available[available.get("nil_value", available.get("portaliq_value", pd.Series(dtype=float))).notna()]
        if not available_with_nil.empty:
            top_available = available_with_nil.nlargest(10, "nil_value" if "nil_value" in available_with_nil.columns else "stars")
            avail_list = []
            for _, row in top_available.iterrows():
                stars = int(row.get('stars', 3)) if pd.notna(row.get('stars')) else 3
                nil_val = row.get('nil_value', row.get('portaliq_value', 0)) or 0
                avail_list.append(
                    f"  - {row['name']} ({row['position']}, {'⭐'*stars}) from {row.get('origin_school', 'Unknown')}: "
                    f"${nil_val:,.0f}"
                )
            context_parts.append(f"""
=== TOP 10 AVAILABLE PORTAL PLAYERS ===
{chr(10).join(avail_list)}
""")

    # School tier reference
    context_parts.append("""
=== SCHOOL TIER REFERENCE ===
Elite Tier (1.3x multiplier): Alabama, Georgia, Ohio State, Michigan, Texas, Oregon, Penn State, Notre Dame, USC, Clemson
Power Tier (1.15x): LSU, Oklahoma, Florida, Miami, Tennessee, Auburn, Texas A&M, Wisconsin, UCLA, Washington, Utah, Ole Miss
Rising Tier (1.0x): Colorado, Indiana, Illinois, Iowa State, Kansas State, Arizona, NC State, Virginia Tech
Developmental Tier (0.85x): All other schools
""")

    # WAR explanation for the AI
    context_parts.append("""
=== PORTAL IQ PROPRIETARY METRICS ===
WAR (Wins Above Replacement): Our proprietary player impact score based on:
- Position value & scarcity (QB highest at 3.0 base)
- Star rating multiplier (5★=2.0x, 4★=1.5x, 3★=1.0x)
- NIL market signal (higher NIL = market believes in value)
- School tier factor (elite schools maximize player potential)
- Physical measurables (height/weight fit for position)
- Experience factor (juniors typically peak)

NIL Confidence Levels:
- "On3 Actual" = Real On3 valuation data
- "Predicted" = Portal IQ proprietary estimate based on recruiting stars, position, school tier
""")

    return "\n".join(context_parts)


def get_player_info(player_name: str) -> str:
    """Get comprehensive info about a specific player including Portal IQ analysis."""
    results = search_players(player_name)
    if results.empty:
        return f"No player found matching '{player_name}'"

    info_parts = []
    for _, row in results.iterrows():
        source = row.get("data_source", "unknown")

        # Get school for tier lookup
        school = row.get('school', row.get('destination_school', row.get('origin_school', 'Unknown')))
        tier_name, tier_data = get_school_tier_info(school)

        # Calculate Portal IQ WAR - prefer transfer portal stars over HS recruiting
        stars_val = row.get('transfer_stars') or row.get('stars') or 3
        if pd.isna(stars_val):
            stars_val = 3

        war_result = calculate_player_war(
            position=row.get('position', 'ATH'),
            stars=stars_val,
            rating=row.get('overall_rating'),
            nil_value=row.get('nil_value', 0) or row.get('portaliq_value', 0),
            destination_school=school,
            height=row.get('height_inches'),
            weight=row.get('weight'),
            year=row.get('year'),
            is_predicted_nil=row.get('is_predicted', True)
        )

        # Calculate NIL estimate if not present
        nil_value = row.get('nil_value', 0) or 0
        if nil_value == 0:
            nil_estimate = estimate_nil_value(
                school_tier=tier_name,
                position=row.get('position', 'ATH'),
                stars=int(stars_val),
                rating=row.get('overall_rating')
            )
            nil_value = nil_estimate.get('value', 0)
            nil_confidence = nil_estimate.get('confidence', 'low')
        else:
            nil_confidence = "actual" if not row.get('is_predicted', True) else "predicted"

        info = f"""
=== PLAYER: {row['name']} ===
Basic Info:
- Position: {row.get('position', 'Unknown')}
- School: {school} ({tier_name} tier)
- Stars: {int(stars_val)}⭐
- Year: {row.get('year', 'Unknown')}

NIL Valuation:
- NIL Value: ${nil_value:,.0f}
- Confidence: {nil_confidence}
- NIL Tier: {get_tier_from_value(nil_value)}

Portal IQ Win Impact:
- WAR: {war_result['war']:.2f} (range: {war_result['war_low']:.2f} - {war_result['war_high']:.2f})
- WAR Confidence: {war_result['confidence']}

WAR Breakdown:
- Base Position WAR: {war_result['breakdown']['base_war']}
- Position Scarcity: ×{war_result['breakdown']['position_scarcity']}
- Star Multiplier: ×{war_result['breakdown']['star_multiplier']}
- School Multiplier: ×{war_result['breakdown']['school_multiplier']}
- NIL Market Bonus: +{war_result['breakdown']['nil_bonus']}
"""
        if source == "transfer_portal":
            info += f"""
Portal Status:
- Status: {row.get('status', 'Unknown')}
- From: {row.get('origin_school', 'Unknown')}
- To: {row.get('destination_school', 'TBD')}
"""
        info_parts.append(info)

    return "\n".join(info_parts[:3])  # Limit to top 3 matches


SYSTEM_PROMPT = """You are the Portal IQ AI Assistant, an elite expert on college football transfer portal and NIL (Name, Image, Likeness) valuations. You have access to Portal IQ's proprietary analytics and 17,500+ player database.

=== YOUR DATA ACCESS ===
1. NIL Valuations: Both actual On3 values AND Portal IQ's proprietary estimates
2. Portal IQ WAR: Our proprietary Wins Above Replacement metric for player impact
3. Transfer Portal: 14,000+ entries across 2024-2026 with status tracking
4. Team Rankings: Portal class scores, transfer counts, star distribution
5. School Tiers: Elite/Power/Rising/Developmental with multipliers
6. Player Measurables: Height, weight, year for position fit analysis

=== PORTAL IQ PROPRIETARY METRICS ===
**WAR (Wins Above Replacement)**: 0-15+ scale measuring projected wins a player adds
- Factors: Position value, star rating, NIL signal, school tier, measurables, experience
- QB highest base (3.0), EDGE rushers (1.5), RBs lower (0.9) due to replaceability

**NIL Confidence Levels**:
- "actual" = Real On3 valuation
- "predicted" = Portal IQ estimate based on our algorithm
- "high/medium/low" = Data completeness for prediction

**School Tiers** (affect both NIL and WAR):
- Elite (1.3x): Alabama, Georgia, Ohio State, Michigan, Texas, Oregon, etc.
- Power (1.15x): LSU, Oklahoma, Florida, Miami, Tennessee, etc.
- Rising (1.0x): Colorado, Indiana, Illinois, etc.
- Developmental (0.85x): All others

=== YOUR CAPABILITIES ===
1. Look up any player's NIL value, WAR, and full analytics breakdown
2. Analyze team portal classes with Portal IQ scoring
3. Explain WHY players have certain valuations (with factor breakdown)
4. Compare players, positions, and schools
5. Identify undervalued/overvalued players based on WAR vs NIL
6. Project transfer impact using school tier multipliers
7. Find available portal players by position, stars, or school

=== RESPONSE GUIDELINES ===
- Always cite specific numbers when available (NIL value, WAR, stars)
- Explain Portal IQ metrics when users ask about methodology
- Be direct and concise - users want actionable insights
- If data is missing, say so clearly and explain what we do have
- Use WAR to contextualize NIL value (high WAR + low NIL = undervalued)

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

    # Header - Portal IQ Ultra Modern Style
    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="width: 40px; height: 40px; background: {COLORS['primary']}; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(245, 191, 3, 0.2);">
                <span style="font-size: 1.25rem;">🤖</span>
            </div>
            <div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <h1 style="color: {COLORS['text_primary']}; margin: 0; font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em;">
                        AI Intelligence
                    </h1>
                    <div style="display: flex; align-items: center; gap: 6px; background: rgba(34, 197, 94, 0.15); padding: 4px 12px; border-radius: 50px; border: 1px solid rgba(34, 197, 94, 0.3);">
                        <div style="width: 8px; height: 8px; background: {COLORS['status_active']}; border-radius: 50%; animation: pulse 2s infinite;"></div>
                        <span style="color: {COLORS['status_active']}; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;">Live</span>
                    </div>
                </div>
                <p style="color: {COLORS['text_muted']}; font-size: 0.85rem; margin: 0;">
                    Natural language queries for players, NIL valuations, and portal intelligence
                </p>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: rgba(245, 191, 3, 0.1); border: 1px solid rgba(245, 191, 3, 0.3); padding: 6px 14px; border-radius: 50px;">
                <span style="color: {COLORS['primary']}; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Powered by Claude</span>
            </div>
        </div>
    </div>
    <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
    </style>
    """, unsafe_allow_html=True)

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

    # Quick actions - Modern chip style
    st.markdown(f"""
    <p style="color: {COLORS['text_muted']}; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 12px;">
        Quick Questions
    </p>
    """, unsafe_allow_html=True)

    quick_questions = [
        ("🏆 Top NIL Players", "Who are the top 5 highest NIL valued players right now?"),
        ("📊 Best Portal Classes", "Which teams have the best 2026 transfer portal classes?"),
        ("🎯 Available QBs", "What quarterbacks are currently available in the portal?"),
        ("📈 NIL Trends", "What are the current NIL market trends for college football?"),
    ]

    # Display as chips/pills
    st.markdown(f"""
    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    for i, (label, question) in enumerate(quick_questions):
        col = [col1, col2, col3, col4][i]
        with col:
            if st.button(label, key=f"quick_{i}", use_container_width=True):
                st.session_state.pending_question = question

    st.divider()

    # Chat container
    chat_container = st.container()

    # Display chat history with modern styling
    with chat_container:
        for message in st.session_state.messages:
            role = message["role"]
            content = message["content"]

            if role == "user":
                # User message - right aligned, gold background
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin: 16px 0;">
                    <div style="max-width: 80%;">
                        <div style="background: {COLORS['primary']}; color: {COLORS['bg_dark']}; padding: 16px 20px; border-radius: 20px; border-top-right-radius: 4px; box-shadow: 0 4px 12px rgba(245, 191, 3, 0.2);">
                            <p style="margin: 0; font-weight: 500;">{content}</p>
                        </div>
                        <p style="color: {COLORS['text_muted']}; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; text-align: right; margin: 6px 8px 0 0;">You</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # AI message - left aligned with gold accent
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; gap: 12px; margin: 16px 0;">
                    <div style="width: 40px; height: 40px; background: {COLORS['primary']}; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(245, 191, 3, 0.2); flex-shrink: 0;">
                        <span style="font-size: 1.1rem;">🤖</span>
                    </div>
                    <div style="max-width: 85%;">
                        <div style="background: {COLORS['bg_light']}; border: 1px solid {COLORS['border']}; padding: 20px 24px; border-radius: 20px; border-top-left-radius: 4px;">
                            <p style="margin: 0; color: {COLORS['text_secondary']}; line-height: 1.7;">{content}</p>
                        </div>
                        <p style="color: {COLORS['text_muted']}; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin: 6px 0 0 8px;">Portal IQ</p>
                    </div>
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

    # Chat input with modern styling
    st.markdown(f"""
    <p style="color: {COLORS['text_muted']}; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px;">
        Ask a Question
    </p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])

    with col1:
        user_input = st.text_input(
            "Your question",
            placeholder="Ask anything about the portal... (e.g., Tell me about Sam Leavitt's NIL value)",
            key="chat_input",
            label_visibility="collapsed"
        )

    with col2:
        send_btn = st.button("Send →", type="primary", use_container_width=True)

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
