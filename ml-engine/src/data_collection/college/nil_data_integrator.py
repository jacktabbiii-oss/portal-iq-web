"""
NIL Data Integrator

Combines NIL deal data from multiple sources (On3, your own data, scraped data)
with player performance statistics from CFBD for model training.

This is the key integration point that creates the training dataset with:
- Actual NIL deal values as the target variable
- Player performance metrics as features
- Recruiting rankings as features
- Social media metrics as features
- School/market context as features

Usage:
    from src.data_collection.college.nil_data_integrator import NILDataIntegrator

    integrator = NILDataIntegrator()

    # Load your custom NIL deal data
    integrator.load_custom_nil_data("path/to/your/deals.csv")

    # Or load from On3 scrape
    integrator.load_on3_data()

    # Build training dataset
    training_data = integrator.build_training_dataset()
"""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from datetime import datetime

import pandas as pd
import numpy as np
import yaml

try:
    from rapidfuzz import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NILDataIntegrator:
    """
    Integrates NIL deal data with player performance for ML training.

    Handles:
    - Multiple NIL data sources (On3, custom CSVs, manual entry)
    - Player name matching across different sources
    - Feature engineering for the NIL valuator model
    - Train/validation/test split by time
    """

    # Expected columns for custom NIL data
    REQUIRED_COLUMNS = ["player_name", "nil_value"]
    OPTIONAL_COLUMNS = [
        "school", "position", "deal_date", "deal_type", "source",
        "collective_name", "brand_name", "contract_length_months",
        "guaranteed_amount", "incentive_amount", "notes"
    ]

    # Position group mappings
    POSITION_GROUPS = {
        "QB": "QB",
        "RB": "RB", "HB": "RB", "FB": "RB",
        "WR": "WR", "SE": "WR", "FL": "WR",
        "TE": "TE",
        "OL": "OL", "OT": "OL", "OG": "OL", "C": "OL", "T": "OL", "G": "OL",
        "DL": "DL", "DT": "DL", "DE": "DL", "NT": "DL",
        "EDGE": "EDGE", "OLB": "EDGE",
        "LB": "LB", "ILB": "LB", "MLB": "LB",
        "CB": "CB", "DB": "CB",
        "S": "S", "FS": "S", "SS": "S",
        "K": "K", "P": "K", "PK": "K",
        "LS": "LS",
        "ATH": "ATH",
    }

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the NIL data integrator.

        Args:
            data_dir: Base data directory (auto-detected if None)
        """
        if data_dir is None:
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "config.yaml").exists():
                    data_dir = str(current / "data")
                    break
                current = current.parent
            else:
                data_dir = "data"

        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.cache_dir = self.data_dir / "cache"

        # Create directories
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # Data storage
        self.nil_deals: pd.DataFrame = pd.DataFrame()
        self.performance_stats: pd.DataFrame = pd.DataFrame()
        self.recruiting_data: pd.DataFrame = pd.DataFrame()
        self.social_data: pd.DataFrame = pd.DataFrame()

        # Load config for school/conference tiers
        self.config = self._load_config()

        logger.info(f"NILDataIntegrator initialized. Data dir: {self.data_dir}")

    def _load_config(self) -> Dict:
        """Load config.yaml for tiers and premiums."""
        config_path = self.data_dir.parent / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path) as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        return {}

    def load_custom_nil_data(
        self,
        filepath: Union[str, Path],
        value_column: str = "nil_value",
        name_column: str = "player_name"
    ) -> pd.DataFrame:
        """
        Load your own NIL deal data from CSV/Excel.

        Args:
            filepath: Path to your NIL data file
            value_column: Column name containing the deal value
            name_column: Column name containing the player name

        Returns:
            Loaded DataFrame

        Expected format:
            player_name, school, position, nil_value, deal_date, deal_type, source
            Travis Hunter, Colorado, CB/WR, 1500000, 2024-01-15, collective, On3
            Shedeur Sanders, Colorado, QB, 4800000, 2024-02-01, brand, Custom
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"NIL data file not found: {filepath}")

        # Load based on file type
        if filepath.suffix == ".csv":
            df = pd.read_csv(filepath)
        elif filepath.suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(filepath)
        elif filepath.suffix == ".json":
            df = pd.read_json(filepath)
        else:
            raise ValueError(f"Unsupported file type: {filepath.suffix}")

        logger.info(f"Loaded {len(df)} rows from {filepath}")

        # Standardize column names
        df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

        # Map common column name variations
        column_mappings = {
            "player": "player_name",
            "name": "player_name",
            "athlete": "player_name",
            "team": "school",
            "college": "school",
            "university": "school",
            "pos": "position",
            "value": "nil_value",
            "deal_value": "nil_value",
            "amount": "nil_value",
            "valuation": "nil_value",
            "date": "deal_date",
            "type": "deal_type",
        }

        for old, new in column_mappings.items():
            if old in df.columns and new not in df.columns:
                df = df.rename(columns={old: new})

        # Validate required columns
        if "player_name" not in df.columns:
            raise ValueError(f"Could not find player name column. Available: {list(df.columns)}")

        if "nil_value" not in df.columns:
            raise ValueError(f"Could not find NIL value column. Available: {list(df.columns)}")

        # Clean values
        df["player_name"] = df["player_name"].astype(str).str.strip()
        df["nil_value"] = pd.to_numeric(df["nil_value"], errors="coerce")

        # Remove invalid rows
        df = df.dropna(subset=["player_name", "nil_value"])
        df = df[df["nil_value"] > 0]

        # Add to collection
        if self.nil_deals.empty:
            self.nil_deals = df
        else:
            self.nil_deals = pd.concat([self.nil_deals, df], ignore_index=True)

        logger.info(f"Total NIL deals: {len(self.nil_deals)}")
        return df

    def load_on3_data(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Load scraped On3 data.

        Args:
            filepath: Path to On3 scrape output, or None for latest

        Returns:
            Loaded DataFrame
        """
        if filepath:
            path = Path(filepath)
        else:
            # Look for latest On3 scrape
            on3_dir = self.raw_dir / "on3"
            if on3_dir.exists():
                files = list(on3_dir.glob("nil_100_latest.csv"))
                if not files:
                    files = sorted(on3_dir.glob("nil_100_*.csv"))
                if files:
                    path = files[-1]
                else:
                    logger.warning("No On3 data found. Run on3_scraper.py first.")
                    return pd.DataFrame()
            else:
                logger.warning("No On3 data directory found.")
                return pd.DataFrame()

        if not path.exists():
            logger.warning(f"On3 file not found: {path}")
            return pd.DataFrame()

        df = pd.read_csv(path)
        logger.info(f"Loaded {len(df)} On3 players from {path}")

        # Standardize columns
        df = df.rename(columns={
            "name": "player_name",
            "nil_valuation": "nil_value",
        })

        df["source"] = "on3"

        # Add to collection
        if self.nil_deals.empty:
            self.nil_deals = df
        else:
            # Merge, preferring custom data over On3 for duplicates
            self.nil_deals = self._merge_nil_sources(self.nil_deals, df)

        return df

    def _merge_nil_sources(self, primary: pd.DataFrame, secondary: pd.DataFrame) -> pd.DataFrame:
        """
        Merge NIL data from multiple sources, handling duplicates.

        Primary source takes precedence for duplicate players.
        """
        # Standardize names for matching
        primary["name_std"] = primary["player_name"].str.lower().str.strip()
        secondary["name_std"] = secondary["player_name"].str.lower().str.strip()

        # Find players only in secondary
        primary_names = set(primary["name_std"])
        new_players = secondary[~secondary["name_std"].isin(primary_names)]

        # Combine
        merged = pd.concat([primary, new_players], ignore_index=True)
        merged = merged.drop(columns=["name_std"])

        logger.info(f"Merged sources: {len(primary)} primary + {len(new_players)} new = {len(merged)} total")
        return merged

    def load_performance_data(self, seasons: List[int] = None) -> pd.DataFrame:
        """
        Load player performance statistics from CFBD cache.

        Args:
            seasons: List of seasons to load (default: 2020-2025)

        Returns:
            Performance stats DataFrame
        """
        if seasons is None:
            seasons = list(range(2020, 2026))

        # Try cache first
        cache_pattern = "cfb_player_stats_*_cache.csv"
        cache_files = list(self.cache_dir.glob(cache_pattern))

        if cache_files:
            dfs = []
            for f in cache_files:
                try:
                    df = pd.read_csv(f)
                    if "season" in df.columns:
                        df = df[df["season"].isin(seasons)]
                    dfs.append(df)
                except Exception as e:
                    logger.warning(f"Error loading {f}: {e}")

            if dfs:
                self.performance_stats = pd.concat(dfs, ignore_index=True)
                logger.info(f"Loaded {len(self.performance_stats)} performance records")
                return self.performance_stats

        # Try raw directory
        raw_path = self.raw_dir / "player_season_stats.csv"
        if raw_path.exists():
            self.performance_stats = pd.read_csv(raw_path)
            if "season" in self.performance_stats.columns:
                self.performance_stats = self.performance_stats[
                    self.performance_stats["season"].isin(seasons)
                ]
            logger.info(f"Loaded {len(self.performance_stats)} performance records from raw")
            return self.performance_stats

        logger.warning("No performance data found. Run cfb_stats.py to collect.")
        return pd.DataFrame()

    def load_recruiting_data(self, years: List[int] = None) -> pd.DataFrame:
        """
        Load recruiting rankings data.

        Args:
            years: Recruiting class years (default: 2018-2025)
        """
        if years is None:
            years = list(range(2018, 2026))

        cache_pattern = "cfb_recruiting_*_cache.csv"
        cache_files = list(self.cache_dir.glob(cache_pattern))

        if cache_files:
            dfs = []
            for f in cache_files:
                try:
                    df = pd.read_csv(f)
                    dfs.append(df)
                except Exception as e:
                    logger.warning(f"Error loading {f}: {e}")

            if dfs:
                self.recruiting_data = pd.concat(dfs, ignore_index=True)
                logger.info(f"Loaded {len(self.recruiting_data)} recruiting records")
                return self.recruiting_data

        raw_path = self.raw_dir / "recruiting_rankings.csv"
        if raw_path.exists():
            self.recruiting_data = pd.read_csv(raw_path)
            logger.info(f"Loaded {len(self.recruiting_data)} recruiting records")
            return self.recruiting_data

        logger.warning("No recruiting data found.")
        return pd.DataFrame()

    def load_social_media_data(self) -> pd.DataFrame:
        """Load social media profile data."""
        path = self.raw_dir / "social_media_profiles.csv"
        if path.exists():
            self.social_data = pd.read_csv(path)
            logger.info(f"Loaded {len(self.social_data)} social media profiles")
        return self.social_data

    def build_training_dataset(
        self,
        min_nil_value: float = 0,
        include_sample: bool = False
    ) -> pd.DataFrame:
        """
        Build the complete training dataset by merging all data sources.

        This is the main output for training the NIL valuator model.

        Args:
            min_nil_value: Minimum NIL value to include
            include_sample: Include sample/synthetic data (for testing only)

        Returns:
            Training-ready DataFrame with features and target
        """
        logger.info("Building training dataset...")

        if self.nil_deals.empty:
            logger.error("No NIL deal data loaded. Call load_custom_nil_data() or load_on3_data() first.")
            return pd.DataFrame()

        # Start with NIL deals as base
        df = self.nil_deals.copy()

        # Filter
        df = df[df["nil_value"] >= min_nil_value]

        if not include_sample and "is_sample_data" in df.columns:
            df = df[df["is_sample_data"] != True]

        # Load auxiliary data if not already loaded
        if self.performance_stats.empty:
            self.load_performance_data()
        if self.recruiting_data.empty:
            self.load_recruiting_data()
        if self.social_data.empty:
            self.load_social_media_data()

        # Merge performance stats
        df = self._merge_performance_features(df)

        # Merge recruiting data
        df = self._merge_recruiting_features(df)

        # Merge social media
        df = self._merge_social_features(df)

        # Add contextual features
        df = self._add_context_features(df)

        # Engineer additional features
        df = self._engineer_features(df)

        # Log target variable (for regression)
        df["nil_value_log"] = np.log1p(df["nil_value"])

        # Add NIL tier (for classification)
        df["nil_tier"] = df["nil_value"].apply(self._get_nil_tier)

        # Save
        output_path = self.processed_dir / "nil_training_dataset.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved training dataset: {output_path} ({len(df)} rows, {len(df.columns)} columns)")

        # Print summary
        self._print_dataset_summary(df)

        return df

    def _merge_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge player performance stats using fuzzy matching."""
        if self.performance_stats.empty:
            return df

        if not FUZZY_AVAILABLE:
            logger.warning("rapidfuzz not installed, using exact matching")
            return df

        logger.info("Merging performance features...")

        # Standardize names
        df["name_std"] = df["player_name"].str.lower().str.strip()

        # Get player name column from stats
        name_col = "player" if "player" in self.performance_stats.columns else "player_name"
        if name_col not in self.performance_stats.columns:
            logger.warning(f"No player name column in performance stats")
            return df

        self.performance_stats["name_std"] = self.performance_stats[name_col].str.lower().str.strip()

        # Aggregate stats per player (latest season)
        if "season" in self.performance_stats.columns:
            agg_stats = self.performance_stats.sort_values("season", ascending=False).groupby("name_std").first().reset_index()
        else:
            agg_stats = self.performance_stats.groupby("name_std").first().reset_index()

        # Create lookup dict for speed
        stats_dict = agg_stats.set_index("name_std").to_dict("index")
        stats_names = list(stats_dict.keys())

        # Match and merge
        performance_rows = []
        for _, row in df.iterrows():
            match = process.extractOne(
                row["name_std"],
                stats_names,
                scorer=fuzz.token_sort_ratio
            )
            if match and match[1] >= 80:
                performance_rows.append(stats_dict[match[0]])
            else:
                performance_rows.append({})

        perf_df = pd.DataFrame(performance_rows)

        # Select useful columns
        useful_cols = [
            "games_played", "games_started", "passing_yards", "passing_tds",
            "rushing_yards", "rushing_tds", "receiving_yards", "receiving_tds",
            "tackles", "sacks", "interceptions", "pff_grade", "production_score"
        ]
        available_cols = [c for c in useful_cols if c in perf_df.columns]

        if available_cols:
            df = pd.concat([df.reset_index(drop=True), perf_df[available_cols].reset_index(drop=True)], axis=1)
            logger.info(f"Added {len(available_cols)} performance columns")

        df = df.drop(columns=["name_std"], errors="ignore")
        return df

    def _merge_recruiting_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge recruiting rankings."""
        if self.recruiting_data.empty:
            return df

        if not FUZZY_AVAILABLE:
            return df

        logger.info("Merging recruiting features...")

        df["name_std"] = df["player_name"].str.lower().str.strip()

        name_col = "name" if "name" in self.recruiting_data.columns else "player_name"
        if name_col not in self.recruiting_data.columns:
            return df

        self.recruiting_data["name_std"] = self.recruiting_data[name_col].str.lower().str.strip()

        recruiting_dict = self.recruiting_data.set_index("name_std").to_dict("index")
        recruiting_names = list(recruiting_dict.keys())

        recruiting_rows = []
        for _, row in df.iterrows():
            match = process.extractOne(
                row["name_std"],
                recruiting_names,
                scorer=fuzz.token_sort_ratio
            )
            if match and match[1] >= 80:
                recruiting_rows.append(recruiting_dict[match[0]])
            else:
                recruiting_rows.append({})

        rec_df = pd.DataFrame(recruiting_rows)

        # Add recruiting columns
        cols_to_add = ["stars", "rating", "national_ranking", "position_ranking", "state_ranking"]
        available = [c for c in cols_to_add if c in rec_df.columns]

        if available:
            for col in available:
                df[f"recruiting_{col}"] = rec_df[col].values
            logger.info(f"Added {len(available)} recruiting columns")

        df = df.drop(columns=["name_std"], errors="ignore")
        return df

    def _merge_social_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Merge social media data."""
        if self.social_data.empty:
            return df

        logger.info("Merging social media features...")

        # Try direct merge first on player_name
        if "player_name" in self.social_data.columns:
            social_cols = [
                "instagram_followers", "twitter_followers", "tiktok_followers",
                "youtube_subscribers", "total_social_following", "instagram_engagement_rate"
            ]
            available = [c for c in social_cols if c in self.social_data.columns]

            if available:
                merge_cols = ["player_name"] + available
                social_subset = self.social_data[merge_cols].drop_duplicates(subset=["player_name"])
                df = df.merge(social_subset, on="player_name", how="left", suffixes=("", "_social"))
                logger.info(f"Added {len(available)} social media columns")

        return df

    def _add_context_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add school/conference tier features from config."""
        logger.info("Adding context features...")

        # School tier
        school_tiers = self.config.get("school_tiers", {})
        def get_school_tier(school):
            if pd.isna(school):
                return 3
            for tier_name, schools in school_tiers.items():
                if school in schools:
                    tier_map = {"tier_5_blue_blood": 5, "tier_4_elite": 4, "tier_3_power_brand": 3,
                               "tier_2_p4_mid": 2, "tier_1_g5_strong": 1}
                    return tier_map.get(tier_name, 3)
            return 3

        if "school" in df.columns:
            df["school_tier"] = df["school"].apply(get_school_tier)

        # Conference tier
        conf_tiers = self.config.get("conference_tiers", {})
        def get_conf_tier(conf):
            if pd.isna(conf):
                return 3
            for tier_name, conferences in conf_tiers.items():
                if conf in conferences:
                    tier_map = {"tier_1": 5, "tier_2": 4, "tier_3": 3, "tier_4": 2, "tier_5": 1}
                    return tier_map.get(tier_name, 3)
            return 3

        if "conference" in df.columns:
            df["conference_tier"] = df["conference"].apply(get_conf_tier)

        # Position premium
        pos_premiums = self.config.get("nil_model", {}).get("position_premiums", {})
        if "position" in df.columns:
            df["position_group"] = df["position"].map(self.POSITION_GROUPS).fillna("ATH")
            df["position_premium"] = df["position_group"].map(pos_premiums).fillna(1.0)

        return df

    def _engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Engineer derived features."""
        logger.info("Engineering features...")

        # Total social following
        social_cols = ["instagram_followers", "twitter_followers", "tiktok_followers"]
        available = [c for c in social_cols if c in df.columns]
        if available and "total_social_following" not in df.columns:
            df["total_social_following"] = df[available].sum(axis=1, min_count=1)

        # Production score
        if "rushing_yards" in df.columns or "passing_yards" in df.columns:
            df["total_yards"] = (
                df.get("passing_yards", 0).fillna(0) +
                df.get("rushing_yards", 0).fillna(0) +
                df.get("receiving_yards", 0).fillna(0)
            )
            df["total_tds"] = (
                df.get("passing_tds", 0).fillna(0) +
                df.get("rushing_tds", 0).fillna(0) +
                df.get("receiving_tds", 0).fillna(0)
            )

        # Interaction features
        if "school_tier" in df.columns and "total_yards" in df.columns:
            df["school_x_production"] = df["school_tier"] * df["total_yards"].fillna(0)

        if "total_social_following" in df.columns and "school_tier" in df.columns:
            df["social_x_school"] = df["total_social_following"].fillna(0) * df["school_tier"]

        if "recruiting_stars" in df.columns and "school_tier" in df.columns:
            df["stars_x_school"] = df["recruiting_stars"].fillna(3) * df["school_tier"]

        return df

    def _get_nil_tier(self, value: float) -> str:
        """Map NIL value to tier."""
        if value >= 1_000_000:
            return "mega"
        elif value >= 500_000:
            return "premium"
        elif value >= 100_000:
            return "solid"
        elif value >= 25_000:
            return "moderate"
        else:
            return "entry"

    def _print_dataset_summary(self, df: pd.DataFrame):
        """Print summary statistics."""
        print("\n" + "=" * 60)
        print("TRAINING DATASET SUMMARY")
        print("=" * 60)

        print(f"\nTotal records: {len(df)}")
        print(f"Total features: {len(df.columns)}")

        if "nil_value" in df.columns:
            print(f"\nNIL Value Statistics:")
            print(f"  Min:    ${df['nil_value'].min():,.0f}")
            print(f"  Max:    ${df['nil_value'].max():,.0f}")
            print(f"  Mean:   ${df['nil_value'].mean():,.0f}")
            print(f"  Median: ${df['nil_value'].median():,.0f}")

        if "nil_tier" in df.columns:
            print(f"\nNIL Tier Distribution:")
            for tier, count in df["nil_tier"].value_counts().items():
                avg = df[df["nil_tier"] == tier]["nil_value"].mean()
                print(f"  {tier:10s}: {count:4d} players (avg ${avg:,.0f})")

        if "school" in df.columns:
            print(f"\nTop 10 Schools:")
            for school, count in df["school"].value_counts().head(10).items():
                avg = df[df["school"] == school]["nil_value"].mean()
                print(f"  {school:20s}: {count:3d} players (avg ${avg:,.0f})")

        if "position_group" in df.columns:
            print(f"\nPosition Groups:")
            for pos, count in df["position_group"].value_counts().items():
                avg = df[df["position_group"] == pos]["nil_value"].mean()
                print(f"  {pos:6s}: {count:4d} players (avg ${avg:,.0f})")

        print("\n" + "=" * 60)


def main():
    """Example usage."""
    print("NIL Data Integrator")
    print("=" * 50)

    integrator = NILDataIntegrator()

    # Load On3 scraped data
    print("\n[1/4] Loading On3 data...")
    on3_data = integrator.load_on3_data()
    print(f"On3 records: {len(on3_data)}")

    # Load performance data
    print("\n[2/4] Loading performance data...")
    perf_data = integrator.load_performance_data()
    print(f"Performance records: {len(perf_data)}")

    # Load recruiting data
    print("\n[3/4] Loading recruiting data...")
    rec_data = integrator.load_recruiting_data()
    print(f"Recruiting records: {len(rec_data)}")

    # Build training dataset
    print("\n[4/4] Building training dataset...")
    training_data = integrator.build_training_dataset(include_sample=True)

    if not training_data.empty:
        print(f"\nTraining dataset ready: {len(training_data)} records")
        print(f"Features: {list(training_data.columns)[:20]}...")


if __name__ == "__main__":
    main()
