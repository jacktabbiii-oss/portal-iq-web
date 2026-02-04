#!/usr/bin/env python
"""
Weekly PFF Grades Update

Run this script weekly (e.g., Tuesdays after Monday grade finalization)
to keep PFF player grades current.

Can be scheduled via:
- Windows Task Scheduler
- Railway Cron Jobs
- GitHub Actions
- crontab (Linux/Mac)

Example cron: 0 6 * * 2 python ml-engine/scripts/weekly_pff_update.py
"""

import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_collection.college.pff_scraper import PFFScraper


def weekly_update():
    """Run weekly PFF grades update."""
    print("="*60)
    print("PFF Weekly Grades Update")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    scraper = PFFScraper()

    if not scraper.is_logged_in:
        print("\n[ERROR] Not logged in to PFF.")
        print("Run: python scrape_pff_all.py --login")
        print("to authenticate first.")
        return False

    # Get all FBS teams
    print("\nGetting FBS team URLs...")
    all_teams = scraper.get_fbs_team_urls()
    print(f"Found {len(all_teams)} FBS teams")

    # Scrape all teams
    print("\nStarting scrape (this may take 30-60 minutes)...")
    df = scraper.scrape_all_teams(all_teams, delay_between=5.0)

    if df.empty:
        print("\n[ERROR] No data scraped. Check PFF login status.")
        return False

    # Save results
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Main output file (overwrite)
    output_path = output_dir / "pff_player_grades.csv"
    df.to_csv(output_path, index=False)

    # Archive with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    archive_path = output_dir / f"pff_grades_archive_{timestamp}.csv"
    df.to_csv(archive_path, index=False)

    print("\n" + "="*60)
    print("WEEKLY UPDATE COMPLETE")
    print("="*60)
    print(f"Total players: {len(df)}")
    print(f"Teams: {df['team'].nunique()}")
    print(f"Output: {output_path}")
    print(f"Archive: {archive_path}")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return True


if __name__ == "__main__":
    success = weekly_update()
    sys.exit(0 if success else 1)
