"""PFF Data Merger - Combines all PFF CSV exports into a single player grades file.

This script reads PFF CSV exports (passing, rushing, receiving, defense, blocking, etc.)
and merges them into a single pff_player_grades.csv with standardized column names.

Usage:
    python -m src.data_collection.pff_merger [input_dir] [output_path]

    Default input: parent of ml-engine (looks for 20*_*.csv files)
    Default output: ml-engine/data/processed/pff_player_grades.csv
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


# Column mapping from PFF export format to app expected format
COLUMN_MAPPING = {
    # Identity columns
    "player": "name",
    "team_name": "team",
    "position": "position",
    "player_id": "pff_id",
    "player_game_count": "games_played",

    # Core grades
    "grades_offense": "pff_offense",
    "grades_defense": "pff_defense",
    "grades_pass": "pff_passing",
    "grades_run": "pff_rushing",
    "grades_pass_route": "pff_receiving",

    # Blocking grades
    "grades_pass_block": "pff_pass_block",
    "grades_run_block": "pff_run_block",
    "pbe": "pass_blocking_efficiency",
    "pressures_allowed": "pressures_allowed",
    "sacks_allowed": "sacks_allowed",
    "hits_allowed": "hits_allowed",
    "hurries_allowed": "hurries_allowed",

    # Defensive grades
    "grades_pass_rush_defense": "pff_pass_rush",
    "grades_run_defense": "pff_run_defense",
    "grades_coverage_defense": "pff_coverage",
    "grades_tackle": "pff_tackling",

    # QB advanced metrics
    "btt_rate": "big_time_throw_pct",
    "big_time_throws": "big_time_throws",
    "twp_rate": "turnover_worthy_play_pct",
    "turnover_worthy_plays": "turnover_worthy_plays",
    "accuracy_percent": "adjusted_completion_pct",
    "completion_percent": "completion_pct",
    "qb_rating": "passer_rating",
    "avg_depth_of_target": "avg_depth_of_target",
    "avg_time_to_throw": "time_to_throw",

    # RB advanced metrics
    "elusive_rating": "elusive_rating",
    "yards_after_contact": "yards_after_contact",
    "yco_attempt": "yaco_per_attempt",
    "breakaway_percent": "breakaway_pct",
    "breakaway_yards": "breakaway_yards",
    "avoided_tackles": "missed_tackles_forced",

    # WR/TE advanced metrics
    "yprr": "yards_per_route_run",
    "drop_rate": "drop_rate",
    "drops": "drops",
    "contested_catch_rate": "contested_catch_rate",
    "contested_receptions": "contested_catches",
    "yards_after_catch": "yards_after_catch",
    "yards_after_catch_per_reception": "yac_per_reception",
    "caught_percent": "catch_rate",
    "routes": "routes_run",

    # Pass rush advanced metrics
    "prp": "pass_rushing_productivity",
    "pass_rush_win_rate": "pass_rush_win_rate",
    "total_pressures": "pressures",
    "hurries": "hurries",
    "hits": "hits",
    "sacks": "sacks",
    "batted_passes": "batted_passes",

    # Run defense metrics
    "stops": "run_stops",

    # Coverage metrics
    "qb_rating_against": "passer_rating_allowed",
    "yards_per_coverage_snap": "yards_per_coverage_snap",
    "coverage_snaps_per_reception": "coverage_snaps_per_reception",
    "receptions": "completions_allowed",
    "targets": "targets_allowed",
    "touchdowns": "tds_allowed",
    "yards": "yards_allowed",
    "interceptions": "ints",
    "pass_break_ups": "pbus",
    "forced_incompletes": "forced_incompletes",
    "forced_incompletion_rate": "forced_incompletion_rate",

    # Tackling metrics
    "tackles": "tackles",
    "assists": "tackle_assists",
    "tackles_for_loss": "tackles_for_loss",
    "missed_tackles": "missed_tackles",
    "missed_tackle_rate": "missed_tackle_pct",
    "forced_fumbles": "forced_fumbles",

    # Snap counts
    "snap_counts_defense": "defensive_snaps",
    "snap_counts_offense": "offensive_snaps",
    "snap_counts_pass_rush": "pass_rush_snaps",
    "snap_counts_coverage": "coverage_snaps",
}


def find_pff_files(directory: Path) -> List[Path]:
    """Find all PFF CSV files in directory."""
    files = []
    for file in directory.glob("20*_*.csv"):
        # Skip files that don't have year_type pattern
        parts = file.stem.split("_")
        if len(parts) >= 2 and parts[0].isdigit():
            files.append(file)
    return sorted(files)


def process_pff_files(
    input_dir: Path,
    output_path: Path,
    years: Optional[List[int]] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """Process all PFF CSV files and merge into a single output file.

    Args:
        input_dir: Directory containing PFF CSV files
        output_path: Path for output pff_player_grades.csv
        years: Optional list of years to process (default: all found)
        verbose: Print progress messages

    Returns:
        Merged DataFrame with all player grades
    """
    if verbose:
        print(f"Scanning for PFF files in {input_dir}...")

    files = find_pff_files(input_dir)

    if not files:
        if verbose:
            print("No PFF files found!")
        return pd.DataFrame()

    if verbose:
        print(f"Found {len(files)} PFF CSV files")

    # Group data by player ID and year
    year_data: Dict[int, Dict[int, Dict]] = {}  # year -> pff_id -> data

    for file in files:
        try:
            parts = file.stem.split("_")
            year = int(parts[0])

            if years and year not in years:
                continue

            df = pd.read_csv(file)

            # Apply column mapping
            df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

            if "pff_id" not in df.columns:
                continue

            df["season"] = year

            if year not in year_data:
                year_data[year] = {}

            # Store by pff_id, merging columns
            for _, row in df.iterrows():
                pid = row["pff_id"]
                if pid not in year_data[year]:
                    year_data[year][pid] = {}
                for col in df.columns:
                    val = row[col]
                    # Only update if value is not null and column doesn't exist or is null
                    if pd.notna(val):
                        existing = year_data[year][pid].get(col)
                        if existing is None or pd.isna(existing):
                            year_data[year][pid][col] = val

            if verbose:
                print(f"  {file.name}: {len(df)} rows")

        except Exception as e:
            if verbose:
                print(f"  Skip {file.name}: {e}")

    # Convert to DataFrame
    all_rows = []
    for year, players in year_data.items():
        for pid, data in players.items():
            all_rows.append(data)

    if not all_rows:
        if verbose:
            print("No data to merge!")
        return pd.DataFrame()

    merged = pd.DataFrame(all_rows)

    # Calculate overall grade if not present
    def calc_overall(row):
        grades = []
        for g in ["pff_offense", "pff_defense", "pff_passing", "pff_rushing",
                  "pff_receiving", "pff_pass_block", "pff_run_block"]:
            val = row.get(g)
            if pd.notna(val):
                grades.append(val)
        return round(sum(grades) / len(grades), 1) if grades else None

    if "pff_overall" not in merged.columns:
        merged["pff_overall"] = merged.apply(calc_overall, axis=1)

    # Reorder columns - put key columns first
    key_cols = [
        "name", "pff_id", "team", "position", "season", "games_played", "pff_overall",
        "pff_offense", "pff_defense", "pff_passing", "pff_rushing", "pff_receiving",
        "pff_pass_block", "pff_run_block", "pff_pass_rush", "pff_coverage",
        "pff_run_defense", "pff_tackling"
    ]
    other_cols = [c for c in merged.columns if c not in key_cols]
    col_order = [c for c in key_cols if c in merged.columns] + other_cols
    merged = merged[col_order]

    # Sort by season desc, then overall grade desc
    merged = merged.sort_values(
        ["season", "pff_overall"],
        ascending=[False, False],
        na_position="last"
    )

    # Save to output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)

    if verbose:
        print(f"\nSaved {len(merged)} players to {output_path}")
        print(f"Columns: {len(merged.columns)}")
        if "season" in merged.columns:
            print(f"Seasons: {sorted(merged['season'].unique())}")

    return merged


def main():
    """Main entry point for PFF merger."""
    # Determine paths from arguments or defaults
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent  # ml-engine/

    if len(sys.argv) > 1:
        input_dir = Path(sys.argv[1])
    else:
        input_dir = project_root.parent  # files/

    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        output_path = project_root / "data" / "processed" / "pff_player_grades.csv"

    print("=" * 60)
    print("PFF Data Merger")
    print("=" * 60)
    print(f"Input directory: {input_dir}")
    print(f"Output file: {output_path}")
    print("=" * 60)

    df = process_pff_files(input_dir, output_path)

    if not df.empty:
        print("\nPFF data merge complete!")
    else:
        print("\nNo data was processed")


if __name__ == "__main__":
    main()
