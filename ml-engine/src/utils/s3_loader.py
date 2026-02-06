"""S3/R2 Data Loader for ML Engine.

Handles loading data from Cloudflare R2 (S3-compatible) storage.
Falls back to local files during development.
"""

import os
import io
import logging
from pathlib import Path
from typing import Optional, Dict
from functools import lru_cache

import pandas as pd

logger = logging.getLogger(__name__)

# Try to import boto3
try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed - S3/R2 storage disabled")


# =============================================================================
# Configuration
# =============================================================================

def get_s3_config() -> dict:
    """Get S3/R2 configuration from environment."""
    return {
        "endpoint_url": os.getenv("R2_ENDPOINT_URL"),
        "access_key_id": os.getenv("R2_ACCESS_KEY_ID"),
        "secret_access_key": os.getenv("R2_SECRET_ACCESS_KEY"),
        "bucket_name": os.getenv("R2_BUCKET_NAME", "portal-iq-data"),
        "region": os.getenv("R2_REGION", "auto"),
    }


def is_s3_configured() -> bool:
    """Check if S3/R2 is properly configured."""
    if not BOTO3_AVAILABLE:
        return False
    config = get_s3_config()
    required = ["endpoint_url", "access_key_id", "secret_access_key"]
    return all(config.get(key) for key in required)


# =============================================================================
# S3 Client
# =============================================================================

class S3DataLoader:
    """Load data from S3/R2 storage."""

    _instance = None
    _client = None
    _data_cache: Dict[str, pd.DataFrame] = {}

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def client(self):
        """Lazy-load S3 client."""
        if self._client is None and BOTO3_AVAILABLE and is_s3_configured():
            try:
                config = get_s3_config()
                self._client = boto3.client(
                    "s3",
                    endpoint_url=config["endpoint_url"],
                    aws_access_key_id=config["access_key_id"],
                    aws_secret_access_key=config["secret_access_key"],
                    region_name=config["region"],
                    config=Config(
                        signature_version="s3v4",
                        retries={"max_attempts": 3, "mode": "adaptive"},
                    ),
                )
                logger.info("S3/R2 client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                self._client = None
        return self._client

    @property
    def bucket(self) -> str:
        return get_s3_config()["bucket_name"]

    def read_csv(self, key: str, use_cache: bool = True) -> pd.DataFrame:
        """Read CSV from S3/R2.

        Args:
            key: S3 object key (e.g., "processed/portal_nil_valuations.csv")
            use_cache: Use in-memory cache

        Returns:
            DataFrame
        """
        # Check cache
        if use_cache and key in self._data_cache:
            logger.debug(f"Using cached data for {key}")
            return self._data_cache[key]

        if not self.client:
            logger.debug(f"S3 not available for {key}")
            return pd.DataFrame()

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            df = pd.read_csv(io.BytesIO(response["Body"].read()))
            logger.info(f"Loaded {len(df)} rows from S3: {key}")

            if use_cache:
                self._data_cache[key] = df

            return df

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code in ("404", "NoSuchKey"):
                logger.warning(f"S3 file not found: {key}")
            else:
                logger.error(f"S3 error for {key}: {e}")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to read S3 CSV {key}: {e}")
            return pd.DataFrame()

    def clear_cache(self):
        """Clear the data cache."""
        self._data_cache.clear()
        logger.info("S3 data cache cleared")


# =============================================================================
# Data Loading Functions
# =============================================================================

# Data path mappings
DATA_PATHS = {
    "nil_valuations": "processed/portal_nil_valuations.csv",
    "nil_rankings": "processed/on3_all_nil_rankings.csv",
    "transfer_portal": "processed/on3_transfer_portal.csv",
    "team_portal_rankings": "processed/on3_team_portal_rankings.csv",
    "cfbd_rosters": "processed/cfbd_rosters.csv",
    "cfbd_player_stats": "processed/cfbd_player_stats.csv",
    "pff_grades": "processed/pff_player_grades.csv",
}


def get_s3_loader() -> S3DataLoader:
    """Get singleton S3 loader instance."""
    return S3DataLoader()


def load_nil_data() -> pd.DataFrame:
    """Load NIL valuation data from S3.

    Returns:
        DataFrame with columns: name, position, school, nil_value, etc.
    """
    loader = get_s3_loader()

    # Try portal NIL valuations first (most comprehensive)
    df = loader.read_csv(DATA_PATHS["nil_valuations"])
    if not df.empty:
        return df

    # Fallback to NIL rankings
    df = loader.read_csv(DATA_PATHS["nil_rankings"])
    if not df.empty:
        return df

    logger.warning("No NIL data available")
    return pd.DataFrame()


def load_portal_data() -> pd.DataFrame:
    """Load transfer portal data from S3.

    Returns:
        DataFrame with portal player information
    """
    loader = get_s3_loader()
    df = loader.read_csv(DATA_PATHS["transfer_portal"])

    if df.empty:
        logger.warning("No portal data available")

    return df


def load_pff_grades() -> pd.DataFrame:
    """Load PFF player grades from S3.

    Returns:
        DataFrame with PFF grades
    """
    loader = get_s3_loader()
    return loader.read_csv(DATA_PATHS["pff_grades"])


def load_rosters() -> pd.DataFrame:
    """Load CFBD roster data from S3.

    Returns:
        DataFrame with roster information
    """
    loader = get_s3_loader()
    return loader.read_csv(DATA_PATHS["cfbd_rosters"])
