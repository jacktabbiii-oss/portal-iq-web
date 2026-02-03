"""
Build National NIL Valuations

This script:
1. Pulls full FBS rosters and stats from CFBD API
2. Merges with On3 NIL valuations (training data)
3. Trains NIL prediction model
4. Generates predicted NIL values for ALL players

Run: python scripts/build_national_valuations.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

# Import collectors and models
from src.data_collection.college.cfb_stats import CFBStatsCollector
from src.models.nil_valuator import NILValuator


def load_on3_nil_data():
    """Load On3 NIL valuations as training data."""
    nil_path = PROJECT_ROOT / "data" / "processed" / "on3_all_nil_rankings.csv"

    if not nil_path.exists():
        print(f"ERROR: On3 NIL data not found at {nil_path}")
        return pd.DataFrame()

    df = pd.read_csv(nil_path)
    print(f"Loaded {len(df)} On3 NIL valuations")

    # Standardize columns
    df = df.rename(columns={
        'nil_valuation': 'nil_value',
        'recruiting_stars': 'stars',
        'recruiting_rating': 'rating',
    })

    return df


def collect_cfbd_data(years=[2024, 2025]):
    """Collect full roster and stats from CFBD."""
    print("\n" + "=" * 60)
    print("COLLECTING CFBD DATA")
    print("=" * 60)

    collector = CFBStatsCollector(data_dir=str(PROJECT_ROOT / "data"))

    # Collect all data
    start_year = min(years)
    end_year = max(years)

    data = collector.collect_all(start_year=start_year, end_year=end_year)

    return data


def merge_data(cfbd_data: dict, on3_nil: pd.DataFrame) -> pd.DataFrame:
    """Merge CFBD roster/stats with On3 NIL valuations."""
    print("\n" + "=" * 60)
    print("MERGING DATA SOURCES")
    print("=" * 60)

    # Get roster data
    roster_df = cfbd_data.get('player_info', pd.DataFrame())
    stats_df = cfbd_data.get('player_stats', pd.DataFrame())
    team_df = cfbd_data.get('team_data', pd.DataFrame())

    if roster_df.empty:
        print("ERROR: No roster data collected")
        return pd.DataFrame()

    print(f"Roster: {len(roster_df)} players")
    print(f"Stats: {len(stats_df)} records")
    print(f"Teams: {len(team_df)} team-seasons")

    # Get most recent season per player
    roster_df = roster_df.sort_values('season', ascending=False)
    roster_df = roster_df.drop_duplicates(subset=['player_name', 'team'], keep='first')
    print(f"Deduplicated roster: {len(roster_df)} unique players")

    # Merge stats with roster (aggregate stats per player)
    if not stats_df.empty:
        # Pivot stats if needed
        stats_agg = stats_df.groupby(['player_name', 'team']).agg({
            col: 'sum' if col.endswith('_YDS') or col.endswith('_TD') else 'first'
            for col in stats_df.columns if col not in ['player_name', 'team']
        }).reset_index()

        merged = roster_df.merge(
            stats_agg,
            on=['player_name', 'team'],
            how='left',
            suffixes=('', '_stats')
        )
    else:
        merged = roster_df.copy()

    # Merge team data
    if not team_df.empty:
        team_latest = team_df.sort_values('season', ascending=False).drop_duplicates('team', keep='first')
        merged = merged.merge(
            team_latest[['team', 'total_wins', 'total_losses', 'sp_overall', 'sp_offense', 'sp_defense', 'talent_composite']],
            on='team',
            how='left'
        )

    # Standardize name for matching with On3
    merged['name_std'] = merged['player_name'].str.lower().str.strip()
    merged['name_std'] = merged['name_std'].str.replace(r'[^a-z\s]', '', regex=True)
    merged['name_std'] = merged['name_std'].str.replace(r'\s+', ' ', regex=True)

    # Same for On3
    on3_nil['name_std'] = on3_nil['name'].str.lower().str.strip()
    on3_nil['name_std'] = on3_nil['name_std'].str.replace(r'[^a-z\s]', '', regex=True)
    on3_nil['name_std'] = on3_nil['name_std'].str.replace(r'\s+', ' ', regex=True)

    # Merge On3 NIL values
    merged = merged.merge(
        on3_nil[['name_std', 'nil_value', 'stars', 'rating', 'followers']],
        on='name_std',
        how='left'
    )

    # Count matched
    matched = merged['nil_value'].notna().sum()
    print(f"Matched {matched} players with On3 NIL values")

    return merged


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer features for NIL prediction."""
    print("\n" + "=" * 60)
    print("ENGINEERING FEATURES")
    print("=" * 60)

    df = df.copy()

    # School tier based on team metrics
    def get_school_tier(row):
        """Assign school tier 1-6 based on wins and talent."""
        wins = row.get('total_wins', 0) or 0
        talent = row.get('talent_composite', 0) or 0
        sp = row.get('sp_overall', 0) or 0

        score = wins * 2 + talent / 100 + max(0, sp) / 5

        if score > 25:
            return 6  # Blue blood
        elif score > 20:
            return 5  # Elite
        elif score > 15:
            return 4  # Power brand
        elif score > 10:
            return 3  # P4 mid
        elif score > 5:
            return 2  # G5 strong
        else:
            return 1  # G5

    df['school_tier'] = df.apply(get_school_tier, axis=1)

    # Position value multiplier
    position_values = {
        'QB': 1.0, 'WR': 0.8, 'RB': 0.6, 'TE': 0.55,
        'OT': 0.7, 'OG': 0.5, 'C': 0.5, 'OL': 0.5,
        'DE': 0.75, 'DT': 0.65, 'LB': 0.55, 'CB': 0.7, 'S': 0.6,
        'EDGE': 0.8, 'DL': 0.65, 'DB': 0.65,
        'K': 0.2, 'P': 0.15, 'LS': 0.1,
        'ATH': 0.5,
    }
    df['position_value'] = df['position'].map(position_values).fillna(0.4)

    # QB premium flag
    df['is_qb'] = (df['position'] == 'QB').astype(int)

    # Recruiting stars (use On3 or default based on team tier)
    df['recruiting_stars'] = df['stars'].fillna(
        df['school_tier'].map({6: 4, 5: 3.5, 4: 3, 3: 2.5, 2: 2, 1: 2})
    )

    # Social followers (use On3 or estimate)
    df['followers'] = df['followers'].fillna(
        df['school_tier'] * 5000 + df['recruiting_stars'] * 2000
    )
    df['log_followers'] = np.log1p(df['followers'])

    # Production score (from stats if available)
    stat_cols = [c for c in df.columns if '_YDS' in c or '_TD' in c]
    if stat_cols:
        df['production_score'] = df[stat_cols].fillna(0).sum(axis=1) / 100
        df['production_score'] = df['production_score'].clip(0, 100)
    else:
        # Estimate from position and tier
        df['production_score'] = df['school_tier'] * 5 + df['recruiting_stars'] * 8

    # Year in school encoding
    year_encoding = {'FR': 1, 'SO': 2, 'JR': 3, 'SR': 4, 'GR': 5}
    df['years_in_college'] = df['year'].map(year_encoding).fillna(2)

    # Team wins
    df['team_wins'] = df['total_wins'].fillna(6)

    # Interaction features
    df['school_x_production'] = df['school_tier'] * df['production_score']
    df['qb_x_production'] = df['is_qb'] * df['production_score']
    df['social_x_tier'] = df['log_followers'] * df['school_tier']

    # Market size estimate (based on team)
    big_markets = ['USC', 'UCLA', 'Miami', 'Texas', 'Ohio State', 'Michigan', 'Penn State']
    df['is_big_market'] = df['team'].isin(big_markets).astype(int)

    print(f"Features engineered: {df.shape[1]} columns")
    print(f"Players with known NIL: {df['nil_value'].notna().sum()}")
    print(f"Players to predict: {df['nil_value'].isna().sum()}")

    return df


def train_and_predict(df: pd.DataFrame) -> pd.DataFrame:
    """Train model on known NIL values and predict for all players."""
    print("\n" + "=" * 60)
    print("TRAINING MODEL")
    print("=" * 60)

    # Split into training (known NIL) and prediction (unknown NIL)
    train_df = df[df['nil_value'].notna()].copy()
    predict_df = df[df['nil_value'].isna()].copy()

    print(f"Training samples: {len(train_df)}")
    print(f"Players to predict: {len(predict_df)}")

    if len(train_df) < 50:
        print("WARNING: Low training data. Using simplified model.")

    # Define feature columns
    feature_cols = [
        'school_tier', 'position_value', 'is_qb', 'recruiting_stars',
        'log_followers', 'production_score', 'years_in_college', 'team_wins',
        'school_x_production', 'qb_x_production', 'social_x_tier', 'is_big_market',
    ]

    # Check which features exist
    available_features = [c for c in feature_cols if c in df.columns]
    print(f"Using {len(available_features)} features: {available_features}")

    # Assign tier based on value
    def assign_tier(val):
        if val >= 1_000_000:
            return 'mega'
        elif val >= 500_000:
            return 'premium'
        elif val >= 100_000:
            return 'solid'
        elif val >= 25_000:
            return 'moderate'
        else:
            return 'entry'

    train_df['nil_tier'] = train_df['nil_value'].apply(assign_tier)

    # Create feature DataFrames
    X_train = train_df[available_features].fillna(0)

    # Initialize and train valuator
    valuator = NILValuator(
        model_dir=str(PROJECT_ROOT / "models" / "nil_national"),
        output_dir=str(PROJECT_ROOT / "outputs" / "reports")
    )

    # Prepare training data
    train_data = X_train.copy()
    train_data['nil_value'] = train_df['nil_value'].values
    train_data['nil_tier'] = train_df['nil_tier'].values

    # Train
    results = valuator.train(train_data, target_col='nil_value', tier_col='nil_tier')

    # Predict for all players
    print("\n" + "=" * 60)
    print("PREDICTING NIL VALUES")
    print("=" * 60)

    all_players = df.copy()
    predictions = []

    for idx, row in all_players.iterrows():
        features = {col: row.get(col, 0) for col in available_features}

        if pd.notna(row.get('nil_value')):
            # Use actual value
            predictions.append({
                'player_name': row['player_name'],
                'team': row['team'],
                'position': row['position'],
                'nil_value': row['nil_value'],
                'nil_value_predicted': row['nil_value'],
                'nil_tier': assign_tier(row['nil_value']),
                'is_predicted': False,
                'confidence': 'actual',
            })
        else:
            # Predict
            try:
                pred = valuator.predict(features)
                predictions.append({
                    'player_name': row['player_name'],
                    'team': row['team'],
                    'position': row['position'],
                    'nil_value': None,
                    'nil_value_predicted': pred['predicted_nil_value'],
                    'nil_tier': pred['predicted_tier'],
                    'is_predicted': True,
                    'confidence': pred['confidence'],
                })
            except Exception as e:
                # Fallback: simple formula
                estimated = (
                    row.get('school_tier', 3) * 20000 +
                    row.get('position_value', 0.5) * 50000 +
                    row.get('recruiting_stars', 3) * 15000 +
                    row.get('production_score', 20) * 1000
                )
                predictions.append({
                    'player_name': row['player_name'],
                    'team': row['team'],
                    'position': row['position'],
                    'nil_value': None,
                    'nil_value_predicted': estimated,
                    'nil_tier': assign_tier(estimated),
                    'is_predicted': True,
                    'confidence': 'low',
                })

    result_df = pd.DataFrame(predictions)

    print(f"\nTotal predictions: {len(result_df)}")
    print(f"Actual values: {(~result_df['is_predicted']).sum()}")
    print(f"Predicted values: {result_df['is_predicted'].sum()}")

    return result_df


def save_results(df: pd.DataFrame):
    """Save national valuations to processed directory."""
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)

    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Full results
    output_path = output_dir / "national_nil_valuations.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} player valuations to {output_path}")

    # Summary stats
    print("\n" + "-" * 40)
    print("SUMMARY STATISTICS")
    print("-" * 40)

    print(f"\nTotal players: {len(df):,}")
    print(f"Actual NIL values: {(~df['is_predicted']).sum():,}")
    print(f"Predicted NIL values: {df['is_predicted'].sum():,}")

    print(f"\nValue distribution (predicted):")
    predicted = df[df['is_predicted']]['nil_value_predicted']
    print(f"  Mean: ${predicted.mean():,.0f}")
    print(f"  Median: ${predicted.median():,.0f}")
    print(f"  Min: ${predicted.min():,.0f}")
    print(f"  Max: ${predicted.max():,.0f}")

    print(f"\nTier distribution:")
    print(df['nil_tier'].value_counts().to_string())

    print(f"\nTop 20 predicted valuations:")
    top_20 = df.nlargest(20, 'nil_value_predicted')
    for i, row in top_20.iterrows():
        actual = f" (actual: ${row['nil_value']:,.0f})" if row['nil_value'] else ""
        print(f"  {row['player_name']} ({row['team']}, {row['position']}): ${row['nil_value_predicted']:,.0f}{actual}")


def main():
    """Main execution."""
    print("=" * 60)
    print("NATIONAL NIL VALUATION BUILDER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1: Load On3 NIL data (training data)
    on3_nil = load_on3_nil_data()
    if on3_nil.empty:
        print("Cannot proceed without On3 NIL training data")
        sys.exit(1)

    # Step 2: Collect CFBD data
    cfbd_data = collect_cfbd_data(years=[2024, 2025])

    # Check if we got roster data
    if cfbd_data.get('player_info', pd.DataFrame()).empty:
        print("\nERROR: No roster data collected from CFBD.")
        print("Possible causes:")
        print("  1. Invalid API key")
        print("  2. Rate limit exceeded")
        print("  3. Network issues")
        print("\nCheck your CFBD_API_KEY in .env")
        sys.exit(1)

    # Step 3: Merge data
    merged_df = merge_data(cfbd_data, on3_nil)
    if merged_df.empty:
        print("Cannot proceed without merged data")
        sys.exit(1)

    # Step 4: Engineer features
    featured_df = engineer_features(merged_df)

    # Step 5: Train and predict
    results_df = train_and_predict(featured_df)

    # Step 6: Save results
    save_results(results_df)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
