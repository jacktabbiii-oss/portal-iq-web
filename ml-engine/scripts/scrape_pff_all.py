#!/usr/bin/env python
"""
PFF Complete Data Scraper

Scrapes PFF college player grades for all FBS teams.
Requires PFF Premium account.

Usage:
    # First time - interactive login
    python scrape_pff_all.py --login

    # Subsequent runs - use saved cookies
    python scrape_pff_all.py

    # Test with a few teams
    python scrape_pff_all.py --test

    # Specific conference
    python scrape_pff_all.py --conference SEC
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_collection.college.pff_scraper import PFFScraper


def main():
    parser = argparse.ArgumentParser(description="Scrape PFF college player grades")
    parser.add_argument("--login", action="store_true", help="Interactive browser login")
    parser.add_argument("--test", action="store_true", help="Test with 5 teams only")
    parser.add_argument("--conference", type=str, help="Filter to specific conference (SEC, Big Ten, etc.)")
    parser.add_argument("--output", type=str, default="pff_player_grades.csv", help="Output filename")
    args = parser.parse_args()

    print("="*60)
    print("PFF College Player Grades Scraper")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Initialize scraper
    scraper = PFFScraper()

    # Handle login
    if args.login or not scraper.is_logged_in:
        print("Starting interactive login...")
        if not scraper.login_interactive():
            print("Login failed. Exiting.")
            return

    if not scraper.is_logged_in:
        print("Not authenticated. Run with --login flag first.")
        return

    # Get team list
    print("\nGetting FBS team list...")
    all_teams = scraper.get_fbs_team_urls()

    # Filter by conference if specified
    if args.conference:
        conf = args.conference.upper()
        all_teams = [t for t in all_teams if conf in (t.get('conference', '') or '').upper()]
        print(f"Filtered to {len(all_teams)} {args.conference} teams")

    # Test mode - only 5 teams
    if args.test:
        all_teams = all_teams[:5]
        print(f"Test mode: scraping {len(all_teams)} teams")

    # Scrape all teams
    df = scraper.scrape_all_teams(all_teams)

    if df.empty:
        print("\nNo data scraped. Check if PFF page structure has changed.")
        return

    # Save results
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / args.output
    df.to_csv(output_path, index=False)

    # Also save timestamped version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_path = output_dir / f"pff_player_grades_{timestamp}.csv"
    df.to_csv(timestamped_path, index=False)

    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)
    print(f"Total players: {len(df)}")
    print(f"Teams scraped: {df['team'].nunique()}")
    print(f"Positions: {df['position'].nunique()}")
    print()
    print(f"Saved to: {output_path}")
    print(f"Backup:   {timestamped_path}")
    print()

    # Show summary stats
    if 'pff_overall' in df.columns:
        print("Grade Distribution:")
        print(f"  Elite (90+):  {len(df[df['pff_overall'] >= 90])} players")
        print(f"  Strong (80+): {len(df[df['pff_overall'] >= 80])} players")
        print(f"  Average (60-79): {len(df[(df['pff_overall'] >= 60) & (df['pff_overall'] < 80)])} players")
        print(f"  Below avg (<60): {len(df[df['pff_overall'] < 60])} players")
        print()

    # Show top players
    print("Top 10 Overall Grades:")
    top_players = df.nlargest(10, 'pff_overall')[['player_name', 'team', 'position', 'pff_overall']]
    print(top_players.to_string(index=False))
    print()

    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
