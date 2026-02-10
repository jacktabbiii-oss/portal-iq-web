"""
Generate NIL Valuations + Unified Player Table for ALL Current FBS Players

This script:
1. Uses ESPN rosters as the base (21k+ current players with headshots)
2. Enriches with CFBD stats and PFF grades (45+ columns)
3. Trains a calibrated ML model on real On3 NIL valuations (368 players)
4. Predicts calibrated valuations for ALL remaining players
5. Merges portal status, school tiers, and pre-computes WAR
6. Outputs:
   - portal_nil_valuations.csv (backward-compat)
   - unified_players.csv (full unified table)

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

load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data" / "processed"

from src.models.calibrated_valuator import CalibratedNILValuator  # noqa: E402

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

    # ESPN rosters - primary source (current players with headshots)
    espn_path = DATA_DIR / "espn_rosters.csv"
    if espn_path.exists():
        data["espn"] = pd.read_csv(espn_path)
        print(f"ESPN rosters: {len(data['espn'])} players")
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

    # PFF grades
    pff_path = DATA_DIR / "pff_player_grades.csv"
    if pff_path.exists():
        data["pff"] = pd.read_csv(pff_path)
        print(f"PFF grades: {len(data['pff'])} entries")
    else:
        data["pff"] = pd.DataFrame()

    # On3 NIL rankings (real valuations - TRAINING DATA)
    nil_path = DATA_DIR / "on3_all_nil_rankings.csv"
    if nil_path.exists():
        data["on3_nil"] = pd.read_csv(nil_path)
        print(f"On3 NIL rankings: {len(data['on3_nil'])} players (training data)")
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
    Build enriched player DataFrame from ESPN + CFBD + PFF data.

    Args:
        data: Dict of loaded DataFrames
        expanded_pff: If True, merge 45+ PFF columns (unified mode)

    Returns:
        (espn_df, real_values_dict, on3_training_df)
    """
    espn_df = data["espn"].copy()
    if espn_df.empty:
        print("ERROR: No ESPN roster data!")
        return pd.DataFrame(), {}, pd.DataFrame()

    # Standardize ESPN data
    espn_df = espn_df.rename(columns={
        "team": "school",
        "espn_id": "player_id",
    })

    # Convert height
    if "height" in espn_df.columns:
        espn_df["height"] = espn_df["height"].apply(convert_height_to_inches)

    # Add normalized name for all lookups
    espn_df["name_normalized"] = espn_df["name"].apply(_normalize_name)

    print(f"Starting with {len(espn_df)} ESPN players")

    # --- Build On3 real-value lookup ---
    on3_nil = data.get("on3_nil", pd.DataFrame())
    real_values = {}
    if not on3_nil.empty and "name" in on3_nil.columns:
        for _, row in on3_nil.iterrows():
            name = str(row.get("name", "")).lower().strip()
            val = row.get("nil_valuation", row.get("nil_value", 0))
            if name and pd.notna(val) and val > 0:
                real_values[name] = {
                    "nil_value": val,
                    "stars": row.get("stars", row.get("recruiting_stars", 3)),
                    "is_predicted": False,
                }
        print(f"Found {len(real_values)} players with real On3 NIL values")

    # --- Merge CFBD stats ---
    cfbd_stats = data.get("cfbd_stats", pd.DataFrame())
    stats_lookup = {}
    if not cfbd_stats.empty:
        if "season" in cfbd_stats.columns:
            cfbd_stats = cfbd_stats.sort_values("season", ascending=False)

        stat_cols = ["passing_yards", "passing_tds", "rushing_yards", "rushing_tds",
                     "receiving_yards", "receiving_tds", "tackles", "sacks"]

        stats_name_col = "player" if "player" in cfbd_stats.columns else "player_name" if "player_name" in cfbd_stats.columns else None
        if stats_name_col:
            cfbd_stats = cfbd_stats.rename(columns={stats_name_col: "name_stats"})
            cfbd_stats["name_lower"] = cfbd_stats["name_stats"].str.lower().str.strip()
            cfbd_stats = cfbd_stats.drop_duplicates(subset=["name_lower"], keep="first")
            stats_lookup = cfbd_stats.set_index("name_lower")[
                [c for c in stat_cols if c in cfbd_stats.columns]
            ].to_dict("index")
            print(f"Stats available for {len(stats_lookup)} players")

    # --- Merge PFF grades ---
    pff_df = data.get("pff", pd.DataFrame())
    pff_lookup = {}
    if not pff_df.empty:
        pff_name_col = "player" if "player" in pff_df.columns else "player_name" if "player_name" in pff_df.columns else "name" if "name" in pff_df.columns else None
        if pff_name_col:
            pff_df["name_lower"] = pff_df[pff_name_col].str.lower().str.strip()
            if "pff_overall" in pff_df.columns:
                pff_df = pff_df.sort_values("pff_overall", ascending=False)
            pff_df = pff_df.drop_duplicates(subset=["name_lower"], keep="first")

            # Choose PFF columns based on mode
            if expanded_pff:
                pff_cols = [c for c in PFF_COLUMNS if c in pff_df.columns]
                print(f"  Expanded PFF mode: {len(pff_cols)} columns available")
            else:
                pff_cols = ["pff_overall", "pff_offense", "pff_defense", "pff_passing",
                           "pff_rushing", "pff_receiving"]
                pff_cols = [c for c in pff_cols if c in pff_df.columns]

            pff_lookup = pff_df.set_index("name_lower")[pff_cols].to_dict("index")
            print(f"PFF grades available for {len(pff_lookup)} players")

    # --- Enrich ESPN players with stats and PFF ---
    for idx, row in espn_df.iterrows():
        name_lower = str(row.get("name", "")).lower().strip()

        # Add stats
        if name_lower in stats_lookup:
            for stat, val in stats_lookup[name_lower].items():
                if pd.notna(val):
                    espn_df.at[idx, stat] = val

        # Add PFF
        if name_lower in pff_lookup:
            for grade, val in pff_lookup[name_lower].items():
                if pd.notna(val):
                    espn_df.at[idx, grade] = val

        # Add stars from On3 if available
        if name_lower in real_values:
            stars = real_values[name_lower].get("stars", None)
            if pd.notna(stars):
                espn_df.at[idx, "stars"] = stars

    return espn_df, real_values, on3_nil


def generate_calibrated_valuations(espn_df: pd.DataFrame, real_values: dict,
                                    on3_df: pd.DataFrame, model: 'CalibratedNILValuator') -> pd.DataFrame:
    """Generate valuations using the calibrated ML model."""
    print("\n" + "=" * 60)
    print("GENERATING CALIBRATED VALUATIONS")
    print("=" * 60)

    # --- Step 1: Train the model on On3 data ---
    print("\nTraining calibrated model on On3 real valuations...")
    cv_metrics = model.train(on3_df)
    print(model.get_calibration_report())

    # --- Step 2: Separate real vs predicted players ---
    real_mask = espn_df["name"].str.lower().str.strip().isin(real_values.keys())
    predict_df = espn_df[~real_mask].copy()
    real_df = espn_df[real_mask].copy()

    print(f"\nPlayers with real On3 values: {len(real_df)}")
    print(f"Players needing prediction: {len(predict_df)}")

    # --- Step 3: Predict with calibrated model ---
    if not predict_df.empty:
        predicted = model.predict(predict_df)

        # Keep only the columns we need from prediction
        for col in ["nil_value", "nil_tier", "confidence", "is_predicted"]:
            predict_df[col] = predicted[col].values
    else:
        predict_df["nil_value"] = []
        predict_df["nil_tier"] = []
        predict_df["confidence"] = []
        predict_df["is_predicted"] = []

    # --- Step 4: Assign real values ---
    real_nil_values = []
    real_nil_tiers = []
    for _, row in real_df.iterrows():
        name_lower = str(row["name"]).lower().strip()
        rv = real_values.get(name_lower, {})
        val = rv.get("nil_value", 0)
        real_nil_values.append(val)

        # Assign tier from value
        if val >= 2_000_000:
            real_nil_tiers.append("mega")
        elif val >= 500_000:
            real_nil_tiers.append("premium")
        elif val >= 100_000:
            real_nil_tiers.append("solid")
        elif val >= 25_000:
            real_nil_tiers.append("moderate")
        else:
            real_nil_tiers.append("entry")

    real_df["nil_value"] = real_nil_values
    real_df["nil_tier"] = real_nil_tiers
    real_df["confidence"] = "actual"
    real_df["is_predicted"] = False

    # --- Step 5: Combine ---
    combined = pd.concat([real_df, predict_df], ignore_index=True)
    combined = combined.sort_values("nil_value", ascending=False).reset_index(drop=True)

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
        from src.utils.data_loader import calculate_player_war
    except ImportError:
        print("WARNING: Could not import calculate_player_war. Skipping WAR computation.")
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

        if (idx + 1) % 5000 == 0:
            print(f"  WAR computed for {idx + 1}/{len(df)} players...")

    df["war"] = wars
    df["war_low"] = war_lows
    df["war_high"] = war_highs
    df["war_confidence"] = war_confs

    print(f"WAR computed for {len(df)} players")
    print(f"  Mean WAR:   {df['war'].mean():.2f}")
    print(f"  Median WAR: {df['war'].median():.2f}")
    print(f"  Max WAR:    {df['war'].max():.2f}")
    print(f"  High confidence: {(df['war_confidence'] == 'high').sum()}")
    print(f"  Medium confidence: {(df['war_confidence'] == 'medium').sum()}")

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

    if len(df) < 15000:
        issues.append(f"Expected 15K+ players, got {len(df)}")

    nil_count = df["nil_value"].notna().sum()
    if nil_count < 15000:
        issues.append(f"NIL coverage too low: {nil_count}")

    pff_count = df["pff_overall"].notna().sum() if "pff_overall" in df.columns else 0
    print(f"PFF match rate: {pff_count}/{len(df)} ({pff_count/len(df)*100:.1f}%)")

    portal_count = df["in_portal"].sum() if "in_portal" in df.columns else 0
    print(f"Portal players: {portal_count}")

    war_count = (df["war"] > 0).sum() if "war" in df.columns else 0
    print(f"Players with WAR > 0: {war_count}")

    if "war" in df.columns:
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
    print("PORTAL IQ - CALIBRATED VALUATION GENERATOR")
    if args.unified:
        print("  MODE: UNIFIED (full player table)")
    else:
        print("  MODE: LEGACY (NIL valuations only)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load all data
    data = load_data()

    # Build enriched player DataFrame
    espn_df, real_values, on3_df = build_player_dataframe(data, expanded_pff=args.unified)

    if espn_df.empty:
        print("ERROR: No player data!")
        return

    if on3_df.empty:
        print("ERROR: No On3 training data! Cannot calibrate.")
        return

    # Create and train calibrated model
    model = CalibratedNILValuator()

    # Generate calibrated valuations
    valuations_df = generate_calibrated_valuations(espn_df, real_values, on3_df, model)

    if valuations_df.empty:
        print("ERROR: No valuations generated!")
        return

    # Always save legacy format
    output_path = DATA_DIR / "portal_nil_valuations.csv"
    valuations_df.to_csv(output_path, index=False)
    print(f"\nSaved {len(valuations_df)} valuations to {output_path}")

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

        # Ensure name_normalized exists
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
    real_count = (~valuations_df["is_predicted"]).sum()
    pred_count = valuations_df["is_predicted"].sum()
    print(f"Total players with valuations: {len(valuations_df)}")
    print(f"  - With real On3 values: {real_count}")
    print(f"  - With calibrated predictions: {pred_count}")
    print(f"\nTier distribution:")
    print(valuations_df["nil_tier"].value_counts().to_string())
    print(f"\nValue statistics:")
    print(f"  Mean:   ${valuations_df['nil_value'].mean():,.0f}")
    print(f"  Median: ${valuations_df['nil_value'].median():,.0f}")
    print(f"  Total:  ${valuations_df['nil_value'].sum():,.0f}")
    print(f"\nTop 10 valuations:")
    top10 = valuations_df[["name", "position", "school", "nil_value", "nil_tier", "is_predicted"]].head(10)
    for i, row in top10.iterrows():
        src = "On3" if not row["is_predicted"] else "Pred"
        print(f"  {i+1:3}. ${row['nil_value']:>12,.0f} | {row['name']:25} | {row['position']:4} | {row['school']:20} | {row['nil_tier']:8} | {src}")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
