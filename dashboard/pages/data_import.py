"""
Data Import Page

Bulk import player stats, grades, and penalties from CSV files or manual entry.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.styling import apply_custom_css, COLORS
from utils.navigation import render_sidebar

# Page config
st.set_page_config(
    page_title="Data Import | Portal IQ",
    page_icon="📥",
    layout="wide",
)

apply_custom_css()

# Data directory
DATA_DIR = Path(__file__).parent.parent.parent / "ml-engine" / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MANUAL_STATS_FILE = DATA_DIR / "manual_player_stats.csv"


def load_existing_manual_stats() -> pd.DataFrame:
    """Load existing manually entered stats."""
    if MANUAL_STATS_FILE.exists():
        return pd.read_csv(MANUAL_STATS_FILE)
    return pd.DataFrame()


def save_manual_stats(df: pd.DataFrame):
    """Save manual stats to CSV."""
    df.to_csv(MANUAL_STATS_FILE, index=False)


def main():
    render_sidebar()

    st.markdown(f"""
    <h1 style="color: {COLORS['primary']};">📥 Advanced Analytics Import</h1>
    <p style="color: {COLORS['text_secondary']};">
        Import proprietary grades and advanced metrics:
    </p>
    <ul style="color: {COLORS['text_secondary']};">
        <li><strong>Player Grades</strong> - Overall, Pass Block, Run Block, Coverage, Pass Rush</li>
        <li><strong>Pressures/Hurries</strong> - OL pressures allowed, DL pressures generated</li>
        <li><strong>Missed Tackles</strong> - Defensive reliability</li>
        <li><strong>Snap Counts</strong> - Playing time context</li>
        <li><strong>Coverage Stats</strong> - Targets, completions allowed, passer rating against</li>
    </ul>
    <p style="color: #7a8fa6; font-size: 0.85rem;">
        Note: Basic stats are auto-pulled. Advanced grades power our proprietary valuations.
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Bulk Import",
        "✏️ Manual Entry",
        "📁 CSV Upload",
        "👁️ View Data"
    ])

    # =========================================================================
    # TAB 1: BULK IMPORT
    # =========================================================================
    with tab1:
        st.markdown("### Bulk Grade Import")
        st.markdown("""
        Paste player grades data below. Expected format (tab or comma separated):

        ```
        Player Name, Team, Position, Overall Grade, Pass Block, Run Block, Sacks Allowed, Pressures, Penalties
        ```
        """)

        col1, col2 = st.columns([3, 1])

        with col1:
            pff_data = st.text_area(
                "Paste Grade Data",
                height=300,
                placeholder="John Smith, Alabama, OT, 85.2, 82.1, 88.3, 2, 15, 3\nJane Doe, Ohio State, EDGE, 91.5, -, -, -, -, 1",
                key="pff_paste"
            )

        with col2:
            st.markdown("**Expected Columns:**")
            st.markdown("""
            - Player Name
            - Team
            - Position
            - Overall Grade
            - Pass Block Grade (OL)
            - Run Block Grade (OL)
            - Sacks Allowed (OL)
            - Pressures Allowed (OL)
            - Penalties
            - Pass Rush Grade (DL)
            - Run Defense Grade (DL)
            - Missed Tackles
            - Coverage Grade (DB)
            - TDs Allowed (DB)
            """)

        if st.button("🔄 Parse & Preview Data", key="parse_pff"):
            if pff_data.strip():
                try:
                    # Try to parse as CSV or TSV
                    lines = pff_data.strip().split("\n")
                    records = []

                    for line in lines:
                        # Handle both comma and tab separated
                        if "\t" in line:
                            parts = [p.strip() for p in line.split("\t")]
                        else:
                            parts = [p.strip() for p in line.split(",")]

                        if len(parts) >= 4:
                            record = {
                                "player_name": parts[0],
                                "team": parts[1] if len(parts) > 1 else "",
                                "position": parts[2] if len(parts) > 2 else "",
                                "pff_overall": float(parts[3]) if len(parts) > 3 and parts[3].replace(".", "").isdigit() else None,
                                "pff_pass_block": float(parts[4]) if len(parts) > 4 and parts[4].replace(".", "").isdigit() else None,
                                "pff_run_block": float(parts[5]) if len(parts) > 5 and parts[5].replace(".", "").isdigit() else None,
                                "sacks_allowed": int(parts[6]) if len(parts) > 6 and parts[6].isdigit() else 0,
                                "pressures_allowed": int(parts[7]) if len(parts) > 7 and parts[7].isdigit() else 0,
                                "penalties": int(parts[8]) if len(parts) > 8 and parts[8].isdigit() else 0,
                            }
                            records.append(record)

                    if records:
                        preview_df = pd.DataFrame(records)
                        st.success(f"Parsed {len(records)} player records!")
                        st.dataframe(preview_df, use_container_width=True)

                        if st.button("💾 Save to Database", key="save_pff"):
                            existing = load_existing_manual_stats()
                            combined = pd.concat([existing, preview_df], ignore_index=True)
                            # Remove duplicates, keep latest
                            combined = combined.drop_duplicates(subset=["player_name", "team"], keep="last")
                            save_manual_stats(combined)
                            st.success(f"Saved {len(records)} records!")
                            st.rerun()
                    else:
                        st.warning("No valid records found. Check format.")

                except Exception as e:
                    st.error(f"Error parsing data: {e}")

    # =========================================================================
    # TAB 2: MANUAL ENTRY
    # =========================================================================
    with tab2:
        st.markdown("### Manual Player Entry")

        col1, col2, col3 = st.columns(3)

        with col1:
            player_name = st.text_input("Player Name", key="manual_name")
            team = st.text_input("Team", key="manual_team")
            position = st.selectbox("Position", [
                "QB", "RB", "WR", "TE", "OT", "OG", "C",
                "EDGE", "DT", "LB", "CB", "S", "K", "P"
            ], key="manual_pos")

        with col2:
            st.markdown("**Player Grades (0-100)**")
            pff_overall = st.number_input("Overall Grade", 0.0, 100.0, 0.0, key="manual_pff")
            pff_pass = st.number_input("Pass Grade", 0.0, 100.0, 0.0, key="manual_pass_grade")
            pff_run = st.number_input("Run Grade", 0.0, 100.0, 0.0, key="manual_run_grade")

        with col3:
            st.markdown("**Accountability Metrics**")
            penalties = st.number_input("Total Penalties", 0, 50, 0, key="manual_penalties")
            missed_tackles = st.number_input("Missed Tackles", 0, 50, 0, key="manual_missed")

            if position in ["OT", "OG", "C"]:
                sacks_allowed = st.number_input("Sacks Allowed", 0, 30, 0, key="manual_sacks_allowed")
                pressures = st.number_input("Pressures Allowed", 0, 100, 0, key="manual_pressures")
            elif position in ["EDGE", "DT", "LB"]:
                offsides = st.number_input("Offsides Penalties", 0, 20, 0, key="manual_offsides")
                roughing = st.number_input("Roughing Passer", 0, 10, 0, key="manual_roughing")
            elif position in ["CB", "S"]:
                pi_calls = st.number_input("Pass Interference", 0, 20, 0, key="manual_pi")
                tds_allowed = st.number_input("TDs Allowed", 0, 20, 0, key="manual_tds_allowed")

        if st.button("➕ Add Player", key="add_manual"):
            if player_name and team:
                new_record = {
                    "player_name": player_name,
                    "team": team,
                    "position": position,
                    "pff_overall": pff_overall if pff_overall > 0 else None,
                    "pff_pass_grade": pff_pass if pff_pass > 0 else None,
                    "pff_run_grade": pff_run if pff_run > 0 else None,
                    "penalties": penalties,
                    "missed_tackles": missed_tackles,
                }

                # Position-specific fields
                if position in ["OT", "OG", "C"]:
                    new_record["sacks_allowed"] = sacks_allowed
                    new_record["pressures_allowed"] = pressures
                elif position in ["EDGE", "DT", "LB"]:
                    new_record["offsides_penalties"] = offsides
                    new_record["roughing_passer"] = roughing
                elif position in ["CB", "S"]:
                    new_record["pass_interference"] = pi_calls
                    new_record["tds_allowed"] = tds_allowed

                existing = load_existing_manual_stats()
                new_df = pd.DataFrame([new_record])
                combined = pd.concat([existing, new_df], ignore_index=True)
                combined = combined.drop_duplicates(subset=["player_name", "team"], keep="last")
                save_manual_stats(combined)

                st.success(f"Added {player_name}!")
                st.rerun()
            else:
                st.warning("Player name and team required.")

    # =========================================================================
    # TAB 3: CSV UPLOAD (PFF Export Support)
    # =========================================================================
    with tab3:
        st.markdown("### Upload Advanced Stats CSV")

        # Check if merged PFF file exists
        PFF_GRADES_FILE = DATA_DIR / "pff_player_grades.csv"

        if PFF_GRADES_FILE.exists():
            pff_df = pd.read_csv(PFF_GRADES_FILE)
            seasons = sorted(pff_df["season"].dropna().unique()) if "season" in pff_df.columns else []
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a472a 0%, #2d5a3d 100%); padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #3d7a4d;">
                <h4 style="color: #4ade80; margin-top: 0;">✓ Proprietary Grades Database Available</h4>
                <p style="color: #a7f3d0; font-size: 0.9rem; margin-bottom: 10px;">
                    <strong>{len(pff_df):,} players</strong> with advanced grades across seasons: {', '.join(map(str, seasons))}
                </p>
                <p style="color: #86efac; font-size: 0.85rem; margin: 0;">
                    This data is automatically merged into player valuations. No import needed!
                </p>
            </div>
            """, unsafe_allow_html=True)

            # Show sample of the merged data
            with st.expander("Preview Grades Database", expanded=False):
                preview_cols = [c for c in ["name", "team", "position", "season", "pff_overall",
                                            "pff_offense", "pff_defense", "pff_passing", "pff_rushing",
                                            "pff_receiving", "pff_pass_block", "pff_run_block",
                                            "pff_pass_rush", "pff_coverage"] if c in pff_df.columns]
                st.dataframe(pff_df[preview_cols].head(50), use_container_width=True)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Players", f"{len(pff_df):,}")
                with col2:
                    st.metric("Columns", f"{len(pff_df.columns)}")
                with col3:
                    st.metric("Seasons", len(seasons))

            st.markdown("---")

        st.markdown(f"""
        <div style="background: #1a2332; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="color: {COLORS['primary']}; margin-top: 0;">Advanced Stats CSV Import</h4>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                Upload CSV exports with player grades. <strong>200+ column variations</strong> are automatically mapped.
            </p>
            <p style="color: #7a8fa6; font-size: 0.85rem;">
                Supports grades, snap counts, advanced metrics, and efficiency stats.
            </p>
        </div>
        <div style="background: #141c28; padding: 12px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: {COLORS['accent']}; font-size: 0.85rem; margin: 0;"><strong>Supported Reports by Position:</strong></p>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 8px; font-size: 0.8rem; color: {COLORS['text_secondary']};">
                <div><strong>QB:</strong> Passing Grades, Depth, Pressure, Time in Pocket, Adj Comp%</div>
                <div><strong>RB:</strong> Rushing Grades, Elusive Rating, Breakaway%, YAC</div>
                <div><strong>WR/TE:</strong> Receiving Grades, YPRR, Drop Rate, Separation</div>
                <div><strong>OL:</strong> Pass Block, Run Block, PBE, Pressures Allowed</div>
                <div><strong>DL/EDGE:</strong> Pass Rush, Run Defense, PRP, Win Rate</div>
                <div><strong>LB/DB:</strong> Coverage, Tackling, Run Stop%, Passer Rating Allowed</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # PFF column mapping (PFF Premium Stats export names -> our internal names)
        # Covers all position reports: QB, RB, WR, TE, OL, DI, ED, LB, CB, S, K/P/ST
        # UPDATED: Now includes actual PFF CSV export column names (grades_offense, btt_rate, etc.)
        PFF_COLUMN_MAP = {
            # =====================================================================
            # PLAYER IDENTITY (actual PFF export format)
            # =====================================================================
            "player": "player_name",
            "player_name": "player_name",
            "name": "player_name",
            "full_name": "player_name",
            "first_name": "first_name",
            "last_name": "last_name",
            "player_id": "pff_id",
            "pff_id": "pff_id",
            "team": "team",
            "school": "team",
            "team_name": "team",
            "position": "position",
            "pos": "position",
            "jersey": "jersey_number",
            "jersey_number": "jersey_number",
            "number": "jersey_number",
            "year": "class_year",
            "class": "class_year",
            "eligibility": "eligibility",
            "player_game_count": "games_played",
            "games_played": "games_played",
            "games": "games_played",

            # =====================================================================
            # OVERALL GRADES (0-100) - includes actual PFF export format
            # =====================================================================
            "overall": "pff_overall",
            "overall_grade": "pff_overall",
            "pff_grade": "pff_overall",
            "pff_overall": "pff_overall",
            "grade": "pff_overall",
            "offense": "pff_offense",
            "offense_grade": "pff_offense",
            "grades_offense": "pff_offense",  # Actual PFF export
            "off": "pff_offense",
            "defense": "pff_defense",
            "defense_grade": "pff_defense",
            "grades_defense": "pff_defense",  # Actual PFF export
            "def": "pff_defense",

            # =====================================================================
            # SNAP COUNTS
            # =====================================================================
            "snaps": "total_snaps",
            "total_snaps": "total_snaps",
            "snap_count": "total_snaps",
            "snap_counts": "total_snaps",
            "pass_snaps": "pass_snaps",
            "pass_snap": "pass_snaps",
            "pass_plays": "pass_snaps",
            "run_snaps": "run_snaps",
            "run_snap": "run_snaps",
            "run_plays": "run_snaps",
            "coverage_snaps": "coverage_snaps",
            "pass_rush_snaps": "pass_rush_snaps",
            "routes_run": "routes_run",
            "route_snaps": "routes_run",
            "pass_block_snaps": "pass_block_snaps",
            "run_block_snaps": "run_block_snaps",

            # =====================================================================
            # OFFENSIVE LINE GRADES & METRICS - includes actual PFF export format
            # =====================================================================
            "pass_block": "pff_pass_block",
            "pass_block_grade": "pff_pass_block",
            "pass_blocking": "pff_pass_block",
            "pass_blocking_grade": "pff_pass_block",
            "grades_pass_block": "pff_pass_block",  # Actual PFF export
            "pbk": "pff_pass_block",
            "pblk": "pff_pass_block",
            "run_block": "pff_run_block",
            "run_block_grade": "pff_run_block",
            "run_blocking": "pff_run_block",
            "run_blocking_grade": "pff_run_block",
            "grades_run_block": "pff_run_block",  # Actual PFF export
            "rbk": "pff_run_block",
            "rblk": "pff_run_block",
            # OL Efficiency Metrics
            "pass_blocking_efficiency": "pass_blocking_efficiency",
            "pbe": "pass_blocking_efficiency",
            "pass_block_efficiency": "pass_blocking_efficiency",
            "pressures_allowed": "pressures_allowed",
            "pres_allowed": "pressures_allowed",
            "pressure_allowed": "pressures_allowed",
            "sacks_allowed": "sacks_allowed",
            "sack_allowed": "sacks_allowed",
            "hurries_allowed": "hurries_allowed",
            "hits_allowed": "hits_allowed",
            "penalties": "penalties",
            "declined_penalties": "declined_penalties",
            "holding_penalties": "holding_penalties",
            "false_starts": "false_starts",
            "block_percent": "block_percent",
            "non_spike_pass_block": "non_spike_pass_blocks",
            "snap_counts_block": "block_snaps",
            "snap_counts_lt": "snaps_lt",
            "snap_counts_lg": "snaps_lg",
            "snap_counts_c": "snaps_c",
            "snap_counts_rg": "snaps_rg",
            "snap_counts_rt": "snaps_rt",

            # =====================================================================
            # QB GRADES & METRICS (Passing) - includes actual PFF export format
            # =====================================================================
            "passing": "pff_passing",
            "passing_grade": "pff_passing",
            "grades_pass": "pff_passing",  # Actual PFF export
            "pass": "pff_passing",
            # Passing Depth
            "deep_passing": "pff_deep_passing",
            "deep_passing_grade": "pff_deep_passing",
            "intermediate_passing": "pff_intermediate_passing",
            "short_passing": "pff_short_passing",
            # Passing Pressure
            "under_pressure": "pff_under_pressure",
            "under_pressure_grade": "pff_under_pressure",
            "clean_pocket": "pff_clean_pocket",
            "clean_pocket_grade": "pff_clean_pocket",
            # Passing Advanced - actual PFF export names
            "adjusted_completion_pct": "adjusted_completion_pct",
            "adjusted_comp_pct": "adjusted_completion_pct",
            "accuracy_percent": "adjusted_completion_pct",  # Actual PFF export
            "adj_comp": "adjusted_completion_pct",
            "time_in_pocket": "time_in_pocket",
            "time_to_throw": "time_to_throw",
            "avg_time_to_throw": "time_to_throw",
            "avg_depth_of_target": "avg_depth_of_target",
            "big_time_throws": "big_time_throws",
            "btt": "big_time_throws",
            "big_time_throw_pct": "big_time_throw_pct",
            "btt_rate": "big_time_throw_pct",  # Actual PFF export
            "turnover_worthy_plays": "turnover_worthy_plays",
            "twp": "turnover_worthy_plays",
            "turnover_worthy_play_pct": "turnover_worthy_play_pct",
            "twp_rate": "turnover_worthy_play_pct",  # Actual PFF export
            "twp_pct": "turnover_worthy_play_pct",
            "passer_rating": "passer_rating",
            "qb_rating": "passer_rating",
            "completion_percent": "completion_pct",
            "sack_percent": "sack_pct",
            "scrambles": "scrambles",
            "dropbacks": "dropbacks",
            "aimed_passes": "aimed_passes",
            "thrown_aways": "thrown_aways",
            "spikes": "spikes",
            "hit_as_threw": "hit_as_threw",
            "bats": "batted_passes",

            # =====================================================================
            # RB GRADES & METRICS (Rushing) - includes actual PFF export format
            # =====================================================================
            "rushing": "pff_rushing",
            "rushing_grade": "pff_rushing",
            "grades_run": "pff_rushing",  # Actual PFF export
            "rush": "pff_rushing",
            "run": "pff_rushing",
            # Rushing Advanced - actual PFF export names
            "elusive_rating": "elusive_rating",
            "elusive": "elusive_rating",
            "elusiveness": "elusive_rating",
            "breakaway_pct": "breakaway_pct",
            "breakaway_percent": "breakaway_pct",  # Actual PFF export
            "breakaway_percentage": "breakaway_pct",
            "breakaway_runs": "breakaway_runs",
            "breakaway_yards": "breakaway_yards",
            "breakaway_attempts": "breakaway_attempts",
            "yards_after_contact": "yards_after_contact",
            "yac": "yards_after_contact",
            "yaco": "yards_after_contact",
            "elu_yco": "yards_after_contact",  # Actual PFF export
            "yards_after_contact_per_attempt": "yaco_per_attempt",
            "yaco_per_att": "yaco_per_attempt",
            "yco_attempt": "yaco_per_attempt",  # Actual PFF export
            "missed_tackles_forced": "missed_tackles_forced",
            "avoided_tackles": "missed_tackles_forced",  # Actual PFF export
            "elu_rush_mtf": "missed_tackles_forced",  # Actual PFF export
            "mtf": "missed_tackles_forced",
            "attempts": "rush_attempts",
            "rush_attempts": "rush_attempts",
            "carries": "rush_attempts",
            "gap_attempts": "gap_attempts",
            "zone_attempts": "zone_attempts",
            "designed_yards": "designed_yards",
            "explosive_runs": "explosive_runs",
            "explosive": "explosive_runs",
            "explosive_run_pct": "explosive_run_pct",
            "ypa": "yards_per_attempt",
            "grades_hands_fumble": "fumble_grade",

            # =====================================================================
            # WR/TE GRADES & METRICS (Receiving) - includes actual PFF export format
            # =====================================================================
            "receiving": "pff_receiving",
            "receiving_grade": "pff_receiving",
            "grades_pass_route": "pff_receiving",  # Actual PFF export
            "recv": "pff_receiving",
            # Receiving Depth
            "deep_receiving": "pff_deep_receiving",
            "intermediate_receiving": "pff_intermediate_receiving",
            "short_receiving": "pff_short_receiving",
            # Receiving Advanced - actual PFF export names
            "yards_per_route_run": "yards_per_route_run",
            "yprr": "yards_per_route_run",
            "ypt": "yards_per_route_run",
            "drop_rate": "drop_rate",
            "drops": "drops",
            "drop": "drops",
            "drop_pct": "drop_rate",
            "grades_hands_drop": "drop_grade",  # Actual PFF export
            "contested_catch_rate": "contested_catch_rate",
            "contested_catches": "contested_catches",
            "contested_receptions": "contested_catches",  # Actual PFF export
            "contested_targets": "contested_targets",
            "separation": "separation",
            "avg_separation": "separation",
            "targets": "targets",
            "tgt": "targets",
            "receptions": "receptions",
            "rec": "receptions",
            "catch_rate": "catch_rate",
            "catch_pct": "catch_rate",
            "caught_percent": "catch_rate",  # Actual PFF export
            "yards_after_catch": "yards_after_catch",
            "yards_after_catch_per_reception": "yac_per_reception",
            "yac_receiving": "yards_after_catch",
            "elu_recv_mtf": "recv_missed_tackles_forced",  # Actual PFF export
            "explosive_plays": "explosive_plays",
            "longest": "longest_reception",
            "first_downs": "first_downs",
            "route_rate": "route_rate",
            "routes": "routes_run",
            "inline_rate": "inline_rate",
            "inline_snaps": "inline_snaps",
            "slot_rate": "slot_rate",
            "slot_snaps": "slot_snaps",
            "wide_rate": "wide_rate",
            "wide_snaps": "wide_snaps",
            "targeted_qb_rating": "targeted_qb_rating",

            # =====================================================================
            # DEFENSIVE LINE / EDGE GRADES & METRICS (Pass Rush) - actual PFF export
            # =====================================================================
            "pass_rush": "pff_pass_rush",
            "pass_rush_grade": "pff_pass_rush",
            "pass_rushing": "pff_pass_rush",
            "grades_pass_rush_defense": "pff_pass_rush",  # Actual PFF export
            "prs": "pff_pass_rush",
            "prsh": "pff_pass_rush",
            # Pass Rush Productivity - actual PFF export names
            "pass_rushing_productivity": "pass_rushing_productivity",
            "prp": "pass_rushing_productivity",
            "pass_rush_productivity": "pass_rushing_productivity",
            "pressures": "pressures",
            "pressure": "pressures",
            "total_pressures": "pressures",
            "sacks": "sacks",
            "sack": "sacks",
            "hurries": "hurries",
            "hurry": "hurries",
            "hits": "hits",
            "qb_hits": "hits",
            "batted_passes": "batted_passes",
            "batted_balls": "batted_passes",
            "pressure_rate": "pressure_rate",
            "pres_rate": "pressure_rate",
            "pass_rush_percent": "pass_rush_percent",
            "win_rate": "pass_rush_win_rate",
            "pass_rush_win_rate": "pass_rush_win_rate",
            "pass_rush_wins": "pass_rush_wins",
            "prwr": "pass_rush_win_rate",
            "pass_rush_opp": "pass_rush_opportunities",
            # True pass set metrics (actual PFF export)
            "true_pass_set_grades_pass_rush_defense": "true_pass_set_grade",
            "true_pass_set_prp": "true_pass_set_prp",
            "true_pass_set_pass_rush_win_rate": "true_pass_set_win_rate",
            "true_pass_set_total_pressures": "true_pass_set_pressures",
            "true_pass_set_sacks": "true_pass_set_sacks",
            "true_pass_set_hurries": "true_pass_set_hurries",
            "true_pass_set_hits": "true_pass_set_hits",

            # =====================================================================
            # RUN DEFENSE GRADES & METRICS - actual PFF export format
            # =====================================================================
            "run_defense": "pff_run_defense",
            "run_defense_grade": "pff_run_defense",
            "grades_run_defense": "pff_run_defense",  # Actual PFF export
            "run_def": "pff_run_defense",
            "rdef": "pff_run_defense",
            "run_stop_pct": "run_stop_pct",
            "run_stop_percentage": "run_stop_pct",
            "rsp": "run_stop_pct",
            "run_stops": "run_stops",
            "stop": "run_stops",
            "stops": "run_stops",
            "tackles": "tackles",
            "tkl": "tackles",
            "solo_tackles": "solo_tackles",
            "assisted_tackles": "assisted_tackles",
            "assists": "assisted_tackles",  # Actual PFF export
            "tackles_for_loss": "tackles_for_loss",
            "tfl": "tackles_for_loss",
            # Snap count locations (actual PFF export)
            "snap_counts_defense": "defensive_snaps",
            "snap_counts_dl": "dl_snaps",
            "snap_counts_dl_a_gap": "dl_a_gap_snaps",
            "snap_counts_dl_b_gap": "dl_b_gap_snaps",
            "snap_counts_dl_outside_t": "dl_outside_t_snaps",
            "snap_counts_dl_over_t": "dl_over_t_snaps",
            "snap_counts_offball": "offball_snaps",
            "snap_counts_box": "box_snaps",
            "snap_counts_fs": "fs_snaps",
            "snap_counts_corner": "corner_snaps",
            "snap_counts_slot": "slot_snaps",

            # =====================================================================
            # COVERAGE GRADES & METRICS (DB/LB) - actual PFF export format
            # =====================================================================
            "coverage": "pff_coverage",
            "coverage_grade": "pff_coverage",
            "grades_coverage_defense": "pff_coverage",  # Actual PFF export
            "cov": "pff_coverage",
            # Slot Coverage
            "slot_coverage": "pff_slot_coverage",
            "slot_coverage_grade": "pff_slot_coverage",
            "slot": "pff_slot_coverage",
            # Outside Coverage
            "outside_coverage": "pff_outside_coverage",
            # Zone vs Man
            "zone_coverage": "pff_zone_coverage",
            "zone_coverage_grade": "pff_zone_coverage",
            "man_coverage": "pff_man_coverage",
            "man_coverage_grade": "pff_man_coverage",
            # Coverage Advanced - actual PFF export names
            "targets_allowed": "targets_allowed",
            "target": "targets_allowed",
            "receptions_allowed": "completions_allowed",
            "catches_allowed": "completions_allowed",
            "completions_allowed": "completions_allowed",
            "comp_allowed": "completions_allowed",
            "yards_allowed": "yards_allowed",
            "yds_allowed": "yards_allowed",
            "yards": "yards_allowed",
            "tds_allowed": "tds_allowed",
            "touchdowns_allowed": "tds_allowed",
            "touchdowns": "tds_allowed",  # In coverage context
            "td_allowed": "tds_allowed",
            "passer_rating_allowed": "passer_rating_allowed",
            "passer_rating_against": "passer_rating_allowed",
            "qb_rating_against": "passer_rating_allowed",  # Actual PFF export
            "qbr_allowed": "passer_rating_allowed",
            "yards_per_coverage_snap": "yards_per_coverage_snap",
            "ypcs": "yards_per_coverage_snap",
            "yards_allowed_per_coverage_snap": "yards_per_coverage_snap",
            "catch_rate_allowed": "catch_rate_allowed",
            "catch_rate": "catch_rate_allowed",  # In coverage context
            "completion_pct_allowed": "catch_rate_allowed",
            "tight_window_pct": "tight_window_pct",
            # Additional coverage metrics (actual PFF export)
            "coverage_snaps_per_reception": "coverage_snaps_per_reception",
            "coverage_snaps_per_target": "coverage_snaps_per_target",
            "coverage_percent": "coverage_percent",
            "avg_depth_of_target": "coverage_avg_depth",
            "dropped_ints": "dropped_ints",
            "forced_incompletes": "forced_incompletes",
            "forced_incompletion_rate": "forced_incompletion_rate",
            "snap_counts_coverage": "coverage_snaps",
            "snap_counts_pass_play": "pass_play_snaps",
            "snap_counts_run_defense": "run_defense_snaps",
            "snap_counts_pass_rush": "pass_rush_snaps",

            # =====================================================================
            # TACKLING GRADES & METRICS - actual PFF export format
            # =====================================================================
            "tackling": "pff_tackling",
            "tackling_grade": "pff_tackling",
            "grades_tackle": "pff_tackling",  # Actual PFF export
            "tack": "pff_tackling",
            "missed_tackles": "missed_tackles",
            "missed_tkl": "missed_tackles",
            "mtkl": "missed_tackles",
            "missed_tackle_pct": "missed_tackle_pct",
            "missed_tackle_rate": "missed_tackle_pct",  # Actual PFF export
            "tackle_efficiency": "tackle_efficiency",

            # =====================================================================
            # TURNOVER METRICS
            # =====================================================================
            "interceptions": "ints",
            "ints": "ints",
            "int": "ints",
            "pass_breakups": "pbus",
            "pbu": "pbus",
            "pbus": "pbus",
            "pass_break_ups": "pbus",
            "forced_fumbles": "forced_fumbles",
            "ff": "forced_fumbles",
            "fumble_recoveries": "fumble_recoveries",
            "fr": "fumble_recoveries",

            # =====================================================================
            # SPECIAL TEAMS
            # =====================================================================
            "kicking": "pff_kicking",
            "kicking_grade": "pff_kicking",
            "punting": "pff_punting",
            "punting_grade": "pff_punting",
            "kickoff": "pff_kickoff",
            "kickoff_grade": "pff_kickoff",
            "punt_return": "pff_punt_return",
            "kick_return": "pff_kick_return",
            "fg_pct": "field_goal_pct",
            "field_goal_pct": "field_goal_pct",
            "fg_made": "field_goals_made",
            "fg_attempts": "field_goal_attempts",
            "punt_avg": "punt_average",
            "punt_average": "punt_average",
            "hangtime": "hangtime",
            "inside_20": "punts_inside_20",

            # =====================================================================
            # SEASON/GAME CONTEXT
            # =====================================================================
            "season": "season",
            "year": "season",
            "week": "week",
            "game": "game",
            "opponent": "opponent",
            "opp": "opponent",
        }

        uploaded_file = st.file_uploader("Upload CSV with Player Grades", type=["csv"], key="pff_csv_upload")

        if uploaded_file:
            try:
                upload_df = pd.read_csv(uploaded_file)
                original_cols = list(upload_df.columns)

                # Normalize column names (lowercase, strip whitespace)
                upload_df.columns = [c.lower().strip().replace(" ", "_") for c in upload_df.columns]

                # Auto-map PFF columns to our format
                mapped_cols = {}
                unmapped_cols = []
                for col in upload_df.columns:
                    if col in PFF_COLUMN_MAP:
                        mapped_cols[col] = PFF_COLUMN_MAP[col]
                    else:
                        unmapped_cols.append(col)

                # Apply mapping
                upload_df = upload_df.rename(columns=mapped_cols)

                # Show mapping results
                st.success(f"Loaded {len(upload_df)} player records!")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Mapped Columns:**")
                    for orig, mapped in mapped_cols.items():
                        st.markdown(f"- `{orig}` → `{mapped}`")

                with col2:
                    if unmapped_cols:
                        st.markdown("**Unmapped (kept as-is):**")
                        for col in unmapped_cols[:10]:
                            st.markdown(f"- `{col}`")
                        if len(unmapped_cols) > 10:
                            st.markdown(f"- ... and {len(unmapped_cols) - 10} more")

                st.markdown("---")
                st.markdown("**Preview (first 20 rows):**")
                # Dynamic preview columns based on what's in the data
                priority_cols = [
                    # Identity
                    "player_name", "team", "position",
                    # Core grades
                    "pff_overall", "pff_offense", "pff_defense",
                    # OL
                    "pff_pass_block", "pff_run_block", "pass_blocking_efficiency", "pressures_allowed",
                    # Pass Rush
                    "pff_pass_rush", "pass_rushing_productivity", "pressures", "sacks",
                    # Coverage
                    "pff_coverage", "passer_rating_allowed", "targets_allowed", "yards_allowed",
                    # Run Defense
                    "pff_run_defense", "run_stop_pct", "tackles",
                    # QB
                    "pff_passing", "adjusted_completion_pct", "big_time_throws", "turnover_worthy_plays",
                    # RB
                    "pff_rushing", "elusive_rating", "yards_after_contact",
                    # WR/TE
                    "pff_receiving", "yards_per_route_run", "drop_rate",
                    # Tackling
                    "pff_tackling", "missed_tackles",
                    # Snaps
                    "total_snaps"
                ]
                preview_cols = [c for c in priority_cols if c in upload_df.columns]
                # Limit to 10 columns for readability
                preview_cols = preview_cols[:10] if len(preview_cols) > 10 else preview_cols
                st.dataframe(upload_df[preview_cols].head(20) if preview_cols else upload_df.head(20), use_container_width=True)

                # Check for required columns
                has_name = "player_name" in upload_df.columns
                has_team = "team" in upload_df.columns

                if not has_name:
                    st.warning("⚠️ No player name column detected. Please ensure CSV has 'player', 'name', or 'player_name' column.")

                if has_name:
                    import_col1, import_col2 = st.columns([1, 3])
                    with import_col1:
                        if st.button("💾 Import All Records", key="import_pff_csv", type="primary"):
                            existing = load_existing_manual_stats()
                            combined = pd.concat([existing, upload_df], ignore_index=True)

                            # Deduplicate - if team available use both, otherwise just name
                            if "team" in combined.columns:
                                combined = combined.drop_duplicates(subset=["player_name", "team"], keep="last")
                            else:
                                combined = combined.drop_duplicates(subset=["player_name"], keep="last")

                            save_manual_stats(combined)
                            st.success(f"Imported {len(upload_df)} player records!")
                            st.cache_data.clear()
                            st.rerun()

                    with import_col2:
                        st.markdown(f"""
                        <p style="color: #7a8fa6; font-size: 0.85rem; padding-top: 8px;">
                            Existing records for same player/team will be updated with new values.
                        </p>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error reading CSV: {e}")
                st.markdown("**Troubleshooting:**")
                st.markdown("- Ensure file is valid CSV format")
                st.markdown("- Check for special characters in column names")
                st.markdown("- Try re-exporting from your data source")

    # =========================================================================
    # TAB 4: VIEW DATA
    # =========================================================================
    with tab4:
        st.markdown("### Current Manual Stats Database")

        existing = load_existing_manual_stats()

        if not existing.empty:
            st.info(f"**{len(existing)} players** in manual database")

            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                pos_filter = st.multiselect("Filter by Position", existing["position"].unique() if "position" in existing.columns else [])
            with col2:
                team_filter = st.multiselect("Filter by Team", existing["team"].unique() if "team" in existing.columns else [])

            display_df = existing.copy()
            if pos_filter:
                display_df = display_df[display_df["position"].isin(pos_filter)]
            if team_filter:
                display_df = display_df[display_df["team"].isin(team_filter)]

            st.dataframe(display_df, use_container_width=True, height=400)

            # Delete options
            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                delete_player = st.selectbox(
                    "Select player to delete",
                    [""] + display_df["player_name"].tolist() if not display_df.empty else [""]
                )
                if delete_player and st.button("🗑️ Delete Player", key="delete_one"):
                    existing = existing[existing["player_name"] != delete_player]
                    save_manual_stats(existing)
                    st.success(f"Deleted {delete_player}")
                    st.rerun()

            with col2:
                if st.button("🗑️ Clear All Data", key="clear_all"):
                    if st.checkbox("Confirm clear all data"):
                        save_manual_stats(pd.DataFrame())
                        st.success("All data cleared!")
                        st.rerun()

            # Export
            st.markdown("---")
            csv_export = existing.to_csv(index=False)
            st.download_button(
                "📥 Export All Data as CSV",
                csv_export,
                "portal_iq_manual_stats.csv",
                "text/csv"
            )

        else:
            st.info("No manual stats entered yet. Use the tabs above to add data.")


if __name__ == "__main__":
    main()
