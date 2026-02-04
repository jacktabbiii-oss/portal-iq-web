"""
PFF Data Import Script for PocketBase

Imports PFF player grades from CSV into PocketBase collection.
Designed for ~71k records across 3 seasons (2023-2025).

Usage:
    python scripts/import_pff_to_pocketbase.py
    python scripts/import_pff_to_pocketbase.py --delay 100      # Slower (100ms between requests)
    python scripts/import_pff_to_pocketbase.py --resume         # Resume from last progress
    python scripts/import_pff_to_pocketbase.py --start-from 5000  # Start from specific row

Environment Variables:
    POCKETBASE_URL - PocketBase instance URL
    POCKETBASE_ADMIN_EMAIL - Admin email for auth
    POCKETBASE_ADMIN_PASSWORD - Admin password for auth

Collection Schema (create in PocketBase admin):
    Name: pff_grades
    Fields:
        - name (text, required)
        - pff_id (number)
        - team (text)
        - position (text)
        - season (number, required)
        - games_played (number)
        - pff_overall (number)
        - pff_offense (number)
        - pff_defense (number)
        - offensive_snaps (number)
        - defensive_snaps (number)
        - stats_json (json)

    Indexes:
        - name (for player lookups)
        - team (for team queries)
        - position (for position filtering)
        - season (for season filtering)
        - pff_id + season (unique constraint)
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env from multiple possible locations
env_paths = [
    Path(__file__).parent.parent / ".env",  # root/.env
    Path(__file__).parent.parent / "ml-engine" / ".env",  # ml-engine/.env
    Path(__file__).parent / ".env",  # scripts/.env
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break
else:
    load_dotenv()  # Try default

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent / "ml-engine" / "data" / "processed"
PFF_CSV = DATA_DIR / "pff_player_grades.csv"

# Core fields to extract (stored as individual columns for indexing/filtering)
CORE_FIELDS = [
    "name", "pff_id", "team", "position", "season", "games_played",
    "pff_overall", "pff_offense", "pff_defense",
    "offensive_snaps", "defensive_snaps", "pass_rush_snaps", "coverage_snaps"
]


def clean_value(val: Any) -> Any:
    """Clean a value for JSON serialization."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return None
        return val
    return str(val) if val else None


def row_to_record(row: pd.Series) -> Dict:
    """Convert a DataFrame row to a PocketBase record."""
    # Extract core fields
    record = {}
    for field in CORE_FIELDS:
        if field in row.index:
            val = row[field]
            record[field] = clean_value(val)

    # All other fields go into stats_json
    stats = {}
    for col in row.index:
        if col not in CORE_FIELDS:
            val = row[col]
            cleaned = clean_value(val)
            if cleaned is not None:  # Only include non-null values
                stats[col] = cleaned

    record["stats_json"] = stats

    return record


def retry_with_backoff(func, max_retries=5, base_delay=1.0):
    """Retry a function with exponential backoff for rate limiting."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "too many" in error_str or "rate" in error_str:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 1, 2, 4, 8, 16 seconds
                logger.warning(f"Rate limited, waiting {delay}s before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
            else:
                raise  # Re-raise non-rate-limit errors
    raise Exception(f"Max retries ({max_retries}) exceeded")


def import_to_pocketbase(batch_size: int = 100, dry_run: bool = False, start_from: int = 0, delay_ms: int = 50):
    """
    Import PFF data to PocketBase.

    Args:
        batch_size: Number of records per batch
        dry_run: If True, just validate data without importing
        start_from: Row index to start from (for resuming failed imports)
        delay_ms: Milliseconds to wait between requests (rate limiting)
    """
    # Check PocketBase config
    pb_url = os.getenv("POCKETBASE_URL")
    pb_email = os.getenv("POCKETBASE_ADMIN_EMAIL")
    pb_password = os.getenv("POCKETBASE_ADMIN_PASSWORD")

    if not pb_url:
        logger.error("POCKETBASE_URL not set. Add to .env file.")
        return

    if not dry_run:
        try:
            from pocketbase import PocketBase

            pb = PocketBase(pb_url)
            pb.admins.auth_with_password(pb_email, pb_password)
            logger.info(f"Connected to PocketBase at {pb_url}")
        except ImportError:
            logger.error("pocketbase package not installed. Run: pip install pocketbase")
            return
        except Exception as e:
            logger.error(f"Failed to connect to PocketBase: {e}")
            return

    # Load PFF data
    if not PFF_CSV.exists():
        logger.error(f"PFF CSV not found: {PFF_CSV}")
        return

    logger.info(f"Loading PFF data from {PFF_CSV}")
    df = pd.read_csv(PFF_CSV)
    logger.info(f"Loaded {len(df):,} records with {len(df.columns)} columns")

    # Show season breakdown
    if "season" in df.columns:
        season_counts = df["season"].value_counts().sort_index()
        logger.info(f"Season breakdown:\n{season_counts}")

    if dry_run:
        logger.info("DRY RUN - Validating data structure...")
        sample_record = row_to_record(df.iloc[0])
        logger.info(f"Sample record core fields: {list(sample_record.keys())}")
        logger.info(f"Sample stats_json has {len(sample_record['stats_json'])} fields")
        logger.info(f"Sample: {json.dumps(sample_record, indent=2)[:500]}...")
        return

    # Skip to start_from if resuming
    if start_from > 0:
        df = df.iloc[start_from:]
        logger.info(f"Resuming from row {start_from}, {len(df):,} records remaining")

    # Import in batches with rate limiting
    logger.info(f"Importing {len(df):,} records to PocketBase (delay: {delay_ms}ms between requests)...")

    created = 0
    updated = 0
    errors = 0
    delay_sec = delay_ms / 1000.0

    # Progress file to track where we left off
    progress_file = DATA_DIR / "import_progress.json"

    for i in tqdm(range(0, len(df), batch_size), desc="Importing"):
        batch = df.iloc[i:i + batch_size]
        batch_start_idx = start_from + i

        for row_offset, (_, row) in enumerate(batch.iterrows()):
            current_row = batch_start_idx + row_offset
            try:
                record = row_to_record(row)

                # Check if record exists (by pff_id + season)
                pff_id = record.get("pff_id")
                season = record.get("season")

                if pff_id and season:
                    # Use retry with backoff for rate limiting
                    def check_existing():
                        return pb.collection("pff_grades").get_list(
                            1, 1,
                            {"filter": f'pff_id = {pff_id} && season = {season}'}
                        )

                    try:
                        existing = retry_with_backoff(check_existing)
                        time.sleep(delay_sec)  # Rate limit delay

                        if existing.items:
                            # Update existing
                            def do_update():
                                return pb.collection("pff_grades").update(
                                    existing.items[0].id,
                                    record
                                )
                            retry_with_backoff(do_update)
                            updated += 1
                        else:
                            # Create new
                            def do_create():
                                return pb.collection("pff_grades").create(record)
                            retry_with_backoff(do_create)
                            created += 1

                    except Exception as e:
                        # Try create if lookup fails
                        def do_create():
                            return pb.collection("pff_grades").create(record)
                        retry_with_backoff(do_create)
                        created += 1
                else:
                    # No pff_id, just create
                    def do_create():
                        return pb.collection("pff_grades").create(record)
                    retry_with_backoff(do_create)
                    created += 1

                time.sleep(delay_sec)  # Rate limit delay

            except Exception as e:
                errors += 1
                if errors <= 10:
                    logger.warning(f"Error importing row {current_row}: {e}")
                elif errors == 11:
                    logger.warning("Suppressing further error messages...")

                # Save progress on error
                if errors % 100 == 0:
                    with open(progress_file, "w") as f:
                        json.dump({"last_row": current_row, "created": created, "updated": updated, "errors": errors}, f)

        # Save progress after each batch
        with open(progress_file, "w") as f:
            json.dump({"last_row": batch_start_idx + len(batch), "created": created, "updated": updated, "errors": errors}, f)

    logger.info(f"Import complete: {created:,} created, {updated:,} updated, {errors:,} errors")

    # Clean up progress file on success
    if progress_file.exists() and errors == 0:
        progress_file.unlink()


def create_collection_schema():
    """Print the collection schema for manual creation in PocketBase admin."""
    schema = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PocketBase Collection: pff_grades                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Create this collection in PocketBase Admin UI:                                ║
║                                                                               ║
║ Collection Name: pff_grades                                                   ║
║ Collection Type: Base collection                                              ║
║                                                                               ║
║ Fields:                                                                       ║
║   ┌─────────────────┬───────────┬──────────┬─────────────────────────────┐   ║
║   │ Field Name      │ Type      │ Required │ Notes                       │   ║
║   ├─────────────────┼───────────┼──────────┼─────────────────────────────┤   ║
║   │ name            │ Text      │ Yes      │ Player name (indexed)       │   ║
║   │ pff_id          │ Number    │ No       │ PFF unique ID               │   ║
║   │ team            │ Text      │ No       │ Team name (indexed)         │   ║
║   │ position        │ Text      │ No       │ Position (indexed)          │   ║
║   │ season          │ Number    │ Yes      │ Season year (indexed)       │   ║
║   │ games_played    │ Number    │ No       │ Games played                │   ║
║   │ pff_overall     │ Number    │ No       │ Overall PFF grade           │   ║
║   │ pff_offense     │ Number    │ No       │ Offense grade               │   ║
║   │ pff_defense     │ Number    │ No       │ Defense grade               │   ║
║   │ offensive_snaps │ Number    │ No       │ Offensive snap count        │   ║
║   │ defensive_snaps │ Number    │ No       │ Defensive snap count        │   ║
║   │ stats_json      │ JSON      │ No       │ All other stats (570+ cols) │   ║
║   └─────────────────┴───────────┴──────────┴─────────────────────────────┘   ║
║                                                                               ║
║ API Rules (optional):                                                         ║
║   - List/Search: @request.auth.id != ""  (authenticated users only)          ║
║   - View: @request.auth.id != ""                                              ║
║   - Create: @request.auth.role = "admin"                                      ║
║   - Update: @request.auth.role = "admin"                                      ║
║   - Delete: @request.auth.role = "admin"                                      ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(schema)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Import PFF data to PocketBase")
    parser.add_argument("--dry-run", action="store_true", help="Validate without importing")
    parser.add_argument("--schema", action="store_true", help="Print collection schema")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for import")
    parser.add_argument("--start-from", type=int, default=0, help="Row index to resume from")
    parser.add_argument("--delay", type=int, default=50, help="Milliseconds between requests (default: 50)")
    parser.add_argument("--resume", action="store_true", help="Resume from last saved progress")

    args = parser.parse_args()

    if args.schema:
        create_collection_schema()
    else:
        start_row = args.start_from

        # Check for resume
        if args.resume:
            progress_file = DATA_DIR / "import_progress.json"
            if progress_file.exists():
                with open(progress_file) as f:
                    progress = json.load(f)
                    start_row = progress.get("last_row", 0)
                    logger.info(f"Resuming from row {start_row} (previous: {progress.get('created', 0)} created, {progress.get('errors', 0)} errors)")

        import_to_pocketbase(
            batch_size=args.batch_size,
            dry_run=args.dry_run,
            start_from=start_row,
            delay_ms=args.delay
        )
