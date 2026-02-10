"""Sync local data files to Cloudflare R2.

This script uploads all processed data files from local storage to R2
so the production API can access them.

Usage:
    python scripts/sync_to_r2.py

Requires environment variables:
    R2_ENDPOINT_URL
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    R2_BUCKET_NAME (default: portal-iq-data)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from botocore.config import Config

# R2 Configuration
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "portal-iq-data")

# Local data directory
DATA_DIR = Path(__file__).parent.parent / "data" / "processed"

# Files to sync (priority order)
CORE_FILES = [
    "portal_nil_valuations.csv",      # Main NIL valuations (17,500+)
    "on3_transfer_portal.csv",        # Transfer portal data
    "on3_all_nil_rankings.csv",       # On3 NIL rankings
    "on3_team_portal_rankings.csv",   # Team rankings
    "pff_player_grades.csv",          # PFF grades
    "cfbd_rosters.csv",               # CFBD rosters (measurables)
    "cfbd_player_stats.csv",          # CFBD player stats
    "cfbd_sp_ratings.csv",            # SP+ ratings
    "cfbd_team_talent.csv",           # Team talent
    "cfbd_team_records.csv",          # Team win/loss records
    "on3_transfer_portal_current.csv",# Current transfer portal cycle
    "espn_rosters.csv",               # ESPN rosters (headshots)
    "unified_players.csv",             # Unified player table (all data merged)
]

# Additional files to sync
EXTRA_FILES = [
    "nil_valuations_2025.csv",
    "nil_performance_merged.csv",
    "on3_nil_100.csv",
    "on3_college_nil_100.csv",
    "on3_nil_rankings.csv",
    "on3_portal_football.csv",
    "on3_portal_football_nil.csv",
    "on3_portal_industry_football_2024.csv",
    "on3_portal_industry_football_2025.csv",
    "on3_portal_industry_football_2026.csv",
    "on3_portal_tracker_2024.csv",
    "on3_portal_tracker_2025.csv",
    "on3_portal_wire_football_2026.csv",
]


def get_s3_client():
    """Create R2/S3 client."""
    if not all([R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        print("ERROR: Missing R2 credentials in environment variables")
        print("Required: R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
        sys.exit(1)

    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT_URL,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def upload_file(client, local_path: Path, s3_key: str):
    """Upload a file to R2."""
    try:
        file_size = local_path.stat().st_size / 1024  # KB
        print(f"  Uploading {local_path.name} ({file_size:.1f} KB)...", end=" ")

        client.upload_file(
            str(local_path),
            R2_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": "text/csv"}
        )
        print("OK")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False


def list_r2_files(client):
    """List files currently in R2."""
    try:
        response = client.list_objects_v2(Bucket=R2_BUCKET_NAME, Prefix="processed/")
        files = [obj["Key"] for obj in response.get("Contents", [])]
        return files
    except Exception as e:
        print(f"Warning: Could not list R2 files: {e}")
        return []


def sync_files(core_only=False, sync_all=False):
    """Sync local files to R2."""
    print("=" * 60)
    print("Portal IQ - Sync Data to R2")
    print("=" * 60)
    print()

    # Check local data directory
    if not DATA_DIR.exists():
        print(f"ERROR: Data directory not found: {DATA_DIR}")
        sys.exit(1)

    print(f"Local data directory: {DATA_DIR}")
    print(f"R2 bucket: {R2_BUCKET_NAME}")
    print()

    # Get S3 client
    client = get_s3_client()

    # List current R2 files
    print("Checking R2 contents...")
    r2_files = list_r2_files(client)
    print(f"  Found {len(r2_files)} files in R2")
    print()

    # Determine files to sync
    if sync_all:
        # Sync ALL CSV files in the processed directory
        files_to_sync = [f.name for f in DATA_DIR.glob("*.csv")]
        print(f"Syncing ALL {len(files_to_sync)} CSV files...")
    elif core_only:
        files_to_sync = CORE_FILES.copy()
    else:
        files_to_sync = CORE_FILES.copy()
        files_to_sync.extend(EXTRA_FILES)

    # Upload files
    print(f"Syncing {len(files_to_sync)} files...")
    print("-" * 40)

    success = 0
    failed = 0
    skipped = 0

    for filename in files_to_sync:
        local_path = DATA_DIR / filename
        s3_key = f"processed/{filename}"

        if not local_path.exists():
            print(f"  Skipping {filename} (not found locally)")
            skipped += 1
            continue

        if upload_file(client, local_path, s3_key):
            success += 1
        else:
            failed += 1

    print("-" * 40)
    print(f"Results: {success} uploaded, {failed} failed, {skipped} skipped")
    print()

    # Verify upload
    print("Verifying R2 contents...")
    r2_files_after = list_r2_files(client)
    print(f"  R2 now has {len(r2_files_after)} files")

    # Show file sizes
    print()
    print("Files in R2:")
    for file in r2_files_after:
        try:
            response = client.head_object(Bucket=R2_BUCKET_NAME, Key=file)
            size = response["ContentLength"] / 1024
            print(f"  {file}: {size:.1f} KB")
        except:
            print(f"  {file}: (size unknown)")

    print()
    print("=" * 60)
    print("Sync complete!")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sync data files to R2")
    parser.add_argument("--core-only", action="store_true", help="Only sync core files")
    parser.add_argument("--all", action="store_true", help="Sync ALL CSV files in processed folder")
    args = parser.parse_args()

    sync_files(core_only=args.core_only, sync_all=args.all)
