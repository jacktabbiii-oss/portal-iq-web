"""
Generate NIL Valuations for ALL Current FBS Players

This script:
1. Uses ESPN rosters as the base (21k+ current players with headshots)
2. Enriches with CFBD stats and PFF grades
3. Merges with On3 NIL rankings (for real valuations)
4. Generates predicted valuations for ALL remaining players
5. Outputs comprehensive portal_nil_valuations.csv

Run: python scripts/generate_all_valuations.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

DATA_DIR = PROJECT_ROOT / "data" / "processed"


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

    # On3 NIL rankings (real valuations for top players)
    nil_path = DATA_DIR / "on3_all_nil_rankings.csv"
    if nil_path.exists():
        data["on3_nil"] = pd.read_csv(nil_path)
        print(f"On3 NIL rankings: {len(data['on3_nil'])} players with real values")
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


def get_school_tier(school: str, team_talent_df: pd.DataFrame) -> int:
    """Get school tier (1-6) based on team talent rankings."""
    if pd.isna(school):
        return 3

    school_clean = str(school).lower().strip()

    # Blue bloods (tier 6)
    blue_bloods = ["alabama", "ohio state", "georgia", "texas", "usc", "michigan", "notre dame", "oklahoma"]
    for bb in blue_bloods:
        if bb in school_clean:
            return 6

    # Elite programs (tier 5)
    elite = ["lsu", "florida", "penn state", "oregon", "clemson", "tennessee", "texas a&m", "miami"]
    for e in elite:
        if e in school_clean:
            return 5

    # Power brand (tier 4)
    power = ["florida state", "auburn", "wisconsin", "iowa", "ucla", "washington", "utah", "ole miss"]
    for p in power:
        if p in school_clean:
            return 4

    # Check talent rankings (skip if data is bad)
    try:
        if not team_talent_df.empty and "school" in team_talent_df.columns:
            # Ensure school column is string type
            school_col = team_talent_df["school"].dropna().astype(str)
            if len(school_col) > 0:
                match = school_col[school_col.str.lower().str.contains(school_clean, na=False)]
                if not match.empty:
                    rank = match.index[0]
                    if rank < 25:
                        return 5
                    elif rank < 50:
                        return 4
                    elif rank < 75:
                        return 3
    except Exception:
        pass  # Fallback to default tier

    return 3  # Default mid-tier


def calculate_nil_value(row, team_talent_df: pd.DataFrame) -> dict:
    """Calculate NIL valuation for a player."""

    # Position base values
    position_base = {
        "QB": 150000, "WR": 80000, "RB": 60000, "TE": 50000,
        "OT": 70000, "OG": 45000, "C": 45000, "OL": 55000,
        "DE": 75000, "DT": 55000, "EDGE": 85000, "DL": 60000,
        "LB": 55000, "CB": 70000, "S": 55000, "DB": 60000,
        "K": 15000, "P": 12000, "LS": 10000, "ATH": 50000,
    }

    position = str(row.get("position", "ATH")).upper().strip()
    base_value = position_base.get(position, 50000)

    # School tier multiplier
    school = row.get("team", row.get("school", ""))
    tier = get_school_tier(school, team_talent_df)
    tier_mult = {6: 2.5, 5: 1.8, 4: 1.4, 3: 1.0, 2: 0.7, 1: 0.5}.get(tier, 1.0)

    # Class year multiplier
    class_year = str(row.get("class_year", "")).lower()
    class_mult = {
        "senior": 0.9, "junior": 1.1, "sophomore": 1.0,
        "freshman": 0.8, "redshirt": 0.85
    }
    year_mult = 1.0
    for year, mult in class_mult.items():
        if year in class_year:
            year_mult = mult
            break

    # Stars multiplier (if available)
    stars = row.get("stars", row.get("recruiting_stars", 3))
    if pd.isna(stars):
        stars = 3
    stars = int(stars) if stars else 3
    stars_mult = {5: 2.0, 4: 1.5, 3: 1.0, 2: 0.7, 1: 0.5}.get(stars, 1.0)

    # PFF grade bonus (if available)
    pff_grade = row.get("pff_overall", row.get("pff_grade", 0))
    if pd.notna(pff_grade) and pff_grade > 0:
        pff_mult = 1.0 + (pff_grade - 60) / 100  # 60 is average
    else:
        pff_mult = 1.0

    # Stats bonus (simplified)
    stats_bonus = 0
    if pd.notna(row.get("passing_yards")) and row.get("passing_yards", 0) > 0:
        stats_bonus += min(row["passing_yards"] / 100, 50000)
    if pd.notna(row.get("rushing_yards")) and row.get("rushing_yards", 0) > 0:
        stats_bonus += min(row["rushing_yards"] / 50, 30000)
    if pd.notna(row.get("receiving_yards")) and row.get("receiving_yards", 0) > 0:
        stats_bonus += min(row["receiving_yards"] / 50, 30000)
    if pd.notna(row.get("tackles")) and row.get("tackles", 0) > 0:
        stats_bonus += min(row["tackles"] * 200, 20000)
    if pd.notna(row.get("sacks")) and row.get("sacks", 0) > 0:
        stats_bonus += min(row["sacks"] * 5000, 30000)

    # Calculate total
    value = base_value * tier_mult * year_mult * stars_mult * pff_mult + stats_bonus

    # Determine tier
    if value >= 1000000:
        nil_tier = "mega"
    elif value >= 500000:
        nil_tier = "premium"
    elif value >= 100000:
        nil_tier = "solid"
    elif value >= 25000:
        nil_tier = "moderate"
    else:
        nil_tier = "entry"

    return {
        "nil_value": round(value, 2),
        "nil_tier": nil_tier,
        "school_tier": tier,
        "confidence": "high" if pff_grade > 0 or stats_bonus > 0 else "medium",
        "is_predicted": True,
    }


def generate_valuations(data: dict) -> pd.DataFrame:
    """Generate NIL valuations for all current players."""
    print("\n" + "=" * 60)
    print("GENERATING VALUATIONS")
    print("=" * 60)

    espn_df = data["espn"].copy()
    if espn_df.empty:
        print("ERROR: No ESPN roster data!")
        return pd.DataFrame()

    # Standardize ESPN data
    espn_df = espn_df.rename(columns={
        "team": "school",
        "espn_id": "player_id",
    })

    # Clean school names (remove "Wildcats", "Bulldogs", etc.)
    if "school" in espn_df.columns:
        espn_df["school"] = espn_df["school"].apply(
            lambda x: " ".join(str(x).split()[:-1]) if pd.notna(x) and len(str(x).split()) > 1 else x
        )

    print(f"Starting with {len(espn_df)} ESPN players")

    # Merge On3 NIL rankings (real values)
    on3_nil = data.get("on3_nil", pd.DataFrame())
    if not on3_nil.empty and "name" in on3_nil.columns:
        # Create lookup for real NIL values
        real_values = {}
        for _, row in on3_nil.iterrows():
            name = str(row.get("name", "")).lower().strip()
            val = row.get("nil_valuation", row.get("nil_value", 0))
            if name and pd.notna(val) and val > 0:
                real_values[name] = {
                    "nil_value": val,
                    "nil_tier": row.get("nil_tier", "solid"),
                    "stars": row.get("stars", row.get("recruiting_stars", 3)),
                    "is_predicted": False,
                }
        print(f"Found {len(real_values)} players with real On3 NIL values")
    else:
        real_values = {}

    # Merge CFBD stats
    cfbd_stats = data.get("cfbd_stats", pd.DataFrame())
    if not cfbd_stats.empty:
        # Get most recent stats per player
        if "season" in cfbd_stats.columns:
            cfbd_stats = cfbd_stats.sort_values("season", ascending=False)

        stat_cols = ["passing_yards", "passing_tds", "rushing_yards", "rushing_tds",
                     "receiving_yards", "receiving_tds", "tackles", "sacks"]

        # Standardize name column
        stats_name_col = "player" if "player" in cfbd_stats.columns else "player_name" if "player_name" in cfbd_stats.columns else None
        if stats_name_col:
            cfbd_stats = cfbd_stats.rename(columns={stats_name_col: "name_stats"})
            cfbd_stats["name_lower"] = cfbd_stats["name_stats"].str.lower().str.strip()
            cfbd_stats = cfbd_stats.drop_duplicates(subset=["name_lower"], keep="first")

            # Create stats lookup
            stats_lookup = cfbd_stats.set_index("name_lower")[
                [c for c in stat_cols if c in cfbd_stats.columns]
            ].to_dict("index")
            print(f"Stats available for {len(stats_lookup)} players")
        else:
            stats_lookup = {}
    else:
        stats_lookup = {}

    # Merge PFF grades
    pff_df = data.get("pff", pd.DataFrame())
    if not pff_df.empty:
        pff_name_col = "player" if "player" in pff_df.columns else "player_name" if "player_name" in pff_df.columns else "name" if "name" in pff_df.columns else None
        if pff_name_col:
            pff_df["name_lower"] = pff_df[pff_name_col].str.lower().str.strip()
            # Get highest grade per player
            if "pff_overall" in pff_df.columns:
                pff_df = pff_df.sort_values("pff_overall", ascending=False)
            pff_df = pff_df.drop_duplicates(subset=["name_lower"], keep="first")

            pff_cols = ["pff_overall", "pff_offense", "pff_defense", "pff_passing",
                       "pff_rushing", "pff_receiving"]
            pff_lookup = pff_df.set_index("name_lower")[
                [c for c in pff_cols if c in pff_df.columns]
            ].to_dict("index")
            print(f"PFF grades available for {len(pff_lookup)} players")
        else:
            pff_lookup = {}
    else:
        pff_lookup = {}

    # Get team talent for school tiers
    team_talent = data.get("team_talent", pd.DataFrame())

    # Generate valuations
    results = []
    real_count = 0
    predicted_count = 0

    for idx, row in espn_df.iterrows():
        name = str(row.get("name", "")).strip()
        name_lower = name.lower()

        # Start with ESPN data
        player = {
            "name": name,
            "player_id": row.get("player_id", idx),
            "position": row.get("position", "ATH"),
            "school": row.get("school", "Unknown"),
            "class_year": row.get("class_year", ""),
            "height": row.get("height", ""),
            "weight": row.get("weight", ""),
            "headshot_url": row.get("headshot_url", ""),
        }

        # Add stats if available
        if name_lower in stats_lookup:
            for stat, val in stats_lookup[name_lower].items():
                if pd.notna(val):
                    player[stat] = val

        # Add PFF grades if available
        if name_lower in pff_lookup:
            for grade, val in pff_lookup[name_lower].items():
                if pd.notna(val):
                    player[grade] = val

        # Check for real NIL value
        if name_lower in real_values:
            real_data = real_values[name_lower]
            player["nil_value"] = real_data["nil_value"]
            player["nil_tier"] = real_data["nil_tier"]
            player["stars"] = real_data.get("stars", 3)
            player["is_predicted"] = False
            player["confidence"] = "actual"
            real_count += 1
        else:
            # Generate predicted valuation
            val_data = calculate_nil_value(player, team_talent)
            player.update(val_data)
            predicted_count += 1

        results.append(player)

    print(f"\nGenerated valuations:")
    print(f"  Real On3 values: {real_count}")
    print(f"  Predicted values: {predicted_count}")
    print(f"  Total: {len(results)}")

    return pd.DataFrame(results)


def filter_current_portal(data: dict) -> pd.DataFrame:
    """Filter portal data to current cycle only (2025-2026)."""
    print("\n" + "=" * 60)
    print("FILTERING PORTAL TO CURRENT CYCLE")
    print("=" * 60)

    portal_df = data.get("portal", pd.DataFrame())
    if portal_df.empty:
        return pd.DataFrame()

    print(f"Total portal entries: {len(portal_df)}")

    # Filter by year in source or date fields
    if "source" in portal_df.columns:
        current = portal_df[portal_df["source"].str.contains("2026|2025", na=False)].copy()
    elif "year" in portal_df.columns:
        current = portal_df[portal_df["year"].isin([2025, 2026])].copy()
    elif "commit_date" in portal_df.columns:
        portal_df["commit_date"] = pd.to_datetime(portal_df["commit_date"], errors="coerce")
        current = portal_df[portal_df["commit_date"].dt.year >= 2025].copy()
    else:
        # Keep most recent entries
        current = portal_df.head(5000).copy()

    print(f"Current cycle (2025-2026): {len(current)} entries")

    return current


def main():
    """Main execution."""
    print("=" * 60)
    print("PORTAL IQ - COMPREHENSIVE VALUATION GENERATOR")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load all data
    data = load_data()

    # Generate valuations for all players
    valuations_df = generate_valuations(data)

    if valuations_df.empty:
        print("ERROR: No valuations generated!")
        return

    # Sort by NIL value
    valuations_df = valuations_df.sort_values("nil_value", ascending=False)
    valuations_df = valuations_df.reset_index(drop=True)

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
    print(f"Total players with valuations: {len(valuations_df)}")
    print(f"  - With real On3 values: {(~valuations_df['is_predicted']).sum()}")
    print(f"  - With predicted values: {valuations_df['is_predicted'].sum()}")
    print(f"\nTier distribution:")
    print(valuations_df["nil_tier"].value_counts().to_string())
    print(f"\nTop 10 valuations:")
    print(valuations_df[["name", "position", "school", "nil_value", "nil_tier"]].head(10).to_string())

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
