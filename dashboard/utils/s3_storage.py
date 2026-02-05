"""S3/R2 Storage Client for Portal IQ.

Handles loading data files from Cloudflare R2 (S3-compatible) storage.
Falls back to local files during development.
"""

import os
import io
import hashlib
from pathlib import Path
from typing import Optional, Union
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from utils.logging_config import get_logger, log_data_operation, log_error
from utils.env_validator import get_env, get_env_bool

logger = get_logger(__name__)

# Try to import boto3 (optional dependency)
try:
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not installed - S3/R2 storage disabled, using local files")


# =============================================================================
# Configuration
# =============================================================================

def get_s3_config() -> dict:
    """Get S3/R2 configuration from environment."""
    return {
        "endpoint_url": get_env("R2_ENDPOINT_URL"),  # e.g., https://<account_id>.r2.cloudflarestorage.com
        "access_key_id": get_env("R2_ACCESS_KEY_ID"),
        "secret_access_key": get_env("R2_SECRET_ACCESS_KEY"),
        "bucket_name": get_env("R2_BUCKET_NAME", default="portal-iq-data"),
        "region": get_env("R2_REGION", default="auto"),
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

class S3StorageClient:
    """Client for reading data from S3/R2 storage."""

    def __init__(self):
        """Initialize the S3 client."""
        self.config = get_s3_config()
        self.bucket = self.config["bucket_name"]
        self._client = None
        self._cache_dir = Path.home() / ".cache" / "portal-iq" / "data"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def client(self):
        """Lazy-load S3 client."""
        if self._client is None and BOTO3_AVAILABLE and is_s3_configured():
            try:
                self._client = boto3.client(
                    "s3",
                    endpoint_url=self.config["endpoint_url"],
                    aws_access_key_id=self.config["access_key_id"],
                    aws_secret_access_key=self.config["secret_access_key"],
                    region_name=self.config["region"],
                    config=Config(
                        signature_version="s3v4",
                        retries={"max_attempts": 3, "mode": "adaptive"},
                    ),
                )
                logger.info("S3/R2 client initialized")
            except Exception as e:
                log_error(e, "Failed to initialize S3 client")
                self._client = None
        return self._client

    def _get_cache_path(self, key: str) -> Path:
        """Get local cache path for an S3 key."""
        # Create safe filename from key
        safe_name = key.replace("/", "_").replace("\\", "_")
        return self._cache_dir / safe_name

    def _is_cache_valid(self, cache_path: Path, max_age_hours: int = 1) -> bool:
        """Check if cached file is still valid."""
        if not cache_path.exists():
            return False

        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=max_age_hours)

    def download_file(
        self,
        key: str,
        local_path: Optional[Path] = None,
        use_cache: bool = True,
        cache_hours: int = 1,
    ) -> Optional[Path]:
        """Download a file from S3/R2.

        Args:
            key: S3 object key (e.g., "processed/portal_nil_valuations.csv")
            local_path: Optional local path to save to
            use_cache: Whether to use local cache
            cache_hours: How long to cache files locally

        Returns:
            Path to local file, or None if download failed
        """
        if not self.client:
            logger.debug(f"S3 not available, cannot download {key}")
            return None

        # Determine local path
        if local_path is None:
            local_path = self._get_cache_path(key)

        # Check cache
        if use_cache and self._is_cache_valid(local_path, cache_hours):
            logger.debug(f"Using cached file: {local_path}")
            return local_path

        try:
            logger.info(f"Downloading from S3: {key}")
            self.client.download_file(self.bucket, key, str(local_path))
            log_data_operation("s3_download", f"{key} -> {local_path}")
            return local_path

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "404" or error_code == "NoSuchKey":
                logger.warning(f"S3 file not found: {key}")
            else:
                log_error(e, f"S3 download failed: {key}")
            return None

        except Exception as e:
            log_error(e, f"S3 download failed: {key}")
            return None

    def read_csv(
        self,
        key: str,
        use_cache: bool = True,
        cache_hours: int = 1,
        **pandas_kwargs,
    ) -> pd.DataFrame:
        """Read a CSV file from S3/R2.

        Args:
            key: S3 object key
            use_cache: Whether to use local cache
            cache_hours: Cache duration
            **pandas_kwargs: Additional arguments for pd.read_csv

        Returns:
            DataFrame, or empty DataFrame if read failed
        """
        local_path = self.download_file(key, use_cache=use_cache, cache_hours=cache_hours)

        if local_path and local_path.exists():
            try:
                df = pd.read_csv(local_path, **pandas_kwargs)
                log_data_operation("s3_read_csv", f"{key}: {len(df)} rows")
                return df
            except Exception as e:
                log_error(e, f"Failed to parse CSV: {key}")

        return pd.DataFrame()

    def read_csv_direct(self, key: str, **pandas_kwargs) -> pd.DataFrame:
        """Read CSV directly from S3 without caching (for large files).

        Args:
            key: S3 object key
            **pandas_kwargs: Arguments for pd.read_csv

        Returns:
            DataFrame
        """
        if not self.client:
            return pd.DataFrame()

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            df = pd.read_csv(io.BytesIO(response["Body"].read()), **pandas_kwargs)
            log_data_operation("s3_read_direct", f"{key}: {len(df)} rows")
            return df

        except Exception as e:
            log_error(e, f"Failed to read CSV directly: {key}")
            return pd.DataFrame()

    def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3/R2."""
        if not self.client:
            return False

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
        except Exception:
            return False

    def list_files(self, prefix: str = "") -> list:
        """List files in the bucket with optional prefix.

        Args:
            prefix: Filter by key prefix (e.g., "processed/")

        Returns:
            List of object keys
        """
        if not self.client:
            return []

        try:
            response = self.client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            files = [obj["Key"] for obj in response.get("Contents", [])]
            logger.debug(f"Listed {len(files)} files with prefix '{prefix}'")
            return files

        except Exception as e:
            log_error(e, f"Failed to list S3 files: {prefix}")
            return []

    def upload_file(self, local_path: Path, key: str) -> bool:
        """Upload a file to S3/R2.

        Args:
            local_path: Local file path
            key: S3 object key

        Returns:
            True if successful
        """
        if not self.client:
            logger.error("S3 not configured - cannot upload")
            return False

        try:
            self.client.upload_file(str(local_path), self.bucket, key)
            log_data_operation("s3_upload", f"{local_path} -> {key}")
            return True

        except Exception as e:
            log_error(e, f"Failed to upload to S3: {key}")
            return False

    def clear_cache(self, older_than_hours: int = 24):
        """Clear old cached files.

        Args:
            older_than_hours: Delete files older than this
        """
        cutoff = datetime.now() - timedelta(hours=older_than_hours)
        cleared = 0

        for cache_file in self._cache_dir.glob("*"):
            if cache_file.is_file():
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff:
                    cache_file.unlink()
                    cleared += 1

        logger.info(f"Cleared {cleared} cached files older than {older_than_hours}h")


# =============================================================================
# Singleton & Helper Functions
# =============================================================================

@st.cache_resource
def get_s3_client() -> S3StorageClient:
    """Get cached S3 client instance."""
    return S3StorageClient()


def load_csv_with_fallback(
    s3_key: str,
    local_path: Path,
    cache_hours: int = 1,
    **pandas_kwargs,
) -> pd.DataFrame:
    """Load CSV from S3, falling back to local file.

    This is the main function to use throughout the app.
    It tries S3 first, then falls back to local files.

    Args:
        s3_key: S3 object key (e.g., "processed/portal_nil_valuations.csv")
        local_path: Local fallback path
        cache_hours: S3 cache duration
        **pandas_kwargs: Arguments for pd.read_csv

    Returns:
        DataFrame
    """
    # Try S3 first if configured
    if is_s3_configured():
        client = get_s3_client()
        df = client.read_csv(s3_key, cache_hours=cache_hours, **pandas_kwargs)
        if not df.empty:
            return df
        logger.debug(f"S3 read failed for {s3_key}, trying local")

    # Fallback to local file
    if local_path.exists():
        try:
            df = pd.read_csv(local_path, **pandas_kwargs)
            log_data_operation("local_read", f"{local_path}: {len(df)} rows")
            return df
        except Exception as e:
            log_error(e, f"Failed to read local CSV: {local_path}")

    logger.warning(f"No data available for {s3_key} / {local_path}")
    return pd.DataFrame()


# =============================================================================
# Data Path Mapping
# =============================================================================

# Map logical data names to S3 keys and local paths
DATA_PATHS = {
    # NIL & Portal Data
    "portal_nil_valuations": {
        "s3_key": "processed/portal_nil_valuations.csv",
        "local": "ml-engine/data/processed/portal_nil_valuations.csv",
    },
    "on3_transfer_portal": {
        "s3_key": "processed/on3_transfer_portal.csv",
        "local": "ml-engine/data/processed/on3_transfer_portal.csv",
    },
    "on3_all_nil_rankings": {
        "s3_key": "processed/on3_all_nil_rankings.csv",
        "local": "ml-engine/data/processed/on3_all_nil_rankings.csv",
    },
    "on3_team_portal_rankings": {
        "s3_key": "processed/on3_team_portal_rankings.csv",
        "local": "ml-engine/data/processed/on3_team_portal_rankings.csv",
    },

    # CFBD Data
    "cfbd_rosters": {
        "s3_key": "processed/cfbd_rosters.csv",
        "local": "ml-engine/data/processed/cfbd_rosters.csv",
    },
    "cfbd_player_stats": {
        "s3_key": "processed/cfbd_player_stats.csv",
        "local": "ml-engine/data/processed/cfbd_player_stats.csv",
    },
    "cfbd_team_talent": {
        "s3_key": "processed/cfbd_team_talent.csv",
        "local": "ml-engine/data/processed/cfbd_team_talent.csv",
    },
    "cfbd_sp_ratings": {
        "s3_key": "processed/cfbd_sp_ratings.csv",
        "local": "ml-engine/data/processed/cfbd_sp_ratings.csv",
    },

    # PFF Grades
    "pff_player_grades": {
        "s3_key": "processed/pff_player_grades.csv",
        "local": "ml-engine/data/processed/pff_player_grades.csv",
    },

    # ESPN Data
    "espn_rosters": {
        "s3_key": "processed/espn_rosters.csv",
        "local": "ml-engine/data/processed/espn_rosters.csv",
    },
}


def load_data(name: str, cache_hours: int = 1, **kwargs) -> pd.DataFrame:
    """Load a named dataset from S3 or local storage.

    Args:
        name: Dataset name (e.g., "portal_nil_valuations")
        cache_hours: How long to cache S3 data
        **kwargs: Additional pd.read_csv arguments

    Returns:
        DataFrame
    """
    if name not in DATA_PATHS:
        logger.error(f"Unknown dataset: {name}")
        return pd.DataFrame()

    paths = DATA_PATHS[name]
    s3_key = paths["s3_key"]

    # Build local path relative to project root
    # Try to find the project root
    project_root = Path(__file__).parent.parent.parent  # dashboard/utils/ -> project root
    local_path = project_root / paths["local"]

    return load_csv_with_fallback(s3_key, local_path, cache_hours, **kwargs)


# =============================================================================
# Upload Utility (for data sync scripts)
# =============================================================================

def sync_local_to_s3(data_dir: Path, prefix: str = "processed/"):
    """Sync local data directory to S3.

    Use this in data pipeline scripts to upload processed data.

    Args:
        data_dir: Local directory with CSV files
        prefix: S3 key prefix
    """
    if not is_s3_configured():
        logger.error("S3 not configured - cannot sync")
        return

    client = get_s3_client()
    uploaded = 0

    for csv_file in data_dir.glob("*.csv"):
        key = f"{prefix}{csv_file.name}"
        if client.upload_file(csv_file, key):
            uploaded += 1

    logger.info(f"Uploaded {uploaded} files to S3 with prefix '{prefix}'")


if __name__ == "__main__":
    # Test S3 connection
    print("Testing S3/R2 connection...")

    if not BOTO3_AVAILABLE:
        print("ERROR: boto3 not installed. Run: pip install boto3")
    elif not is_s3_configured():
        print("S3/R2 not configured. Set these environment variables:")
        print("  - R2_ENDPOINT_URL")
        print("  - R2_ACCESS_KEY_ID")
        print("  - R2_SECRET_ACCESS_KEY")
        print("  - R2_BUCKET_NAME (optional, defaults to 'portal-iq-data')")
    else:
        client = S3StorageClient()
        files = client.list_files()
        print(f"Connected! Found {len(files)} files in bucket.")
        if files:
            print("First 10 files:")
            for f in files[:10]:
                print(f"  - {f}")
