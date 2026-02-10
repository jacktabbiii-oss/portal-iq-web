"""
Generate NIL Valuations + Unified Player Table for ALL Players (FBS + FCS + Historical)

This script:
1. Uses PFF grades as the BASE (71k+ players - ALL college football)
2. Enriches with ESPN rosters (FBS headshots, height, weight)
3. Enriches with CFBD stats (production data)
4. Trains a calibrated ML model on real On3 NIL valuations
5. Predicts valuations for FBS AND FCS current season players (2025-2026)
6. Merges portal status, school tiers, and pre-computes WAR
7. Outputs:
   - portal_nil_valuations.csv (FBS + FCS current season, with NIL valuations)
   - unified_players.csv (ALL players - FBS + FCS + historical)

Run: python scripts/generate_all_valuations.py           # legacy mode
     python scripts/generate_all_valuations.py --unified  # full unified build
"""

import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

import pandas as pd
import numpy as np
from dotenv import load_dotenv
import boto3
from io import BytesIO

load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data" / "processed"

from src.models.custom_nil_valuator import CustomNILValuator  # noqa: E402

# S3/R2 client for loading PFF detailed stats
_s3_client = None

def get_s3_client():
    """Get or create S3 client for R2."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            's3',
            endpoint_url=os.getenv('R2_ENDPOINT_URL'),
            aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            region_name='auto'
        )
    return _s3_client

def load_pff_stat_from_r2(category: str, stat_type: str, season: int = 2025) -> pd.DataFrame:
    """Load PFF detailed stat file from R2.

    Args:
        category: Category folder (passing, rushing, receiving, defense, pass_rush, blocking)
        stat_type: Stat file name without year prefix (e.g., "passing_summary")
        season: Year to load (default: 2025)

    Returns:
        DataFrame with the stats
    """
    filename = f"{season}_{stat_type}.csv"
    s3_key = f"pff/{category}/{filename}"
    bucket = os.getenv('R2_BUCKET_NAME', 'portal-iq-data')

    try:
        s3 = get_s3_client()
        obj = s3.get_object(Bucket=bucket, Key=s3_key)
        df = pd.read_csv(BytesIO(obj['Body'].read()), low_memory=False)
        df["season"] = season
        return df
    except Exception as e:
        print(f"  Warning: Could not load {s3_key}: {e}")
        return pd.DataFrame()

# PFF columns to merge into unified table (curated from 100+ available)
PFF_COLUMNS = [
    # Core grades
    "pff_overall", "pff_offense", "pff_defense",
    "pff_passing", "pff_rushing", "pff_receiving",
    "pff_pass_block", "pff_run_block", "pff_pass_rush",
    "pff_coverage", "pff_run_defense", "pff_tackling",
    # Snap counts
    "games_played", "snap_counts_offense", "snap_counts_defense",
    # QB advanced
    "completion_pct", "passer_rating", "big_time_throw_pct",
    "turnover_worthy_play_pct", "avg_depth_of_target",
    "pressure_grades_pass",
    # RB advanced
    "elusive_rating", "yaco_per_attempt", "breakaway_pct",
    "breakaway_yards", "missed_tackles_forced",
    # WR/TE advanced
    "yards_per_route_run", "drop_rate", "contested_catch_rate",
    "targeted_qb_rating",
    "targets", "receptions", "rec_yards",
    # Pass rush advanced
    "pass_rush_win_rate", "pass_rushing_productivity",
    "pressures", "sacks", "hurries",
    # Coverage advanced
    "forced_incompletion_rate", "passer_rating_allowed",
    "yards_per_coverage_snap",
    "man_grades_coverage_defense", "zone_grades_coverage_defense",
    # Blocking advanced
    "pass_blocking_efficiency", "pressures_allowed",
    "true_pass_set_pbe",
    # Tackling
    "tackles", "missed_tackle_rate",
    # Production
    "yards", "touchdowns",
]


def load_data():
    """Load all data sources."""
    print("=" * 60)
    print("LOADING DATA SOURCES")
    print("=" * 60)

    data = {}

    # PFF grades - PRIMARY SOURCE (ALL college football)
    pff_path = DATA_DIR / "pff_player_grades.csv"
    if pff_path.exists():
        data["pff"] = pd.read_csv(pff_path)
        print(f"PFF grades: {len(data['pff'])} entries (PRIMARY BASE - FBS + FCS + historical)")
    else:
        data["pff"] = pd.DataFrame()
        print("PFF grades: NOT FOUND")

    # ESPN rosters - enrichment (FBS only, for headshots)
    espn_path = DATA_DIR / "espn_rosters.csv"
    if espn_path.exists():
        data["espn"] = pd.read_csv(espn_path)
        print(f"ESPN rosters: {len(data['espn'])} players (FBS enrichment)")
    else:
        data["espn"] = pd.DataFrame()
        print("ESPN rosters: NOT FOUND")

    # CFBD rosters (for additional info)
    cfbd_path = DATA_DIR / "cfbd_rosters.csv"
    if cfbd_path.exists():
        data["cfbd_rosters"] = pd.read_csv(cfbd_path)
        print(f"CFBD rosters: {len(data['cfbd_rosters'])} entries")
    else:
        data["cfbd_rosters"] = pd.DataFrame()

    # CFBD player stats
    stats_path = DATA_DIR / "cfbd_player_stats.csv"
    if stats_path.exists():
        data["cfbd_stats"] = pd.read_csv(stats_path)
        print(f"CFBD stats: {len(data['cfbd_stats'])} entries")
    else:
        data["cfbd_stats"] = pd.DataFrame()

    # On3 NIL rankings (real valuations - TRAINING DATA)
    nil_path = DATA_DIR / "on3_all_nil_rankings.csv"
    if nil_path.exists():
        data["on3_nil"] = pd.read_csv(nil_path)
        print(f"On3 NIL rankings: {len(data['on3_nil'])} players (FBS training data)")
    else:
        data["on3_nil"] = pd.DataFrame()

    # On3 portal data
    portal_path = DATA_DIR / "on3_transfer_portal.csv"
    if portal_path.exists():
        data["portal"] = pd.read_csv(portal_path)
        print(f"On3 portal: {len(data['portal'])} total entries")
    else:
        data["portal"] = pd.DataFrame()

    # Team talent rankings
    talent_path = DATA_DIR / "cfbd_team_talent.csv"
    if talent_path.exists():
        data["team_talent"] = pd.read_csv(talent_path)
        print(f"Team talent: {len(data['team_talent'])} teams")
    else:
        data["team_talent"] = pd.DataFrame()

    # Load PFF detailed stats from R2 (production data - yards, TDs, games)
    print(f"\nLoading PFF detailed stats from R2...")
    season = 2025  # Current season

    data["pff_passing"] = load_pff_stat_from_r2("passing", "passing_summary", season)
    if not data["pff_passing"].empty:
        print(f"  Passing stats: {len(data['pff_passing'])} QB records")

    data["pff_rushing"] = load_pff_stat_from_r2("rushing", "rushing_summary", season)
    if not data["pff_rushing"].empty:
        print(f"  Rushing stats: {len(data['pff_rushing'])} RB records")

    data["pff_receiving"] = load_pff_stat_from_r2("receiving", "receiving_summary", season)
    if not data["pff_receiving"].empty:
        print(f"  Receiving stats: {len(data['pff_receiving'])} WR/TE records")

    data["pff_defense"] = load_pff_stat_from_r2("defense", "defense_summary", season)
    if not data["pff_defense"].empty:
        print(f"  Defense stats: {len(data['pff_defense'])} defensive records")

    return data


def convert_height_to_inches(height) -> float:
    """Convert height string like '6' 4\"' to inches (76)."""
    if pd.isna(height):
        return None
    if isinstance(height, (int, float)):
        return float(height)
    height_str = str(height).strip()
    if "'" in height_str:
        try:
            parts = height_str.replace('"', '').split("'")
            feet = int(parts[0].strip())
            inches = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
            return float(feet * 12 + inches)
        except (ValueError, IndexError):
            return None
    try:
        return float(height_str)
    except ValueError:
        return None


def _normalize_name(name: str) -> str:
    """Normalize player name for matching."""
    if pd.isna(name):
        return ""
    return re.sub(r"[.\-']", "", str(name)).lower().strip()


def build_player_dataframe(data: dict, expanded_pff: bool = False) -> tuple:
    """
    Build comprehensive player DataFrame starting from PFF (ALL players).

    Strategy: PFF as base (71K) → outer merge everything else → keep ALL data

    Args:
        data: Dict of loaded DataFrames
        expanded_pff: If True, keep 45+ PFF columns (unified mode)

    Returns:
        (all_players_df, real_values_dict, on3_training_df)
    """

    # =========================================================================
    # STEP 1: PFF AS BASE - ALL COLLEGE FOOTBALL PLAYERS
    # =========================================================================

    pff_df = data.get("pff", pd.DataFrame())
    if pff_df.empty:
        print("ERROR: No PFF data! Cannot build comprehensive table.")
        return pd.DataFrame(), {}, pd.DataFrame()

    print(f"\n{'='*60}")
    print(f"BUILDING COMPREHENSIVE PLAYER TABLE")
    print(f"{'='*60}")
    print(f"Starting with PFF as base: {len(pff_df)} total player records")

    # Normalize PFF name column
    pff_name_col = "player" if "player" in pff_df.columns else "player_name" if "player_name" in pff_df.columns else "name" if "name" in pff_df.columns else None
    if not pff_name_col:
        print("ERROR: PFF data has no name column!")
        return pd.DataFrame(), {}, pd.DataFrame()

    pff_df = pff_df.rename(columns={pff_name_col: "name"})
    pff_df["name_normalized"] = pff_df["name"].apply(_normalize_name)

    # Deduplicate PFF: keep latest season + highest grade per player
    if "season" in pff_df.columns:
        pff_df["season"] = pd.to_numeric(pff_df["season"], errors="coerce")
        pff_df = pff_df.sort_values(["name_normalized", "season", "pff_overall"],
                                      ascending=[True, False, False], na_position="last")
    elif "pff_overall" in pff_df.columns:
        pff_df = pff_df.sort_values(["name_normalized", "pff_overall"],
                                      ascending=[True, False], na_position="last")

    pff_df = pff_df.drop_duplicates(subset=["name_normalized"], keep="first")
    print(f"After deduplication: {len(pff_df)} unique players")

    # Select PFF columns to keep
    if expanded_pff:
        pff_cols_to_keep = ["name", "name_normalized", "team", "position", "season"] + \
                          [c for c in PFF_COLUMNS if c in pff_df.columns]
    else:
        pff_cols_to_keep = ["name", "name_normalized", "team", "position", "season",
                           "pff_overall", "pff_offense", "pff_defense",
                           "pff_passing", "pff_rushing", "pff_receiving"]

    base_df = pff_df[[c for c in pff_cols_to_keep if c in pff_df.columns]].copy()

    # Rename PFF team → school for consistency
    if "team" in base_df.columns:
        base_df = base_df.rename(columns={"team": "school"})

    # Add season/league markers
    if "season" not in base_df.columns:
        base_df["season"] = 2025

    print(f"PFF columns retained: {len(base_df.columns)}")

    # =========================================================================
    # STEP 2: MERGE ESPN ROSTERS (FBS ENRICHMENT - headshots, height, weight)
    # =========================================================================

    espn_df = data.get("espn", pd.DataFrame())
    if not espn_df.empty:
        print(f"\nMerging ESPN rosters ({len(espn_df)} FBS players)...")

        espn_df = espn_df.rename(columns={"team": "school", "espn_id": "player_id"})
        if "height" in espn_df.columns:
            espn_df["height"] = espn_df["height"].apply(convert_height_to_inches)
        espn_df["name_normalized"] = espn_df["name"].apply(_normalize_name)

        # Keep ESPN-specific enrichment columns
        espn_cols = ["name_normalized", "player_id", "headshot_url", "height",
                     "weight", "jersey", "team_id", "class_year"]
        espn_merge = espn_df[[c for c in espn_cols if c in espn_df.columns]].copy()
        espn_merge = espn_merge.drop_duplicates(subset=["name_normalized"], keep="first")

        # Outer merge to keep ALL PFF players + add ESPN enrichment where available
        base_df = base_df.merge(espn_merge, on="name_normalized", how="left", suffixes=("", "_espn"))

        espn_matched = base_df["player_id"].notna().sum()
        print(f"  ESPN matched: {espn_matched} players ({espn_matched/len(base_df)*100:.1f}%)")
    else:
        print("\nNo ESPN data available")
        base_df["player_id"] = None
        base_df["headshot_url"] = None
        base_df["height"] = None
        base_df["weight"] = None

    # =========================================================================
    # STEP 3: MERGE PFF DETAILED STATS (production data - yards, TDs, games, etc.)
    # =========================================================================

    print(f"\nMerging PFF detailed stats (production data)...")

    # Merge passing stats (QB)
    pff_passing = data.get("pff_passing", pd.DataFrame())
    if not pff_passing.empty:
        # Standardize column names
        if "player" in pff_passing.columns:
            pff_passing = pff_passing.rename(columns={"player": "name"})

        # Rename PFF columns to match expected names
        pff_passing = pff_passing.rename(columns={
            "yards": "passing_yards",
            "touchdowns": "passing_tds",
            "interceptions": "passing_ints",
            "player_game_count": "games_played",
            "grades_pass": "pff_passing_grade"
        })

        pff_passing["name_normalized"] = pff_passing["name"].apply(_normalize_name)

        # Select relevant columns
        pass_cols = ["name_normalized", "attempts", "completions", "passing_yards", "passing_tds",
                     "passing_ints", "games_played", "pff_passing_grade"]
        pass_merge = pff_passing[[c for c in pass_cols if c in pff_passing.columns]].copy()
        pass_merge = pass_merge.drop_duplicates(subset=["name_normalized"], keep="first")

        base_df = base_df.merge(pass_merge, on="name_normalized", how="left", suffixes=("", "_pff_pass"))

        pass_matched = base_df["passing_yards"].notna().sum() if "passing_yards" in base_df.columns else 0
        print(f"  Passing stats matched: {pass_matched} QBs")

    # Merge rushing stats (RB/QB/etc)
    pff_rushing = data.get("pff_rushing", pd.DataFrame())
    if not pff_rushing.empty:
        if "player" in pff_rushing.columns:
            pff_rushing = pff_rushing.rename(columns={"player": "name"})

        # Rename PFF columns to match expected names
        pff_rushing = pff_rushing.rename(columns={
            "yards": "rushing_yards",
            "touchdowns": "rushing_tds",
            "attempts": "rushing_attempts",
            "player_game_count": "games_played_rushing"
        })

        pff_rushing["name_normalized"] = pff_rushing["name"].apply(_normalize_name)

        rush_cols = ["name_normalized", "rushing_attempts", "rushing_yards", "rushing_tds",
                     "games_played_rushing"]
        rush_merge = pff_rushing[[c for c in rush_cols if c in pff_rushing.columns]].copy()
        rush_merge = rush_merge.drop_duplicates(subset=["name_normalized"], keep="first")

        base_df = base_df.merge(rush_merge, on="name_normalized", how="left", suffixes=("", "_pff_rush"))

        rush_matched = base_df["rushing_yards"].notna().sum() if "rushing_yards" in base_df.columns else 0
        print(f"  Rushing stats matched: {rush_matched} RBs")

    # Merge receiving stats (WR/TE)
    pff_receiving = data.get("pff_receiving", pd.DataFrame())
    if not pff_receiving.empty:
        if "player" in pff_receiving.columns:
            pff_receiving = pff_receiving.rename(columns={"player": "name"})

        # Rename PFF columns to match expected names
        pff_receiving = pff_receiving.rename(columns={
            "yards": "receiving_yards",
            "touchdowns": "receiving_tds",
            "player_game_count": "games_played_receiving"
        })

        pff_receiving["name_normalized"] = pff_receiving["name"].apply(_normalize_name)

        rec_cols = ["name_normalized", "targets", "receptions", "receiving_yards", "receiving_tds",
                    "games_played_receiving"]
        rec_merge = pff_receiving[[c for c in rec_cols if c in pff_receiving.columns]].copy()
        rec_merge = rec_merge.drop_duplicates(subset=["name_normalized"], keep="first")

        base_df = base_df.merge(rec_merge, on="name_normalized", how="left", suffixes=("", "_pff_rec"))

        rec_matched = base_df["receiving_yards"].notna().sum() if "receiving_yards" in base_df.columns else 0
        print(f"  Receiving stats matched: {rec_matched} WR/TEs")

    # Merge defense stats (tackles, sacks, etc)
    pff_defense = data.get("pff_defense", pd.DataFrame())
    if not pff_defense.empty:
        if "player" in pff_defense.columns:
            pff_defense = pff_defense.rename(columns={"player": "name"})

        # Rename PFF columns
        pff_defense = pff_defense.rename(columns={
            "player_game_count": "games_played_defense"
        })

        pff_defense["name_normalized"] = pff_defense["name"].apply(_normalize_name)

        def_cols = ["name_normalized", "tackles", "assists", "sacks", "interceptions",
                    "games_played_defense"]
        def_merge = pff_defense[[c for c in def_cols if c in pff_defense.columns]].copy()
        def_merge = def_merge.drop_duplicates(subset=["name_normalized"], keep="first")

        base_df = base_df.merge(def_merge, on="name_normalized", how="left", suffixes=("", "_pff_def"))

        def_matched = base_df["tackles"].notna().sum() if "tackles" in base_df.columns else 0
        print(f"  Defense stats matched: {def_matched} defenders")

    # Consolidate games_played from multiple sources (prioritize by position)
    if "games_played" not in base_df.columns:
        base_df["games_played"] = None

    for idx in base_df.index:
        if pd.notna(base_df.at[idx, "games_played"]):
            continue

        pos = base_df.at[idx, "position"] if "position" in base_df.columns else ""

        # Prioritize by position
        if pos == "QB" and "games_played" in base_df.columns and pd.notna(base_df.at[idx, "games_played"]):
            pass  # Already set from passing
        elif pos in ["RB", "HB", "FB"] and "games_played_rushing" in base_df.columns:
            base_df.at[idx, "games_played"] = base_df.at[idx, "games_played_rushing"]
        elif pos in ["WR", "TE"] and "games_played_receiving" in base_df.columns:
            base_df.at[idx, "games_played"] = base_df.at[idx, "games_played_receiving"]
        elif "games_played_defense" in base_df.columns:
            base_df.at[idx, "games_played"] = base_df.at[idx, "games_played_defense"]

    # Count players with stats
    stat_cols = [c for c in ["passing_yards", "rushing_yards", "receiving_yards", "tackles"] if c in base_df.columns]
    if stat_cols:
        total_with_stats = base_df[stat_cols].notna().any(axis=1).sum()
        print(f"  Total players with production stats: {total_with_stats}")

    # =========================================================================
    # STEP 4: MERGE CFBD ROSTERS (additional measurables)
    # =========================================================================

    cfbd_rosters = data.get("cfbd_rosters", pd.DataFrame())
    if not cfbd_rosters.empty:
        print(f"\nMerging CFBD rosters ({len(cfbd_rosters)} records)...")

        if "name" in cfbd_rosters.columns:
            cfbd_rosters["name_normalized"] = cfbd_rosters["name"].apply(_normalize_name)

            # Keep CFBD-specific columns that ESPN might not have
            cfbd_cols = ["name_normalized", "hometown", "recruit_year"]
            cfbd_merge = cfbd_rosters[[c for c in cfbd_cols if c in cfbd_rosters.columns]].copy()
            cfbd_merge = cfbd_merge.drop_duplicates(subset=["name_normalized"], keep="first")

            base_df = base_df.merge(cfbd_merge, on="name_normalized", how="left")

    # =========================================================================
    # STEP 5: BUILD ON3 REAL VALUE LOOKUP (for ML training)
    # =========================================================================

    on3_nil = data.get("on3_nil", pd.DataFrame())
    real_values = {}

    if not on3_nil.empty and "name" in on3_nil.columns:
        print(f"\nProcessing On3 NIL training data ({len(on3_nil)} players)...")

        for _, row in on3_nil.iterrows():
            name = str(row.get("name", "")).lower().strip()
            val = row.get("nil_valuation", row.get("nil_value", 0))
            if name and pd.notna(val) and val > 0:
                real_values[name] = {
                    "nil_value": val,
                    "stars": row.get("stars", row.get("recruiting_stars", 3)),
                    "is_predicted": False,
                }
        print(f"  Found {len(real_values)} players with real On3 NIL values")

        # Add stars from On3 to base where available
        for idx, row in base_df.iterrows():
            name_lower = str(row.get("name", "")).lower().strip()
            if name_lower in real_values:
                stars = real_values[name_lower].get("stars")
                if pd.notna(stars):
                    base_df.at[idx, "stars"] = stars

    # =========================================================================
    # STEP 6: IDENTIFY FBS vs FCS (for NIL prediction targeting)
    # =========================================================================

    print(f"\nIdentifying FBS vs FCS players...")

    # FBS schools (Power 5 + Group of 5)
    fbs_schools = set()
    if not espn_df.empty and "school" in espn_df.columns:
        fbs_schools = set(espn_df["school"].dropna().unique())

    # Add known FBS schools from CFBD
    cfbd_stats = data.get("cfbd_stats", pd.DataFrame())
    if not cfbd_stats.empty and "school" in cfbd_stats.columns:
        fbs_schools.update(cfbd_stats["school"].dropna().unique())

    # Mark FBS vs FCS
    def classify_division(school):
        if pd.isna(school):
            return "Unknown"
        school_norm = str(school).lower().strip()
        # Check if in FBS schools
        for fbs in fbs_schools:
            if fbs.lower().strip() in school_norm or school_norm in fbs.lower().strip():
                return "FBS"
        return "FCS"

    base_df["division"] = base_df["school"].apply(classify_division)

    fbs_count = (base_df["division"] == "FBS").sum()
    fcs_count = (base_df["division"] == "FCS").sum()
    unk_count = (base_df["division"] == "Unknown").sum()

    print(f"  FBS: {fbs_count} players")
    print(f"  FCS: {fcs_count} players")
    print(f"  Unknown: {unk_count} players")

    # =========================================================================
    # SUMMARY
    # =========================================================================

    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE TABLE BUILT")
    print(f"{'='*60}")
    print(f"Total players: {len(base_df)}")
    print(f"  FBS: {fbs_count}")
    print(f"  FCS: {fcs_count}")
    print(f"  Unknown: {unk_count}")
    print(f"Columns: {len(base_df.columns)}")
    print(f"With headshots: {base_df['headshot_url'].notna().sum() if 'headshot_url' in base_df.columns else 0}")
    print(f"With PFF overall: {base_df['pff_overall'].notna().sum() if 'pff_overall' in base_df.columns else 0}")

    return base_df, real_values, on3_nil


def generate_calibrated_valuations(all_players_df: pd.DataFrame, real_values: dict,
                                    on3_df: pd.DataFrame, model: 'CustomNILValuator') -> pd.DataFrame:
    """Generate NIL valuations for FBS and FCS players."""
    print("\n" + "=" * 60)
    print("GENERATING NIL VALUATIONS (FBS + FCS)")
    print("=" * 60)

    # Separate FBS and FCS for processing
    fbs_mask = all_players_df["division"] == "FBS"
    fbs_df = all_players_df[fbs_mask].copy()
    fcs_df = all_players_df[~fbs_mask].copy()

    print(f"\nFBS players (will predict NIL): {len(fbs_df)}")
    print(f"FCS players (will predict NIL): {len(fcs_df)}")

    if fbs_df.empty:
        print("No FBS players to predict!")
        all_players_df["nil_value"] = None
        all_players_df["nil_tier"] = None
        all_players_df["is_predicted"] = None
        all_players_df["confidence"] = None
        return all_players_df

    # Store On3 real values for comparison (separate column)
    print(f"\nStoring On3 real values for comparison...")
    fbs_df["on3_nil_value"] = None
    fbs_df["on3_nil_tier"] = None
    for idx, row in fbs_df.iterrows():
        name_lower = str(row["name"]).lower().strip()
        if name_lower in real_values:
            rv = real_values[name_lower]
            val = rv.get("nil_value", 0)
            fbs_df.at[idx, "on3_nil_value"] = val

            # On3 tier
            if val >= 2_000_000:
                fbs_df.at[idx, "on3_nil_tier"] = "mega"
            elif val >= 500_000:
                fbs_df.at[idx, "on3_nil_tier"] = "premium"
            elif val >= 100_000:
                fbs_df.at[idx, "on3_nil_tier"] = "solid"
            elif val >= 25_000:
                fbs_df.at[idx, "on3_nil_tier"] = "moderate"
            else:
                fbs_df.at[idx, "on3_nil_tier"] = "entry"

    on3_count = fbs_df["on3_nil_value"].notna().sum()
    print(f"  {on3_count} players have On3 real values for comparison")

    # Filter to current season (2025) only - exclude NFL draftees and graduates
    print(f"\nFiltering to current season (2025) players only...")
    current_season = 2025
    fbs_current = fbs_df[fbs_df["season"] == current_season].copy()
    fbs_old = fbs_df[fbs_df["season"] != current_season].copy()

    print(f"  Current season (2025): {len(fbs_current)} players")
    print(f"  Old seasons: {len(fbs_old)} players (will set NIL=NULL)")

    # Apply custom algorithm to CURRENT FBS players only (our main feature)
    print(f"\nApplying custom algorithm to {len(fbs_current)} current season players...")
    print("(Custom algorithm is primary - On3 values for comparison only)")

    if not fbs_current.empty:
        # Generate valuations for current season FBS players using CustomNILValuator
        predicted = model.valuate_dataframe(fbs_current)
        # CRITICAL: Use .values to copy by position, not by index (avoids misalignment)
        fbs_current["nil_value"] = predicted["custom_nil_value"].values
        fbs_current["nil_tier"] = predicted["nil_tier"].values
        fbs_current["confidence"] = predicted["valuation_confidence"].values
        fbs_current["is_predicted"] = True

    # Old season players get NULL valuations (they're not in college anymore)
    if not fbs_old.empty:
        fbs_old["nil_value"] = None
        fbs_old["nil_tier"] = None
        fbs_old["confidence"] = None
        fbs_old["is_predicted"] = None

    # Combine current and old season FBS players
    fbs_with_nil = pd.concat([fbs_current, fbs_old], ignore_index=True)

    # Process FCS players the same way (filter by season, apply custom algorithm)
    print(f"\nProcessing FCS players...")

    if not fcs_df.empty:
        # Store On3 values for FCS (if any)
        fcs_df["on3_nil_value"] = None
        fcs_df["on3_nil_tier"] = None
        for idx, row in fcs_df.iterrows():
            name_lower = str(row["name"]).lower().strip()
            if name_lower in real_values:
                rv = real_values[name_lower]
                val = rv.get("nil_value", 0)
                fcs_df.at[idx, "on3_nil_value"] = val
                if val >= 2_000_000:
                    fcs_df.at[idx, "on3_nil_tier"] = "mega"
                elif val >= 500_000:
                    fcs_df.at[idx, "on3_nil_tier"] = "premium"
                elif val >= 100_000:
                    fcs_df.at[idx, "on3_nil_tier"] = "solid"
                elif val >= 25_000:
                    fcs_df.at[idx, "on3_nil_tier"] = "moderate"
                else:
                    fcs_df.at[idx, "on3_nil_tier"] = "entry"

        on3_fcs = fcs_df["on3_nil_value"].notna().sum()
        print(f"  {on3_fcs} FCS players have On3 values")

        # Filter FCS to current season only
        fcs_current = fcs_df[fcs_df["season"] == current_season].copy()
        fcs_old = fcs_df[fcs_df["season"] != current_season].copy()

        print(f"  Current season (2025): {len(fcs_current)} FCS players")
        print(f"  Old seasons: {len(fcs_old)} FCS players (will set NIL=NULL)")

        # Apply custom algorithm to current FCS players
        if not fcs_current.empty:
            print(f"  Applying custom algorithm to {len(fcs_current)} current FCS players...")
            predicted_fcs = model.valuate_dataframe(fcs_current)
            fcs_current["nil_value"] = predicted_fcs["custom_nil_value"].values
            fcs_current["nil_tier"] = predicted_fcs["nil_tier"].values
            fcs_current["confidence"] = predicted_fcs["valuation_confidence"].values
            fcs_current["is_predicted"] = True

        # Old season FCS get NULL
        if not fcs_old.empty:
            fcs_old["nil_value"] = None
            fcs_old["nil_tier"] = None
            fcs_old["confidence"] = None
            fcs_old["is_predicted"] = None

        fcs_with_nil = pd.concat([fcs_current, fcs_old], ignore_index=True)
    else:
        fcs_with_nil = fcs_df
        fcs_with_nil["nil_value"] = None
        fcs_with_nil["nil_tier"] = None
        fcs_with_nil["is_predicted"] = None
        fcs_with_nil["confidence"] = None

    # Combine all
    combined = pd.concat([fbs_with_nil, fcs_with_nil], ignore_index=True)

    # Sort by NIL value (nulls last)
    combined = combined.sort_values("nil_value", ascending=False, na_position="last").reset_index(drop=True)

    return combined


def merge_portal_status(df: pd.DataFrame, data: dict) -> pd.DataFrame:
    """Merge transfer portal status into unified table."""
    print("\n" + "=" * 60)
    print("MERGING PORTAL STATUS")
    print("=" * 60)

    portal_df = data.get("portal", pd.DataFrame())
    if portal_df.empty:
        print("No portal data available")
        df["in_portal"] = False
        df["portal_status"] = None
        df["origin_school"] = None
        df["destination_school"] = None
        df["portal_year"] = None
        return df

    # Filter to current cycle
    if "source" in portal_df.columns:
        portal_df = portal_df[portal_df["source"].str.contains("2026|2025", na=False)].copy()
    elif "year" in portal_df.columns:
        portal_df = portal_df[portal_df["year"].isin([2025, 2026])].copy()

    print(f"Current cycle portal entries: {len(portal_df)}")

    # Normalize names for matching
    portal_df["_name_key"] = portal_df["name"].apply(_normalize_name)

    # Deduplicate: prefer Committed > Entered > Withdrawn
    status_order = {"Committed": 0, "Entered": 1, "Withdrawn": 2, "Expected": 3}
    if "status" in portal_df.columns:
        portal_df["_status_order"] = portal_df["status"].map(status_order).fillna(99)
        portal_df = portal_df.sort_values("_status_order")
    portal_df = portal_df.drop_duplicates(subset=["_name_key"], keep="first")

    # Build portal lookup
    portal_lookup = {}
    for _, row in portal_df.iterrows():
        key = row["_name_key"]
        if not key:
            continue
        portal_lookup[key] = {
            "portal_status": row.get("status", "Entered"),
            "origin_school": row.get("from_school", row.get("origin_school", "")),
            "destination_school": row.get("to_school", row.get("destination_school", "")),
            "portal_year": row.get("year", row.get("source", "")),
        }
    print(f"Portal lookup built for {len(portal_lookup)} players")

    # Merge into unified table
    in_portal = []
    portal_status = []
    origin_school = []
    destination_school = []
    portal_year = []

    for _, row in df.iterrows():
        key = _normalize_name(str(row.get("name", "")))
        if key in portal_lookup:
            p = portal_lookup[key]
            in_portal.append(True)
            portal_status.append(p["portal_status"])
            origin_school.append(p["origin_school"])
            destination_school.append(p["destination_school"])
            portal_year.append(str(p["portal_year"]))
        else:
            in_portal.append(False)
            portal_status.append(None)
            origin_school.append(None)
            destination_school.append(None)
            portal_year.append(None)

    df["in_portal"] = in_portal
    df["portal_status"] = portal_status
    df["origin_school"] = origin_school
    df["destination_school"] = destination_school
    df["portal_year"] = portal_year

    matched = sum(in_portal)
    print(f"Portal status merged: {matched} players matched ({matched/len(df)*100:.1f}%)")
    return df


def merge_school_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """Merge school tier, multiplier, and conference into unified table."""
    print("\n" + "=" * 60)
    print("MERGING SCHOOL TIERS")
    print("=" * 60)

    try:
        from src.models.school_tiers import get_school_tiers
        tiers = get_school_tiers()
        if not tiers:
            print("WARNING: School tiers empty. Using defaults.")
            df["school_tier"] = "g5_mid"
            df["school_multiplier"] = 0.8
            df["conference"] = None
            return df

        print(f"Loaded tiers for {len(tiers)} schools")

        # Build case-insensitive lookup
        tier_lookup = {}
        for school, info in tiers.items():
            tier_lookup[school.lower().strip()] = info

        school_tier = []
        school_mult = []
        conference = []

        for _, row in df.iterrows():
            school = str(row.get("school", "")).lower().strip()
            # Try exact match, then partial
            info = tier_lookup.get(school)
            if info is None:
                for key, val in tier_lookup.items():
                    if key in school or school in key:
                        info = val
                        break

            if info:
                school_tier.append(info["tier"])
                school_mult.append(info["multiplier"])
                conference.append(info.get("conference"))
            else:
                school_tier.append("g5_mid")
                school_mult.append(0.8)
                conference.append(None)

        df["school_tier"] = school_tier
        df["school_multiplier"] = school_mult
        df["conference"] = conference

        tier_dist = pd.Series(school_tier).value_counts()
        print(f"Tier distribution:\n{tier_dist.to_string()}")

    except Exception as e:
        print(f"WARNING: Could not load school tiers: {e}")
        df["school_tier"] = "g5_mid"
        df["school_multiplier"] = 0.8
        df["conference"] = None

    return df


def compute_war(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute WAR for every player in unified table."""
    print("\n" + "=" * 60)
    print("COMPUTING WAR FOR ALL PLAYERS")
    print("=" * 60)

    try:
        # Import from parent ml-engine directory
        import sys
        from pathlib import Path
        parent_dir = Path(__file__).parent.parent.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))

        from src.utils.data_loader import calculate_player_war
        print("Successfully imported calculate_player_war")
    except ImportError as e:
        print(f"WARNING: Could not import calculate_player_war: {e}")
        print("Skipping WAR computation.")
        df["war"] = 0.0
        df["war_low"] = 0.0
        df["war_high"] = 0.0
        df["war_confidence"] = "low"
        return df

    wars = []
    war_lows = []
    war_highs = []
    war_confs = []

    pff_col_set = set(PFF_COLUMNS)

    for idx, row in df.iterrows():
        # Build PFF stats dict from row
        pff_stats = {}
        for col in pff_col_set:
            val = row.get(col)
            if pd.notna(val):
                try:
                    pff_stats[col] = float(val)
                except (ValueError, TypeError):
                    pass

        try:
            result = calculate_player_war(
                position=str(row.get("position", "ATH")),
                stars=int(row.get("stars", 0)) if pd.notna(row.get("stars")) else 0,
                nil_value=float(row.get("nil_value", 0)) if pd.notna(row.get("nil_value")) else 0,
                school=str(row.get("school", "")),
                pff_stats=pff_stats if pff_stats else None,
            )
            wars.append(result.get("war", 0.0))
            war_lows.append(result.get("war_low", 0.0))
            war_highs.append(result.get("war_high", 0.0))
            war_confs.append(result.get("confidence", "low"))
        except Exception:
            wars.append(0.0)
            war_lows.append(0.0)
            war_highs.append(0.0)
            war_confs.append("low")

        if (idx + 1) % 10000 == 0:
            print(f"  WAR computed for {idx + 1}/{len(df)} players...")

    df["war"] = wars
    df["war_low"] = war_lows
    df["war_high"] = war_highs
    df["war_confidence"] = war_confs

    print(f"WAR computed for {len(df)} players")
    print(f"  Mean WAR:   {df['war'].mean():.2f}")
    print(f"  Median WAR: {df['war'].median():.2f}")
    print(f"  Max WAR:    {df['war'].max():.2f}")
    non_zero = (df['war'] > 0).sum()
    print(f"  Non-zero WAR: {non_zero} ({non_zero/len(df)*100:.1f}%)")

    return df


def merge_headshots_unified(df: pd.DataFrame, data: dict) -> pd.DataFrame:
    """Merge headshots from portal/On3/ESPN with priority chain."""
    portal_df = data.get("portal", pd.DataFrame())
    on3_nil = data.get("on3_nil", pd.DataFrame())

    headshot_lookup = {}

    # Priority 1: On3 portal (best coverage)
    if not portal_df.empty and "headshot_url" in portal_df.columns:
        for _, row in portal_df.iterrows():
            name = _normalize_name(str(row.get("name", "")))
            url = row.get("headshot_url")
            if name and pd.notna(url) and str(url).startswith("http"):
                headshot_lookup[name] = str(url)

    # Priority 2: On3 NIL
    if not on3_nil.empty and "headshot_url" in on3_nil.columns:
        for _, row in on3_nil.iterrows():
            name = _normalize_name(str(row.get("name", "")))
            url = row.get("headshot_url")
            if name and name not in headshot_lookup and pd.notna(url) and str(url).startswith("http"):
                headshot_lookup[name] = str(url)

    # Apply headshots — only fill where missing
    if headshot_lookup:
        for idx, row in df.iterrows():
            if pd.isna(row.get("headshot_url")) or not str(row.get("headshot_url", "")).startswith("http"):
                key = _normalize_name(str(row.get("name", "")))
                if key in headshot_lookup:
                    df.at[idx, "headshot_url"] = headshot_lookup[key]

    has_headshot = df["headshot_url"].notna().sum() if "headshot_url" in df.columns else 0
    print(f"Headshot coverage: {has_headshot}/{len(df)} ({has_headshot/len(df)*100:.1f}%)")

    return df


def filter_current_portal(data: dict) -> pd.DataFrame:
    """Filter portal data to current cycle only (2025-2026)."""
    print("\n" + "=" * 60)
    print("FILTERING PORTAL TO CURRENT CYCLE")
    print("=" * 60)

    portal_df = data.get("portal", pd.DataFrame())
    if portal_df.empty:
        return pd.DataFrame()

    print(f"Total portal entries: {len(portal_df)}")

    if "source" in portal_df.columns:
        current = portal_df[portal_df["source"].str.contains("2026|2025", na=False)].copy()
    elif "year" in portal_df.columns:
        current = portal_df[portal_df["year"].isin([2025, 2026])].copy()
    elif "commit_date" in portal_df.columns:
        portal_df["commit_date"] = pd.to_datetime(portal_df["commit_date"], errors="coerce")
        current = portal_df[portal_df["commit_date"].dt.year >= 2025].copy()
    else:
        current = portal_df.head(5000).copy()

    print(f"Current cycle (2025-2026): {len(current)} entries")
    return current


def verify_unified_table(df: pd.DataFrame) -> bool:
    """Sanity checks on the unified table."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    issues = []

    if len(df) < 50000:
        print(f"Expected 50K+ players (FBS+FCS), got {len(df)}")

    fbs_count = (df["division"] == "FBS").sum() if "division" in df.columns else 0
    fcs_count = (df["division"] == "FCS").sum() if "division" in df.columns else 0
    print(f"FBS: {fbs_count}, FCS: {fcs_count}")

    nil_count = df["nil_value"].notna().sum()
    print(f"NIL valuations: {nil_count}")

    pff_count = df["pff_overall"].notna().sum() if "pff_overall" in df.columns else 0
    print(f"PFF match rate: {pff_count}/{len(df)} ({pff_count/len(df)*100:.1f}%)")

    portal_count = df["in_portal"].sum() if "in_portal" in df.columns else 0
    print(f"Portal players: {portal_count}")

    war_count = (df["war"] > 0).sum() if "war" in df.columns else 0
    print(f"Players with WAR > 0: {war_count}")

    if "war" in df.columns and war_count > 0:
        war_max = df["war"].max()
        war_median = df["war"].median()
        print(f"WAR range: {df['war'].min():.2f} to {war_max:.2f} (median {war_median:.2f})")
        if war_max > 20:
            issues.append(f"WAR max suspiciously high: {war_max}")

    headshot_count = df["headshot_url"].notna().sum() if "headshot_url" in df.columns else 0
    print(f"Headshot coverage: {headshot_count}/{len(df)} ({headshot_count/len(df)*100:.1f}%)")

    col_count = len(df.columns)
    print(f"Total columns: {col_count}")

    if issues:
        print(f"\nWARNINGS: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\nAll checks passed!")

    return len(issues) == 0


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Generate NIL valuations and unified player table")
    parser.add_argument("--unified", action="store_true", help="Build full unified_players.csv")
    args = parser.parse_args()

    print("=" * 60)
    print("PORTAL IQ - COMPREHENSIVE VALUATION GENERATOR")
    if args.unified:
        print("  MODE: UNIFIED (FBS + FCS + historical)")
    else:
        print("  MODE: DEFAULT (FBS + FCS NIL valuations)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load all data
    data = load_data()

    # Build comprehensive player DataFrame (PFF-first)
    all_players_df, real_values, on3_df = build_player_dataframe(data, expanded_pff=args.unified)

    if all_players_df.empty:
        print("ERROR: No player data!")
        return

    if on3_df.empty:
        print("ERROR: No On3 training data! Cannot calibrate NIL.")
        # Continue anyway - we can still build the table without NIL predictions

    # Create custom valuator model (transparent, rule-based)
    model = CustomNILValuator()

    # Generate NIL valuations (FBS + FCS)
    valuations_df = generate_calibrated_valuations(all_players_df, real_values, on3_df, model)

    if valuations_df.empty:
        print("ERROR: No data generated!")
        return

    # Save FBS + FCS valuations
    output_path = DATA_DIR / "portal_nil_valuations.csv"
    valuations_df.to_csv(output_path, index=False)

    fbs_count = (valuations_df["division"] == "FBS").sum() if "division" in valuations_df.columns else len(valuations_df)
    fcs_count = (valuations_df["division"] == "FCS").sum() if "division" in valuations_df.columns else 0
    print(f"\nSaved {len(valuations_df)} valuations to {output_path}")
    print(f"  FBS: {fbs_count}")
    print(f"  FCS: {fcs_count}")

    # Filter and save current portal
    current_portal = filter_current_portal(data)
    if not current_portal.empty:
        portal_output = DATA_DIR / "on3_transfer_portal_current.csv"
        current_portal.to_csv(portal_output, index=False)
        print(f"Saved {len(current_portal)} current portal entries to {portal_output}")

    # --- UNIFIED MODE: Add portal, school tiers, WAR ---
    if args.unified:
        unified_df = valuations_df.copy()

        # Merge portal status
        unified_df = merge_portal_status(unified_df, data)

        # Merge school tiers + conference
        unified_df = merge_school_tiers(unified_df)

        # Merge headshots from all sources
        unified_df = merge_headshots_unified(unified_df, data)

        # Pre-compute WAR
        unified_df = compute_war(unified_df)

        # Ensure normalized columns exist
        if "name_normalized" not in unified_df.columns:
            unified_df["name_normalized"] = unified_df["name"].apply(_normalize_name)

        # Add school_normalized for fast filtering
        unified_df["school_normalized"] = unified_df["school"].str.lower().str.strip()

        # Verify
        verify_unified_table(unified_df)

        # Save unified table
        unified_path = DATA_DIR / "unified_players.csv"
        unified_df.to_csv(unified_path, index=False)
        print(f"\nSaved unified table: {len(unified_df)} players, {len(unified_df.columns)} columns")
        print(f"  File: {unified_path}")
        print(f"  Size: {unified_path.stat().st_size / 1_000_000:.1f} MB")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    fbs_count = (valuations_df["division"] == "FBS").sum() if "division" in valuations_df.columns else len(valuations_df)
    fcs_count = (valuations_df["division"] == "FCS").sum() if "division" in valuations_df.columns else 0

    print(f"Total players: {len(valuations_df)}")
    print(f"  FBS: {fbs_count}")
    print(f"  FCS: {fcs_count}")

    if "nil_value" in valuations_df.columns:
        real_count = (valuations_df["is_predicted"] == False).sum()
        pred_count = (valuations_df["is_predicted"] == True).sum()
        print(f"\nNIL valuations (FBS + FCS):")
        print(f"  - With real On3 values: {real_count}")
        print(f"  - With calibrated predictions: {pred_count}")

        nil_df = valuations_df[valuations_df["nil_value"].notna()]
        if not nil_df.empty:
            print(f"\nTier distribution:")
            print(nil_df["nil_tier"].value_counts().to_string())
            print(f"\nValue statistics:")
            print(f"  Mean:   ${nil_df['nil_value'].mean():,.0f}")
            print(f"  Median: ${nil_df['nil_value'].median():,.0f}")
            print(f"  Total:  ${nil_df['nil_value'].sum():,.0f}")
            print(f"\nTop 10 valuations:")
            top10 = nil_df[["name", "position", "school", "nil_value", "nil_tier", "is_predicted"]].head(10)
            for i, row in top10.iterrows():
                src = "On3" if not row["is_predicted"] else "Pred"
                print(f"  {i+1:3}. ${row['nil_value']:>12,.0f} | {row['name']:25} | {row['position']:4} | {row['school']:20} | {row['nil_tier']:8} | {src}")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
