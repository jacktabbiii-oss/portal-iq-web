"""
Process scraped On3 data and extract embedded JSON fields.
Also attempts to fetch NIL data from On3's API endpoints.
"""
import pandas as pd
import json
import ast
import requests
from pathlib import Path

def extract_from_composite_rating(df: pd.DataFrame) -> pd.DataFrame:
    """Extract fields from the composite_rating JSON column."""

    def parse_rating(val):
        if pd.isna(val):
            return {}
        if isinstance(val, str):
            try:
                # Try JSON first
                return json.loads(val)
            except:
                try:
                    # Try literal eval for Python dict strings
                    return ast.literal_eval(val)
                except:
                    return {}
        elif isinstance(val, dict):
            return val
        return {}

    # Parse the composite_rating column
    ratings = df['composite_rating'].apply(parse_rating)

    # Extract individual fields
    df['position'] = ratings.apply(lambda x: x.get('positionAbbr', 'Unknown'))
    df['recruiting_stars'] = ratings.apply(lambda x: x.get('consensusStars') or x.get('stars'))
    df['recruiting_rating'] = ratings.apply(lambda x: x.get('consensusRating') or x.get('rating'))
    df['national_rank'] = ratings.apply(lambda x: x.get('consensusNationalRank') or x.get('nationalRank'))
    df['position_rank'] = ratings.apply(lambda x: x.get('consensusPositionRank') or x.get('positionRank'))
    df['state'] = ratings.apply(lambda x: x.get('stateAbbr'))
    df['five_star_plus'] = ratings.apply(lambda x: x.get('fiveStarPlus', False))

    return df


def try_on3_api():
    """
    Try to fetch NIL data from On3's public API endpoints.
    These may or may not be available/stable.
    """
    print("\nAttempting On3 API endpoints...")

    endpoints = [
        "https://www.on3.com/api/v1/nil/rankings",
        "https://www.on3.com/api/nil/rankings/player/nil-100",
        "https://api.on3.com/v1/nil/rankings",
    ]

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://www.on3.com/nil/rankings/player/nil-100/",
    }

    for endpoint in endpoints:
        try:
            print(f"  Trying: {endpoint}")
            resp = requests.get(endpoint, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                print(f"    SUCCESS! Got {type(data)}")
                return data
            else:
                print(f"    Status: {resp.status_code}")
        except Exception as e:
            print(f"    Error: {e}")

    print("  No API endpoints accessible")
    return None


def main():
    data_dir = Path("data/raw/on3")

    # Find the latest scraped file
    files = list(data_dir.glob("nil_100_*.csv"))
    if not files:
        print("No scraped On3 data found. Run scrape_on3.py first.")
        return

    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    print(f"Processing: {latest_file}")

    # Load and process
    df = pd.read_csv(latest_file)
    print(f"Loaded {len(df)} players")

    # Extract from composite_rating
    if 'composite_rating' in df.columns:
        df = extract_from_composite_rating(df)
        print("Extracted recruiting data from composite_rating")

    # Try API for NIL values
    api_data = try_on3_api()
    if api_data:
        print("Got API data - merging...")
        # Would merge here if API worked

    # Clean up and save
    output_cols = [
        'name', 'school', 'position', 'nil_valuation',
        'recruiting_stars', 'recruiting_rating', 'national_rank',
        'position_rank', 'state', 'five_star_plus', 'scraped_at'
    ]

    available_cols = [c for c in output_cols if c in df.columns]
    df_clean = df[available_cols].copy()

    # Add nil_rank based on position in list (since we can't get actual values)
    df_clean['nil_rank'] = range(1, len(df_clean) + 1)

    # Save cleaned data
    output_path = data_dir / "nil_100_cleaned.csv"
    df_clean.to_csv(output_path, index=False)
    print(f"\nSaved cleaned data to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("CLEANED DATA SUMMARY")
    print("=" * 60)
    print(f"\nTotal players: {len(df_clean)}")
    print(f"\nPosition distribution:")
    print(df_clean['position'].value_counts().head(10).to_string())
    print(f"\nStar distribution:")
    print(df_clean['recruiting_stars'].value_counts().sort_index(ascending=False).to_string())
    print(f"\nTop 15 players:")
    print(df_clean[['nil_rank', 'name', 'position', 'recruiting_stars', 'recruiting_rating']].head(15).to_string(index=False))

    print("\n" + "=" * 60)
    print("NOTE: NIL valuations could not be scraped from On3.")
    print("Options:")
    print("1. Manually add NIL values to data/raw/on3/nil_100_cleaned.csv")
    print("2. Use On3 subscription API if you have access")
    print("3. Cross-reference with other sources (Opendorse, etc.)")
    print("=" * 60)


if __name__ == "__main__":
    main()
