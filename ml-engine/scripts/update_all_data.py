"""
Update All Data

Master script to:
1. Scrape On3 portal/NIL data
2. Collect CFBD rosters and stats
3. Merge all data sources
4. Retrain NIL prediction model
5. Generate updated valuations

Run: python scripts/update_all_data.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")


def run_on3_scraper():
    """Run the On3 scraper to get latest portal/NIL data."""
    print("\n" + "=" * 60)
    print("STEP 1: SCRAPING ON3 DATA")
    print("=" * 60)

    scraper_path = PROJECT_ROOT / "scripts" / "scrape_on3_full.py"
    if scraper_path.exists():
        result = subprocess.run(
            [sys.executable, str(scraper_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("On3 scraper completed successfully")
        else:
            print(f"On3 scraper failed: {result.stderr[:500]}")
    else:
        print("On3 scraper not found - skipping")


def collect_cfbd_data():
    """Collect roster and stats from CFBD API."""
    print("\n" + "=" * 60)
    print("STEP 2: COLLECTING CFBD DATA")
    print("=" * 60)

    from src.data_collection.college.cfb_api import CFBDataAPI

    api = CFBDataAPI()

    # Collect 2024 and 2025 data
    data = api.collect_all(years=[2024, 2025])

    # Save data
    api.save_data(data)

    return data


def merge_data_sources(cfbd_data: dict, current_season: int = 2025):
    """Merge CFBD rosters with On3 NIL/portal data.

    Training uses ALL historical data for better model accuracy.
    Output only includes current season players for display.
    """
    print("\n" + "=" * 60)
    print("STEP 3: MERGING DATA SOURCES")
    print("=" * 60)

    data_dir = PROJECT_ROOT / "data" / "processed"

    # Load On3 data
    nil_path = data_dir / "on3_all_nil_rankings.csv"
    portal_path = data_dir / "on3_transfer_portal.csv"
    team_path = data_dir / "on3_team_portal_rankings.csv"

    nil_df = pd.read_csv(nil_path) if nil_path.exists() else pd.DataFrame()
    portal_df = pd.read_csv(portal_path) if portal_path.exists() else pd.DataFrame()
    team_df = pd.read_csv(team_path) if team_path.exists() else pd.DataFrame()

    print(f"On3 NIL rankings: {len(nil_df)} (all used for training)")
    print(f"On3 portal: {len(portal_df)}")
    print(f"On3 team rankings: {len(team_df)}")

    # Get CFBD rosters
    rosters = cfbd_data.get("rosters", pd.DataFrame())
    stats = cfbd_data.get("player_stats", pd.DataFrame())
    talent = cfbd_data.get("team_talent", pd.DataFrame())
    records = cfbd_data.get("team_records", pd.DataFrame())

    print(f"CFBD rosters (all seasons): {len(rosters)}")
    print(f"CFBD stats: {len(stats)}")

    if rosters.empty:
        print("No CFBD roster data - using portal data only")
        return portal_df, nil_df, team_df

    # Merge stats into rosters
    if not stats.empty:
        rosters = rosters.merge(
            stats,
            on=["player_name", "team", "season"],
            how="left",
            suffixes=("", "_stats")
        )

    # Merge team data
    if not talent.empty:
        talent = talent.rename(columns={"school": "team"})
        rosters = rosters.merge(
            talent[["team", "talent", "year"]],
            left_on=["team", "season"],
            right_on=["team", "year"],
            how="left"
        )

    if not records.empty:
        records = records.rename(columns={"school": "team"})
        rosters = rosters.merge(
            records[["team", "year", "total_wins", "total_losses"]],
            left_on=["team", "season"],
            right_on=["team", "year"],
            how="left"
        )

    print(f"Merged CFBD data: {len(rosters)} players")

    # FILTER: Only use current season rosters for output
    current_rosters = rosters[rosters["season"] == current_season].copy()
    print(f"Current season ({current_season}) rosters: {len(current_rosters)} players")

    # Filter portal to current year BEFORE overwriting source column
    # Portal data has year in source field like "portal_wire_football_2026"
    if "source" in portal_df.columns:
        current_portal = portal_df[portal_df["source"].str.contains("2026|2025", na=False)].copy()
    else:
        current_portal = portal_df.copy()
    print(f"Current portal entries (2025-2026): {len(current_portal)}")

    # Now set source indicators
    current_portal["source"] = "portal"
    current_rosters["source"] = "cfbd"

    # Standardize names for matching
    def std_name(name):
        if pd.isna(name):
            return ""
        return str(name).lower().strip().replace(".", "").replace("-", " ")

    current_portal["name_std"] = current_portal["name"].apply(std_name)
    current_rosters["name_std"] = current_rosters["player_name"].apply(std_name)

    # Find players in current CFBD roster but not in portal
    portal_names = set(current_portal["name_std"])
    cfbd_only = current_rosters[~current_rosters["name_std"].isin(portal_names)].copy()
    cfbd_only = cfbd_only.rename(columns={"player_name": "name", "team": "school"})

    print(f"Current season players not in portal: {len(cfbd_only)}")

    # Combine current season only
    combined = pd.concat([current_portal, cfbd_only], ignore_index=True)
    print(f"Combined current players: {len(combined)}")

    return combined, nil_df, team_df


def train_model_and_predict(players_df, nil_df, team_df):
    """Train NIL model and generate predictions."""
    print("\n" + "=" * 60)
    print("STEP 4: TRAINING MODEL & GENERATING PREDICTIONS")
    print("=" * 60)

    from sklearn.ensemble import RandomForestRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_absolute_error, r2_score
    import joblib

    # Build school tier mapping
    school_tiers = {}
    if not team_df.empty and "team" in team_df.columns:
        if "year" in team_df.columns:
            team_df = team_df[team_df["year"] == team_df["year"].max()]
        if "overall_score" in team_df.columns:
            team_df = team_df.sort_values("overall_score", ascending=False)

        for idx, row in team_df.iterrows():
            team = row.get("team", "")
            rank = len(school_tiers) + 1
            if rank <= 15:
                tier = 6
            elif rank <= 35:
                tier = 5
            elif rank <= 65:
                tier = 4
            elif rank <= 100:
                tier = 3
            else:
                tier = 2
            school_tiers[team] = tier

    # Prepare training data from NIL rankings
    nil_df = nil_df.rename(columns={
        "nil_valuation": "nil_value",
        "recruiting_stars": "stars",
        "recruiting_rating": "rating",
    })

    train_df = nil_df[nil_df["nil_value"].notna() & (nil_df["nil_value"] > 0)].copy()

    def get_tier(school):
        if pd.isna(school):
            return 3
        for key, tier in school_tiers.items():
            if key.lower() in str(school).lower():
                return tier
        return 3

    position_values = {
        "QB": 1.0, "WR": 0.8, "RB": 0.6, "TE": 0.55,
        "OT": 0.7, "OG": 0.5, "C": 0.5, "OL": 0.55,
        "DE": 0.75, "DT": 0.65, "LB": 0.55, "CB": 0.7, "S": 0.6,
        "EDGE": 0.8, "DL": 0.65, "DB": 0.65,
        "K": 0.2, "P": 0.15, "SF": 0.85, "PG": 0.85,
    }

    # Engineer features for training data
    train_df["school_tier"] = train_df["school"].apply(get_tier)
    train_df["position_value"] = train_df["position"].map(position_values).fillna(0.5)
    train_df["is_qb"] = (train_df["position"] == "QB").astype(int)
    train_df["recruiting_stars"] = train_df["stars"].fillna(3)
    train_df["recruiting_rating"] = train_df["rating"].fillna(85) / 100
    train_df["log_followers"] = np.log1p(train_df["followers"].fillna(10000))
    train_df["rank_score"] = 1 / (1 + train_df["national_rank"].fillna(500) / 100)
    train_df["nil_rank_score"] = 1 / (1 + train_df["nil_rank"].fillna(200) / 50)

    feature_cols = [
        "school_tier", "position_value", "is_qb", "recruiting_stars",
        "recruiting_rating", "log_followers", "rank_score", "nil_rank_score"
    ]

    X = train_df[feature_cols].fillna(0).values
    y = np.log1p(train_df["nil_value"].values)

    # Train
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestRegressor(n_estimators=200, max_depth=12, min_samples_leaf=3, random_state=42, n_jobs=-1)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    mae = mean_absolute_error(np.expm1(y_test), np.expm1(y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"Model MAE: ${mae:,.0f}")
    print(f"Model R2: {r2:.3f}")

    # Save model
    model_dir = PROJECT_ROOT / "models" / "nil_national"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "model.joblib")
    joblib.dump(scaler, model_dir / "scaler.joblib")

    # Generate predictions for all players
    print(f"\nGenerating predictions for {len(players_df)} players...")

    # Create lookup for known NIL values
    known_values = {}
    for _, row in train_df.iterrows():
        key = str(row["name"]).lower().strip()
        known_values[key] = row["nil_value"]

    # Engineer features for all players
    players_df["school_col"] = players_df.get("school", players_df.get("destination_school", players_df.get("origin_school", "")))
    players_df["school_tier"] = players_df["school_col"].apply(get_tier)
    players_df["position_value"] = players_df["position"].map(position_values).fillna(0.5)
    players_df["is_qb"] = (players_df["position"] == "QB").astype(int)
    players_df["recruiting_stars"] = players_df.get("stars", pd.Series([3] * len(players_df))).fillna(3)
    players_df["recruiting_rating"] = players_df.get("rating", pd.Series([80] * len(players_df))).fillna(80) / 100
    players_df["log_followers"] = players_df["school_tier"] * 1.5 + players_df["recruiting_stars"] * 0.8
    players_df["rank_score"] = players_df["recruiting_stars"] / 5
    players_df["nil_rank_score"] = 0.1

    X_all = players_df[feature_cols].fillna(0).values
    X_all_scaled = scaler.transform(X_all)
    y_pred_all = np.expm1(model.predict(X_all_scaled))

    # Build results
    def get_tier_name(val):
        if val >= 1_000_000:
            return "mega"
        elif val >= 500_000:
            return "premium"
        elif val >= 100_000:
            return "solid"
        elif val >= 25_000:
            return "moderate"
        return "entry"

    results = []
    for idx, row in players_df.iterrows():
        name = row.get("name", row.get("player_name", ""))
        name_key = str(name).lower().strip()

        if name_key in known_values:
            nil_value = known_values[name_key]
            is_predicted = False
            confidence = "actual"
        else:
            nil_value = y_pred_all[idx]
            is_predicted = True
            stars = row.get("recruiting_stars", 3)
            tier = row.get("school_tier", 3)
            confidence = "high" if stars >= 4 and tier >= 4 else ("medium" if stars >= 3 else "low")

        results.append({
            "name": name,
            "position": row.get("position", ""),
            "school": row.get("school_col", row.get("school", "")),
            "origin_school": row.get("origin_school", row.get("from_school", "")),
            "destination_school": row.get("destination_school", row.get("to_school", "")),
            "status": row.get("status", ""),
            "nil_value_predicted": round(nil_value, 2),
            "nil_tier": get_tier_name(nil_value),
            "is_predicted": is_predicted,
            "confidence": confidence,
            "recruiting_stars": row.get("recruiting_stars", 3),
            "school_tier": row.get("school_tier", 3),
            "source": row.get("source", "portal"),
        })

    results_df = pd.DataFrame(results)

    # Deduplicate: keep highest NIL value per player
    before_dedup = len(results_df)
    results_df = results_df.sort_values("nil_value_predicted", ascending=False)
    results_df = results_df.drop_duplicates(subset=["name"], keep="first")
    results_df = results_df.reset_index(drop=True)
    print(f"\nDeduplicated: {before_dedup} -> {len(results_df)} unique players")

    # Save
    output_path = PROJECT_ROOT / "data" / "processed" / "portal_nil_valuations.csv"
    results_df.to_csv(output_path, index=False)

    actual = (~results_df["is_predicted"]).sum()
    predicted = results_df["is_predicted"].sum()

    print(f"\nSaved {len(results_df)} valuations")
    print(f"  Actual: {actual}")
    print(f"  Predicted: {predicted}")

    return results_df


def main():
    """Main execution."""
    print("=" * 60)
    print("PORTAL IQ DATA UPDATE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: On3 scraper (optional - skip if recent data exists)
    # run_on3_scraper()

    # Step 2: CFBD data
    cfbd_data = collect_cfbd_data()

    # Step 3: Merge data
    players_df, nil_df, team_df = merge_data_sources(cfbd_data)

    # Step 4: Train and predict
    results = train_model_and_predict(players_df, nil_df, team_df)

    print("\n" + "=" * 60)
    print("UPDATE COMPLETE")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Summary
    print("\nSUMMARY:")
    print(f"  Total players: {len(results):,}")
    print(f"  Tier distribution:")
    print(results["nil_tier"].value_counts().to_string())


if __name__ == "__main__":
    main()
