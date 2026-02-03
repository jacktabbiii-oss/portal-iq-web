"""
Build NIL Valuations from Portal Data

Uses existing portal data (14,450 players) as the roster base,
trains on On3 NIL rankings, and generates proprietary valuations.

Run: python scripts/build_nil_valuations_from_portal.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import joblib


def load_data():
    """Load all available data sources."""
    data_dir = PROJECT_ROOT / "data" / "processed"

    print("Loading data sources...")

    # Portal data (our roster base)
    portal_path = data_dir / "on3_transfer_portal.csv"
    portal_df = pd.read_csv(portal_path)
    print(f"  Portal players: {len(portal_df):,}")

    # NIL rankings (training data with known values)
    nil_path = data_dir / "on3_all_nil_rankings.csv"
    nil_df = pd.read_csv(nil_path)
    print(f"  NIL rankings: {len(nil_df):,}")

    # NIL 100 (top 100 with most data)
    nil100_path = data_dir / "on3_college_nil_100.csv"
    if nil100_path.exists():
        nil100_df = pd.read_csv(nil100_path)
        print(f"  NIL 100: {len(nil100_df):,}")
    else:
        nil100_df = pd.DataFrame()

    # Team rankings (for school tier data)
    team_path = data_dir / "on3_team_portal_rankings.csv"
    team_df = pd.read_csv(team_path)
    print(f"  Team rankings: {len(team_df):,}")

    return portal_df, nil_df, nil100_df, team_df


def build_school_tiers(team_df: pd.DataFrame) -> dict:
    """Build school tier mapping from team rankings."""

    # Get 2026 rankings
    if 'year' in team_df.columns:
        rankings = team_df[team_df['year'] == 2026].copy()
    else:
        rankings = team_df.copy()

    # Sort by overall_score
    if 'overall_score' in rankings.columns:
        rankings = rankings.sort_values('overall_score', ascending=False)
    elif 'points' in rankings.columns:
        rankings = rankings.sort_values('points', ascending=False)

    # Assign tiers based on ranking
    school_tiers = {}
    for idx, row in rankings.iterrows():
        team = row.get('team', row.get('name', ''))
        rank = len(school_tiers) + 1

        if rank <= 15:
            tier = 6  # Blue blood
        elif rank <= 35:
            tier = 5  # Elite
        elif rank <= 65:
            tier = 4  # Power brand
        elif rank <= 100:
            tier = 3  # P4 mid
        elif rank <= 130:
            tier = 2  # G5 strong
        else:
            tier = 1  # G5

        school_tiers[team] = tier

    # Add known blue bloods manually
    blue_bloods = ['Alabama', 'Ohio State', 'Georgia', 'Texas', 'USC', 'Michigan',
                   'Oklahoma', 'Notre Dame', 'LSU', 'Clemson', 'Florida', 'Penn State']
    for school in blue_bloods:
        for key in school_tiers:
            if school.lower() in key.lower():
                school_tiers[key] = max(school_tiers.get(key, 1), 5)

    return school_tiers


def prepare_training_data(nil_df: pd.DataFrame, school_tiers: dict) -> pd.DataFrame:
    """Prepare training data from NIL rankings."""

    df = nil_df.copy()

    # Standardize column names
    df = df.rename(columns={
        'nil_valuation': 'nil_value',
        'recruiting_stars': 'stars',
        'recruiting_rating': 'rating',
    })

    # Remove rows without NIL value
    df = df[df['nil_value'].notna() & (df['nil_value'] > 0)]

    # Extract school tier
    def get_tier(school):
        if pd.isna(school):
            return 3
        school_str = str(school).lower()
        for key, tier in school_tiers.items():
            if key.lower() in school_str or school_str in key.lower():
                return tier
        return 3  # Default to P4 mid

    df['school_tier'] = df['school'].apply(get_tier)

    # Position value
    position_values = {
        'QB': 1.0, 'WR': 0.8, 'RB': 0.6, 'TE': 0.55,
        'OT': 0.7, 'OG': 0.5, 'C': 0.5, 'OL': 0.55,
        'DE': 0.75, 'DT': 0.65, 'LB': 0.55, 'CB': 0.7, 'S': 0.6,
        'EDGE': 0.8, 'DL': 0.65, 'DB': 0.65,
        'K': 0.2, 'P': 0.15, 'LS': 0.1,
        'SF': 0.85, 'PG': 0.85, 'SG': 0.8, 'PF': 0.75, 'ATH': 0.5,
    }
    df['position_value'] = df['position'].map(position_values).fillna(0.5)

    # Is QB
    df['is_qb'] = (df['position'] == 'QB').astype(int)

    # Recruiting stars
    df['recruiting_stars'] = df['stars'].fillna(3)

    # Recruiting rating
    df['recruiting_rating'] = df['rating'].fillna(85) / 100  # Normalize to 0-1

    # Social followers
    df['followers'] = df['followers'].fillna(10000)
    df['log_followers'] = np.log1p(df['followers'])

    # National rank (inverse - lower is better)
    df['national_rank'] = df['national_rank'].fillna(500)
    df['rank_score'] = 1 / (1 + df['national_rank'] / 100)

    # NIL rank
    df['nil_rank'] = df['nil_rank'].fillna(200)
    df['nil_rank_score'] = 1 / (1 + df['nil_rank'] / 50)

    return df


def prepare_prediction_data(portal_df: pd.DataFrame, school_tiers: dict) -> pd.DataFrame:
    """Prepare portal players for prediction."""

    df = portal_df.copy()

    # Standardize columns
    df = df.rename(columns={
        'nil_valuation': 'nil_value',
        'from_school': 'origin_school',
        'to_school': 'destination_school',
    })

    # Use destination school if available, else origin
    df['school'] = df['destination_school'].fillna(df['origin_school'])

    # School tier
    def get_tier(school):
        if pd.isna(school):
            return 3
        school_str = str(school).lower()
        for key, tier in school_tiers.items():
            if key.lower() in school_str or school_str in key.lower():
                return tier
        return 3

    df['school_tier'] = df['school'].apply(get_tier)

    # Position value
    position_values = {
        'QB': 1.0, 'WR': 0.8, 'RB': 0.6, 'TE': 0.55,
        'OT': 0.7, 'OG': 0.5, 'C': 0.5, 'OL': 0.55,
        'DE': 0.75, 'DT': 0.65, 'LB': 0.55, 'CB': 0.7, 'S': 0.6,
        'EDGE': 0.8, 'DL': 0.65, 'DB': 0.65,
        'K': 0.2, 'P': 0.15, 'LS': 0.1,
        'ATH': 0.5, 'IOL': 0.5,
    }
    df['position_value'] = df['position'].map(position_values).fillna(0.5)

    # Is QB
    df['is_qb'] = (df['position'] == 'QB').astype(int)

    # Recruiting stars
    df['recruiting_stars'] = df['stars'].fillna(3)

    # Recruiting rating
    if 'rating' in df.columns:
        df['recruiting_rating'] = df['rating'].fillna(80) / 100
    else:
        df['recruiting_rating'] = 0.8

    # No social data for most portal players - estimate based on tier
    df['log_followers'] = df['school_tier'] * 1.5 + df['recruiting_stars'] * 0.8

    # Rank scores (portal players don't have NIL rank yet)
    if 'national_rank' in df.columns:
        df['national_rank'] = df['national_rank'].fillna(1000)
        df['rank_score'] = 1 / (1 + df['national_rank'] / 100)
    else:
        df['rank_score'] = df['recruiting_stars'] / 5

    # No NIL rank for prediction targets
    df['nil_rank_score'] = 0.1  # Default low

    return df


def train_model(train_df: pd.DataFrame):
    """Train NIL prediction model."""

    print("\n" + "=" * 60)
    print("TRAINING NIL PREDICTION MODEL")
    print("=" * 60)

    # Feature columns
    feature_cols = [
        'school_tier', 'position_value', 'is_qb', 'recruiting_stars',
        'recruiting_rating', 'log_followers', 'rank_score', 'nil_rank_score'
    ]

    # Prepare data
    X = train_df[feature_cols].fillna(0).values
    y = np.log1p(train_df['nil_value'].values)  # Log transform target

    print(f"Training samples: {len(X)}")
    print(f"Features: {feature_cols}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train multiple models
    models = {
        'random_forest': RandomForestRegressor(
            n_estimators=200, max_depth=12, min_samples_leaf=3,
            random_state=42, n_jobs=-1
        ),
        'gradient_boosting': GradientBoostingRegressor(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            random_state=42
        ),
    }

    best_model = None
    best_mae = float('inf')
    best_name = None

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train_scaled, y_train)

        # Evaluate
        y_pred = model.predict(X_test_scaled)
        y_pred_dollars = np.expm1(y_pred)
        y_test_dollars = np.expm1(y_test)

        mae = mean_absolute_error(y_test_dollars, y_pred_dollars)
        r2 = r2_score(y_test, y_pred)

        print(f"  MAE: ${mae:,.0f}")
        print(f"  R²: {r2:.3f}")

        if mae < best_mae:
            best_mae = mae
            best_model = model
            best_name = name

    print(f"\n[BEST] Model: {best_name} (MAE: ${best_mae:,.0f})")

    # Feature importance
    if hasattr(best_model, 'feature_importances_'):
        print("\nFeature Importance:")
        importances = best_model.feature_importances_
        for feat, imp in sorted(zip(feature_cols, importances), key=lambda x: -x[1]):
            print(f"  {feat}: {imp:.3f}")

    return best_model, scaler, feature_cols


def predict_valuations(model, scaler, feature_cols, predict_df: pd.DataFrame, train_df: pd.DataFrame) -> pd.DataFrame:
    """Generate NIL predictions for all portal players."""

    print("\n" + "=" * 60)
    print("GENERATING PREDICTIONS")
    print("=" * 60)

    # Create name-based lookup for training data (known values)
    known_values = {}
    for _, row in train_df.iterrows():
        name_key = str(row['name']).lower().strip()
        known_values[name_key] = row['nil_value']

    # Prepare features
    X = predict_df[feature_cols].fillna(0).values
    X_scaled = scaler.transform(X)

    # Predict
    y_pred_log = model.predict(X_scaled)
    y_pred = np.expm1(y_pred_log)

    # Assign tier
    def get_tier(val):
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

    results = []
    for idx, row in predict_df.iterrows():
        name = row['name']
        name_key = str(name).lower().strip()

        # Check if we have known value
        if name_key in known_values:
            nil_value = known_values[name_key]
            is_predicted = False
            confidence = 'actual'
        else:
            nil_value = y_pred[len(results)]
            is_predicted = True

            # Confidence based on features
            stars = row.get('recruiting_stars', 3)
            tier = row.get('school_tier', 3)
            if stars >= 4 and tier >= 4:
                confidence = 'high'
            elif stars >= 3 and tier >= 3:
                confidence = 'medium'
            else:
                confidence = 'low'

        results.append({
            'name': name,
            'position': row['position'],
            'school': row.get('school', row.get('destination_school', row.get('origin_school', 'Unknown'))),
            'origin_school': row.get('origin_school', ''),
            'destination_school': row.get('destination_school', ''),
            'status': row.get('status', 'Unknown'),
            'nil_value_predicted': round(nil_value, 2),
            'nil_tier': get_tier(nil_value),
            'is_predicted': is_predicted,
            'confidence': confidence,
            'recruiting_stars': row.get('recruiting_stars', 3),
            'school_tier': row.get('school_tier', 3),
        })

    result_df = pd.DataFrame(results)

    # Stats
    predicted_count = result_df['is_predicted'].sum()
    actual_count = (~result_df['is_predicted']).sum()

    print(f"Total players: {len(result_df):,}")
    print(f"Actual NIL values: {actual_count:,}")
    print(f"Predicted NIL values: {predicted_count:,}")

    return result_df


def save_results(df: pd.DataFrame):
    """Save results to processed directory."""

    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)

    output_dir = PROJECT_ROOT / "data" / "processed"

    # Save full results
    output_path = output_dir / "portal_nil_valuations.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df):,} valuations to {output_path}")

    # Summary
    print("\n" + "-" * 40)
    print("VALUE DISTRIBUTION")
    print("-" * 40)

    values = df['nil_value_predicted']
    print(f"Mean: ${values.mean():,.0f}")
    print(f"Median: ${values.median():,.0f}")
    print(f"Min: ${values.min():,.0f}")
    print(f"Max: ${values.max():,.0f}")

    print("\n" + "-" * 40)
    print("TIER DISTRIBUTION")
    print("-" * 40)
    print(df['nil_tier'].value_counts().to_string())

    print("\n" + "-" * 40)
    print("TOP 25 PORTAL VALUATIONS")
    print("-" * 40)
    top_25 = df.nlargest(25, 'nil_value_predicted')
    for i, (_, row) in enumerate(top_25.iterrows(), 1):
        actual = " (actual)" if not row['is_predicted'] else ""
        school = row.get('destination_school') or row.get('school', 'Unknown')
        print(f"{i:2}. {row['name'][:25]:<25} ({row['position']:>4}) → {school[:20]:<20} ${row['nil_value_predicted']:>12,.0f}{actual}")


def main():
    """Main execution."""
    print("=" * 60)
    print("PORTAL NIL VALUATION BUILDER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load data
    portal_df, nil_df, nil100_df, team_df = load_data()

    # Build school tiers
    school_tiers = build_school_tiers(team_df)
    print(f"\nBuilt tier mapping for {len(school_tiers)} schools")

    # Prepare training data
    train_df = prepare_training_data(nil_df, school_tiers)
    print(f"\nPrepared {len(train_df)} training samples")

    # Prepare prediction data
    predict_df = prepare_prediction_data(portal_df, school_tiers)
    print(f"Prepared {len(predict_df)} players for prediction")

    # Train model
    model, scaler, feature_cols = train_model(train_df)

    # Save model
    model_dir = PROJECT_ROOT / "models" / "nil_portal"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "model.joblib")
    joblib.dump(scaler, model_dir / "scaler.joblib")
    print(f"\nModel saved to {model_dir}")

    # Generate predictions
    results_df = predict_valuations(model, scaler, feature_cols, predict_df, train_df)

    # Save results
    save_results(results_df)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
