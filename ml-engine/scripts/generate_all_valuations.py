"""
Generate NIL Valuations for ALL Current FBS Players

This script:
1. Uses ESPN rosters as the base (21k+ current players with headshots)
2. Enriches with CFBD stats and PFF grades
3. Trains a calibrated ML model on real On3 NIL valuations (368 players)
4. Predicts calibrated valuations for ALL remaining players
5. Outputs comprehensive portal_nil_valuations.csv

Run: python scripts/generate_all_valuations.py
"""

import os
import sys
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


def build_player_dataframe(data: dict) -> tuple:
    """
    Build enriched player DataFrame from ESPN + CFBD + PFF data.

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
            pff_cols = ["pff_overall", "pff_offense", "pff_defense", "pff_passing",
                       "pff_rushing", "pff_receiving"]
            pff_lookup = pff_df.set_index("name_lower")[
                [c for c in pff_cols if c in pff_df.columns]
            ].to_dict("index")
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


def main():
    """Main execution."""
    print("=" * 60)
    print("PORTAL IQ - CALIBRATED VALUATION GENERATOR")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load all data
    data = load_data()

    # Build enriched player DataFrame
    espn_df, real_values, on3_df = build_player_dataframe(data)

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

    # Save valuations
    output_path = DATA_DIR / "portal_nil_valuations.csv"
    valuations_df.to_csv(output_path, index=False)
    print(f"\nSaved {len(valuations_df)} valuations to {output_path}")

    # Filter and save current portal
    current_portal = filter_current_portal(data)
    if not current_portal.empty:
        portal_output = DATA_DIR / "on3_transfer_portal_current.csv"
        current_portal.to_csv(portal_output, index=False)
        print(f"Saved {len(current_portal)} current portal entries to {portal_output}")

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
