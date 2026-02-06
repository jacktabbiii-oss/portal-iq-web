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

# Base path for local data files (ml-engine/data)
LOCAL_DATA_BASE = Path(__file__).parent.parent.parent / "data"

# Data path mappings - S3 key and local fallback
DATA_PATHS = {
    "nil_valuations": {
        "s3_key": "processed/portal_nil_valuations.csv",
        "local": "processed/portal_nil_valuations.csv",
    },
    "nil_rankings": {
        "s3_key": "processed/on3_all_nil_rankings.csv",
        "local": "processed/on3_all_nil_rankings.csv",
    },
    "transfer_portal": {
        "s3_key": "processed/on3_transfer_portal.csv",
        "local": "processed/on3_transfer_portal.csv",
    },
    "team_portal_rankings": {
        "s3_key": "processed/on3_team_portal_rankings.csv",
        "local": "processed/on3_team_portal_rankings.csv",
    },
    "cfbd_rosters": {
        "s3_key": "processed/cfbd_rosters.csv",
        "local": "processed/cfbd_rosters.csv",
    },
    "cfbd_player_stats": {
        "s3_key": "processed/cfbd_player_stats.csv",
        "local": "processed/cfbd_player_stats.csv",
    },
    "pff_grades": {
        "s3_key": "processed/pff_player_grades.csv",
        "local": "processed/pff_player_grades.csv",
    },
}


def get_s3_loader() -> S3DataLoader:
    """Get singleton S3 loader instance."""
    return S3DataLoader()


def load_csv_with_fallback(data_key: str) -> pd.DataFrame:
    """Load CSV from S3, falling back to local file if S3 fails.

    Args:
        data_key: Key from DATA_PATHS (e.g., "nil_valuations")

    Returns:
        DataFrame
    """
    paths = DATA_PATHS.get(data_key)
    if not paths:
        logger.error(f"Unknown data key: {data_key}")
        return pd.DataFrame()

    # Try S3 first
    loader = get_s3_loader()
    df = loader.read_csv(paths["s3_key"])
    if not df.empty:
        logger.info(f"Loaded {data_key} from S3: {len(df)} rows")
        return df

    # Fallback to local file
    local_path = LOCAL_DATA_BASE / paths["local"]
    if local_path.exists():
        try:
            df = pd.read_csv(local_path)
            logger.info(f"Loaded {data_key} from local file: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to read local file {local_path}: {e}")

    logger.warning(f"No data available for {data_key} (S3 and local both failed)")
    return pd.DataFrame()


def load_nil_data() -> pd.DataFrame:
    """Load NIL valuation data.

    Returns:
        DataFrame with columns: name, position, school, nil_value, etc.
    """
    # Try portal NIL valuations first (most comprehensive)
    df = load_csv_with_fallback("nil_valuations")
    if not df.empty:
        return df

    # Fallback to NIL rankings
    df = load_csv_with_fallback("nil_rankings")
    if not df.empty:
        return df

    logger.warning("No NIL data available from any source")
    return pd.DataFrame()


def load_portal_data() -> pd.DataFrame:
    """Load transfer portal data.

    Returns:
        DataFrame with portal player information
    """
    return load_csv_with_fallback("transfer_portal")


def load_pff_grades() -> pd.DataFrame:
    """Load PFF player grades.

    Returns:
        DataFrame with PFF grades
    """
    return load_csv_with_fallback("pff_grades")


def load_rosters() -> pd.DataFrame:
    """Load CFBD roster data.

    Returns:
        DataFrame with roster information
    """
    return load_csv_with_fallback("cfbd_rosters")


def get_s3_diagnostics() -> dict:
    """Get S3 connection diagnostics for debugging."""
    config = get_s3_config()

    result = {
        "boto3_available": BOTO3_AVAILABLE,
        "s3_configured": is_s3_configured(),
        "local_data_base": str(LOCAL_DATA_BASE),
        "local_data_exists": LOCAL_DATA_BASE.exists(),
        "config": {
            "endpoint_url": config["endpoint_url"][:50] + "..." if config["endpoint_url"] else None,
            "bucket_name": config["bucket_name"],
            "access_key_set": bool(config["access_key_id"]),
            "secret_key_set": bool(config["secret_access_key"]),
        },
        "s3_files": [],
        "local_files": [],
        "error": None,
    }

    # Check local files first
    for name, paths in DATA_PATHS.items():
        local_path = LOCAL_DATA_BASE / paths["local"]
        if local_path.exists():
            try:
                size = local_path.stat().st_size
                result["local_files"].append(f"✓ {name}: {size / 1024:.1f} KB")
            except Exception:
                result["local_files"].append(f"? {name}: exists but can't read size")
        else:
            result["local_files"].append(f"✗ {name}: not found at {local_path}")

    # Check S3
    if not BOTO3_AVAILABLE:
        result["error"] = "boto3 not installed - using local files only"
        return result

    if not is_s3_configured():
        result["error"] = "S3 not configured - using local files only"
        return result

    loader = get_s3_loader()

    if not loader.client:
        result["error"] = "Failed to create S3 client - using local files only"
        return result

    # Try to list S3 files
    try:
        response = loader.client.list_objects_v2(
            Bucket=loader.bucket,
            Prefix="processed/",
            MaxKeys=20
        )
        files = [obj["Key"] for obj in response.get("Contents", [])]
        result["s3_files"] = files
        result["s3_total_files"] = response.get("KeyCount", 0)
    except Exception as e:
        result["error"] = f"S3 list failed: {str(e)[:100]}"

    return result
