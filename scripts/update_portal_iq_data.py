"""
Portal IQ Data Update Automation Script

Automates data updates for Portal IQ. Run weekly during season, monthly off-season.

Usage:
    python scripts/update_portal_iq_data.py              # Run all updates
    python scripts/update_portal_iq_data.py --pff-only   # Just PFF import
    python scripts/update_portal_iq_data.py --cfbd-only  # Just CFBD refresh
    python scripts/update_portal_iq_data.py --check      # Health check only
    python scripts/update_portal_iq_data.py --dry-run    # Preview without changes

Manual Tasks (NOT automated):
    - Download PFF CSV from PFF website (requires subscription)
    - On3 NIL data (requires manual scrape or API access)
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
env_paths = [
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "ml-engine" / ".env",
]
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

# Setup logging
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"data_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Data paths
DATA_DIR = PROJECT_ROOT / "ml-engine" / "data" / "processed"
PFF_CSV = DATA_DIR / "pff_player_grades.csv"
ROSTER_CSV = DATA_DIR / "college_football_rosters.csv"
NIL_CSV = DATA_DIR / "nil_valuations.csv"


class DataUpdateManager:
    """Manages all data update operations for Portal IQ."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "updates": {},
            "errors": [],
            "warnings": []
        }

    def run_all(self):
        """Run all automated updates."""
        logger.info("=" * 60)
        logger.info("PORTAL IQ DATA UPDATE - Starting")
        logger.info("=" * 60)

        if self.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")

        # 1. Health check first
        self.health_check()

        # 2. Import PFF if CSV is fresh
        self.update_pff_data()

        # 3. Refresh CFBD data
        self.update_cfbd_data()

        # 4. Validate data integrity
        self.validate_data()

        # 5. Summary
        self.print_summary()

        return self.results

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    def health_check(self):
        """Check data freshness and connectivity."""
        logger.info("\n--- Health Check ---")

        checks = {}

        # Check PocketBase connection
        try:
            from dashboard.utils.pocketbase_client import is_pocketbase_connected
            pb_connected = is_pocketbase_connected()
            checks["pocketbase"] = "Connected" if pb_connected else "Not Connected"
            logger.info(f"PocketBase: {'✓ Connected' if pb_connected else '✗ Not Connected'}")
        except Exception as e:
            checks["pocketbase"] = f"Error: {e}"
            logger.warning(f"PocketBase check failed: {e}")

        # Check data files
        data_files = {
            "PFF Grades": PFF_CSV,
            "Rosters": ROSTER_CSV,
            "NIL Valuations": NIL_CSV,
        }

        for name, path in data_files.items():
            if path.exists():
                mod_time = datetime.fromtimestamp(path.stat().st_mtime)
                age_days = (datetime.now() - mod_time).days
                size_mb = path.stat().st_size / (1024 * 1024)

                status = "✓ Fresh" if age_days < 7 else "⚠ Stale" if age_days < 30 else "✗ Old"
                checks[name] = {
                    "exists": True,
                    "age_days": age_days,
                    "size_mb": round(size_mb, 2),
                    "modified": mod_time.isoformat()
                }
                logger.info(f"{name}: {status} ({age_days} days old, {size_mb:.1f}MB)")
            else:
                checks[name] = {"exists": False}
                logger.warning(f"{name}: ✗ Not Found")

        self.results["updates"]["health_check"] = checks

    # =========================================================================
    # PFF DATA UPDATE
    # =========================================================================

    def update_pff_data(self):
        """Import PFF data to PocketBase if CSV is available and fresh."""
        logger.info("\n--- PFF Data Update ---")

        if not PFF_CSV.exists():
            msg = f"PFF CSV not found at {PFF_CSV}"
            logger.warning(msg)
            self.results["warnings"].append(msg)
            self.results["updates"]["pff"] = {"status": "skipped", "reason": "CSV not found"}
            return

        # Check if CSV is fresh (modified in last 7 days)
        mod_time = datetime.fromtimestamp(PFF_CSV.stat().st_mtime)
        age_days = (datetime.now() - mod_time).days

        if age_days > 7:
            logger.info(f"PFF CSV is {age_days} days old - consider downloading fresh data")
            self.results["warnings"].append(f"PFF data is {age_days} days old")

        # Load and validate
        df = pd.read_csv(PFF_CSV)
        logger.info(f"Loaded {len(df):,} PFF records")

        if "season" in df.columns:
            season_counts = df["season"].value_counts().sort_index()
            logger.info(f"Seasons: {dict(season_counts)}")

        if self.dry_run:
            logger.info("DRY RUN: Would import to PocketBase")
            self.results["updates"]["pff"] = {
                "status": "dry_run",
                "records": len(df),
                "csv_age_days": age_days
            }
            return

        # Run import
        try:
            from scripts.import_pff_to_pocketbase import import_to_pocketbase
            import_to_pocketbase(batch_size=100, dry_run=False)
            self.results["updates"]["pff"] = {
                "status": "success",
                "records": len(df),
                "csv_age_days": age_days
            }
            logger.info("PFF import completed")
        except Exception as e:
            logger.error(f"PFF import failed: {e}")
            self.results["errors"].append(f"PFF import: {e}")
            self.results["updates"]["pff"] = {"status": "failed", "error": str(e)}

    # =========================================================================
    # CFBD DATA UPDATE
    # =========================================================================

    def update_cfbd_data(self):
        """Refresh roster and player data from CFBD API."""
        logger.info("\n--- CFBD Data Update ---")

        api_key = os.getenv("CFBD_API_KEY")
        if not api_key:
            msg = "CFBD_API_KEY not set - skipping CFBD update"
            logger.warning(msg)
            self.results["warnings"].append(msg)
            self.results["updates"]["cfbd"] = {"status": "skipped", "reason": "No API key"}
            return

        if self.dry_run:
            logger.info("DRY RUN: Would refresh CFBD data")
            self.results["updates"]["cfbd"] = {"status": "dry_run"}
            return

        try:
            import cfbd
            from cfbd.rest import ApiException

            # Configure API
            configuration = cfbd.Configuration()
            configuration.api_key['Authorization'] = api_key
            configuration.api_key_prefix['Authorization'] = 'Bearer'

            current_year = datetime.now().year

            # Get teams API
            teams_api = cfbd.TeamsApi(cfbd.ApiClient(configuration))

            # Fetch FBS teams
            logger.info(f"Fetching FBS teams for {current_year}...")
            teams = teams_api.get_fbs_teams(year=current_year)
            logger.info(f"Found {len(teams)} FBS teams")

            # Get roster API
            roster_api = cfbd.PlayersApi(cfbd.ApiClient(configuration))

            all_rosters = []
            for team in teams[:5]:  # Limit for testing - remove [:5] for full run
                try:
                    roster = roster_api.get_roster(year=current_year, team=team.school)
                    for player in roster:
                        all_rosters.append({
                            "name": f"{player.first_name} {player.last_name}",
                            "team": team.school,
                            "position": player.position,
                            "height": player.height,
                            "weight": player.weight,
                            "year": player.year,
                            "jersey": player.jersey,
                            "home_city": player.home_city,
                            "home_state": player.home_state,
                        })
                except Exception as e:
                    logger.warning(f"Failed to get roster for {team.school}: {e}")

            if all_rosters:
                roster_df = pd.DataFrame(all_rosters)
                roster_df.to_csv(ROSTER_CSV, index=False)
                logger.info(f"Saved {len(roster_df):,} roster entries")
                self.results["updates"]["cfbd"] = {
                    "status": "success",
                    "teams": len(teams),
                    "players": len(roster_df)
                }
            else:
                self.results["updates"]["cfbd"] = {"status": "no_data"}

        except ImportError:
            msg = "cfbd package not installed. Run: pip install cfbd"
            logger.warning(msg)
            self.results["warnings"].append(msg)
            self.results["updates"]["cfbd"] = {"status": "skipped", "reason": "Package not installed"}
        except Exception as e:
            logger.error(f"CFBD update failed: {e}")
            self.results["errors"].append(f"CFBD: {e}")
            self.results["updates"]["cfbd"] = {"status": "failed", "error": str(e)}

    # =========================================================================
    # DATA VALIDATION
    # =========================================================================

    def validate_data(self):
        """Validate data integrity and completeness."""
        logger.info("\n--- Data Validation ---")

        validations = {}

        # Validate PFF data
        if PFF_CSV.exists():
            df = pd.read_csv(PFF_CSV)
            pff_checks = {
                "total_records": len(df),
                "has_name": df["name"].notna().sum() if "name" in df.columns else 0,
                "has_season": df["season"].notna().sum() if "season" in df.columns else 0,
                "has_overall": df["pff_overall"].notna().sum() if "pff_overall" in df.columns else 0,
            }

            # Check for minimum snap thresholds
            if "offensive_snaps" in df.columns:
                pff_checks["players_250_snaps"] = (df["offensive_snaps"] >= 250).sum()
            if "defensive_snaps" in df.columns:
                pff_checks["defenders_200_snaps"] = (df["defensive_snaps"] >= 200).sum()

            validations["pff"] = pff_checks
            logger.info(f"PFF: {pff_checks['total_records']:,} records, {pff_checks['has_overall']:,} with grades")

        # Validate roster data
        if ROSTER_CSV.exists():
            df = pd.read_csv(ROSTER_CSV)
            roster_checks = {
                "total_players": len(df),
                "unique_teams": df["team"].nunique() if "team" in df.columns else 0,
                "has_position": df["position"].notna().sum() if "position" in df.columns else 0,
            }
            validations["roster"] = roster_checks
            logger.info(f"Roster: {roster_checks['total_players']:,} players from {roster_checks['unique_teams']} teams")

        self.results["updates"]["validation"] = validations

    # =========================================================================
    # SUMMARY
    # =========================================================================

    def print_summary(self):
        """Print update summary."""
        logger.info("\n" + "=" * 60)
        logger.info("UPDATE SUMMARY")
        logger.info("=" * 60)

        if self.results["errors"]:
            logger.error(f"Errors: {len(self.results['errors'])}")
            for err in self.results["errors"]:
                logger.error(f"  - {err}")

        if self.results["warnings"]:
            logger.warning(f"Warnings: {len(self.results['warnings'])}")
            for warn in self.results["warnings"]:
                logger.warning(f"  - {warn}")

        logger.info(f"\nLog saved to: {LOG_FILE}")

        # Save results JSON
        results_file = LOG_DIR / f"update_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"Results saved to: {results_file}")

        # Manual tasks reminder
        logger.info("\n" + "-" * 60)
        logger.info("MANUAL TASKS REMINDER:")
        logger.info("-" * 60)
        logger.info("1. Download fresh PFF CSV from: https://premium.pff.com/")
        logger.info("   → Save to: ml-engine/data/processed/pff_player_grades.csv")
        logger.info("2. Check On3 NIL rankings for market changes")
        logger.info("3. Review portal activity on On3/247Sports")
        logger.info("-" * 60)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Portal IQ Data Update Automation")
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--pff-only", action="store_true", help="Only update PFF data")
    parser.add_argument("--cfbd-only", action="store_true", help="Only update CFBD data")
    parser.add_argument("--check", action="store_true", help="Health check only")

    args = parser.parse_args()

    manager = DataUpdateManager(dry_run=args.dry_run)

    if args.check:
        manager.health_check()
        manager.print_summary()
    elif args.pff_only:
        manager.health_check()
        manager.update_pff_data()
        manager.print_summary()
    elif args.cfbd_only:
        manager.health_check()
        manager.update_cfbd_data()
        manager.print_summary()
    else:
        manager.run_all()


if __name__ == "__main__":
    main()
