"""
Data Import Page

Bulk import player stats and penalties from PFF, manual entry, or CSV files.
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
    <h1 style="color: {COLORS['primary']};">📥 PFF & Advanced Data Import</h1>
    <p style="color: {COLORS['text_secondary']};">
        Import metrics that <strong>cannot be auto-pulled</strong> from CFBD:
    </p>
    <ul style="color: {COLORS['text_secondary']};">
        <li><strong>PFF Grades</strong> - Overall, Pass Block, Run Block, Coverage, Pass Rush</li>
        <li><strong>Pressures/Hurries</strong> - OL pressures allowed, DL pressures generated</li>
        <li><strong>Missed Tackles</strong> - Defensive reliability</li>
        <li><strong>Snap Counts</strong> - Playing time context</li>
        <li><strong>Coverage Stats</strong> - Targets, completions allowed, passer rating against</li>
    </ul>
    <p style="color: #7a8fa6; font-size: 0.85rem;">
        Note: Basic stats (pass/rush/rec yards, tackles, sacks) are auto-pulled from CFBD.
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 PFF Bulk Import",
        "✏️ Manual Entry",
        "📁 CSV Upload",
        "👁️ View Data"
    ])

    # =========================================================================
    # TAB 1: PFF BULK IMPORT
    # =========================================================================
    with tab1:
        st.markdown("### Import from PFF")
        st.markdown("""
        Copy data from PFF and paste below. Expected format (tab or comma separated):

        ```
        Player Name, Team, Position, Overall Grade, Pass Block, Run Block, Sacks Allowed, Pressures, Penalties
        ```
        """)

        col1, col2 = st.columns([3, 1])

        with col1:
            pff_data = st.text_area(
                "Paste PFF Data",
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

        if st.button("🔄 Parse & Preview PFF Data", key="parse_pff"):
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
            st.markdown("**PFF Grades (0-100)**")
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
        st.markdown("### Upload PFF CSV Export")

        st.markdown(f"""
        <div style="background: #1a2332; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="color: {COLORS['primary']}; margin-top: 0;">PFF Premium Export Support</h4>
            <p style="color: {COLORS['text_secondary']}; font-size: 0.9rem;">
                Upload CSV exports directly from PFF Premium. Column names are automatically mapped.
            </p>
            <p style="color: #7a8fa6; font-size: 0.85rem;">
                <strong>How to export from PFF:</strong> Go to team grades page → Export → Download CSV
            </p>
        </div>
        """, unsafe_allow_html=True)

        # PFF column mapping (PFF export names -> our internal names)
        PFF_COLUMN_MAP = {
            # Player identity
            "player": "player_name",
            "player_name": "player_name",
            "name": "player_name",
            "full_name": "player_name",
            "team": "team",
            "school": "team",
            "team_name": "team",
            "position": "position",
            "pos": "position",

            # Overall grades
            "overall": "pff_overall",
            "overall_grade": "pff_overall",
            "pff_grade": "pff_overall",
            "grade": "pff_overall",
            "offense": "pff_offense",
            "offense_grade": "pff_offense",
            "defense": "pff_defense",
            "defense_grade": "pff_defense",

            # Offensive grades
            "pass_block": "pff_pass_block",
            "pass_block_grade": "pff_pass_block",
            "pbk": "pff_pass_block",
            "run_block": "pff_run_block",
            "run_block_grade": "pff_run_block",
            "rbk": "pff_run_block",
            "receiving": "pff_receiving",
            "receiving_grade": "pff_receiving",
            "recv": "pff_receiving",
            "rushing": "pff_rushing",
            "rushing_grade": "pff_rushing",
            "rush": "pff_rushing",
            "passing": "pff_passing",
            "passing_grade": "pff_passing",

            # Defensive grades
            "pass_rush": "pff_pass_rush",
            "pass_rush_grade": "pff_pass_rush",
            "prs": "pff_pass_rush",
            "run_defense": "pff_run_defense",
            "run_def": "pff_run_defense",
            "rdef": "pff_run_defense",
            "coverage": "pff_coverage",
            "coverage_grade": "pff_coverage",
            "cov": "pff_coverage",
            "tackling": "pff_tackling",
            "tackling_grade": "pff_tackling",
            "tack": "pff_tackling",

            # Snap counts
            "snaps": "total_snaps",
            "total_snaps": "total_snaps",
            "snap_count": "total_snaps",
            "snap_counts": "total_snaps",
            "pass_snaps": "pass_snaps",
            "run_snaps": "run_snaps",

            # Advanced metrics - pass rush
            "pressures": "pressures",
            "pressure": "pressures",
            "hurries": "hurries",
            "hurry": "hurries",
            "hits": "hits",
            "qb_hits": "hits",

            # Advanced metrics - OL
            "pressures_allowed": "pressures_allowed",
            "pres_allowed": "pressures_allowed",
            "sacks_allowed": "sacks_allowed",
            "sack_allowed": "sacks_allowed",

            # Advanced metrics - coverage
            "targets": "targets_allowed",
            "targets_allowed": "targets_allowed",
            "tgt": "targets_allowed",
            "receptions_allowed": "completions_allowed",
            "catches_allowed": "completions_allowed",
            "completions_allowed": "completions_allowed",
            "yards_allowed": "yards_allowed",
            "yds_allowed": "yards_allowed",
            "tds_allowed": "tds_allowed",
            "touchdowns_allowed": "tds_allowed",

            # Tackling
            "missed_tackles": "missed_tackles",
            "missed_tkl": "missed_tackles",
            "mtkl": "missed_tackles",

            # Turnovers
            "interceptions": "ints",
            "ints": "ints",
            "int": "ints",
            "pass_breakups": "pbus",
            "pbu": "pbus",
            "pbus": "pbus",
            "forced_fumbles": "forced_fumbles",
            "ff": "forced_fumbles",
        }

        uploaded_file = st.file_uploader("Upload PFF CSV Export", type=["csv"], key="pff_csv_upload")

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
                preview_cols = ["player_name", "team", "position", "pff_overall", "pff_pass_block", "pff_run_block", "pff_coverage", "total_snaps"]
                preview_cols = [c for c in preview_cols if c in upload_df.columns]
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
                            st.success(f"Imported {len(upload_df)} PFF records!")
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
                st.markdown("- Try re-exporting from PFF")

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
