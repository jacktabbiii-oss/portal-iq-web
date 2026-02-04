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
    # TAB 3: CSV UPLOAD
    # =========================================================================
    with tab3:
        st.markdown("### Upload CSV File")

        st.markdown("""
        Upload a CSV with player stats. Required columns: `player_name`, `team`, `position`

        Optional columns: `pff_overall`, `pff_pass_grade`, `pff_run_grade`, `penalties`,
        `sacks_allowed`, `pressures_allowed`, `missed_tackles`, `offsides_penalties`,
        `roughing_passer`, `pass_interference`, `tds_allowed`
        """)

        # Download template
        template_df = pd.DataFrame({
            "player_name": ["Example Player"],
            "team": ["Alabama"],
            "position": ["OT"],
            "pff_overall": [85.5],
            "pff_pass_grade": [82.0],
            "pff_run_grade": [88.0],
            "penalties": [3],
            "sacks_allowed": [2],
            "pressures_allowed": [15],
            "missed_tackles": [0],
        })

        csv_template = template_df.to_csv(index=False)
        st.download_button(
            "📄 Download Template CSV",
            csv_template,
            "pff_import_template.csv",
            "text/csv"
        )

        uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="csv_upload")

        if uploaded_file:
            try:
                upload_df = pd.read_csv(uploaded_file)
                st.success(f"Loaded {len(upload_df)} records!")
                st.dataframe(upload_df.head(20), use_container_width=True)

                if st.button("💾 Import All Records", key="import_csv"):
                    existing = load_existing_manual_stats()
                    combined = pd.concat([existing, upload_df], ignore_index=True)
                    combined = combined.drop_duplicates(subset=["player_name", "team"], keep="last")
                    save_manual_stats(combined)
                    st.success(f"Imported {len(upload_df)} records!")
                    st.rerun()

            except Exception as e:
                st.error(f"Error reading CSV: {e}")

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
