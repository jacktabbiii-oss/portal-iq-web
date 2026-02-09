#!/usr/bin/env python3
"""
Scrape social media links from team athletic websites.

This script:
1. Visits each team's roster page
2. Extracts social media links (Instagram, Twitter, TikTok) for each player
3. Saves results to player_social_links.csv
4. Optionally uploads to R2 storage

Usage:
    # Scrape all teams (slow)
    python scrape_social_links.py --all

    # Scrape specific teams
    python scrape_social_links.py --teams "Ohio State,Georgia,Colorado"

    # Scrape and upload to R2
    python scrape_social_links.py --all --upload
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Scrape social media links from team rosters")
    parser.add_argument("--all", action="store_true", help="Scrape all configured teams")
    parser.add_argument("--teams", type=str, help="Comma-separated list of teams to scrape")
    parser.add_argument("--upload", action="store_true", help="Upload results to R2")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    parser.add_argument("--fetch-followers", action="store_true", help="Fetch actual follower counts (slow)")

    args = parser.parse_args()

    if not args.all and not args.teams:
        print("Please specify --all or --teams")
        parser.print_help()
        return

    try:
        from data_collection.college.roster_social_scraper import RosterSocialScraper, SCHOOL_ROSTER_URLS
    except ImportError:
        from src.data_collection.college.roster_social_scraper import RosterSocialScraper, SCHOOL_ROSTER_URLS

    # Determine which teams to scrape
    if args.all:
        teams = list(SCHOOL_ROSTER_URLS.keys())
    else:
        teams = [t.strip() for t in args.teams.split(",")]

    logger.info(f"Scraping {len(teams)} teams...")

    async with RosterSocialScraper(headless=args.headless) as scraper:
        all_players = []

        for i, team in enumerate(teams):
            logger.info(f"[{i+1}/{len(teams)}] {team}")
            try:
                players = await scraper.scrape_team_roster(team)
                all_players.extend(players)
                logger.info(f"  Found {len(players)} players with social links")
            except Exception as e:
                logger.error(f"  Error: {e}")

        # Optionally fetch follower counts
        if args.fetch_followers and all_players:
            logger.info("Fetching follower counts (this will take a while)...")
            all_players = await scraper.fetch_follower_counts(all_players)

    # Save results
    if all_players:
        import pandas as pd
        from dataclasses import asdict

        df = pd.DataFrame([asdict(p) for p in all_players])

        # Find data directory
        data_dir = Path(__file__).parent.parent / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)

        output_path = data_dir / "player_social_links.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} players to {output_path}")

        # Upload to R2 if requested
        if args.upload:
            try:
                from utils.s3_storage import upload_to_r2
                r2_path = "processed/player_social_links.csv"
                upload_to_r2(str(output_path), r2_path)
                logger.info(f"Uploaded to R2: {r2_path}")
            except ImportError:
                logger.warning("Could not import upload_to_r2. Make sure s3_storage module is available.")
            except Exception as e:
                logger.error(f"R2 upload failed: {e}")

        # Print summary
        print("\n" + "=" * 50)
        print("Social Media Scraping Complete")
        print("=" * 50)
        print(f"Total players with social links: {len(df)}")

        # Count by platform
        ig_count = df["instagram_url"].notna().sum()
        tw_count = df["twitter_url"].notna().sum()
        tt_count = df["tiktok_url"].notna().sum()

        print(f"  Instagram: {ig_count}")
        print(f"  Twitter/X: {tw_count}")
        print(f"  TikTok: {tt_count}")

        if args.fetch_followers:
            total_followers = df["instagram_followers"].fillna(0).sum() + \
                             df["twitter_followers"].fillna(0).sum() + \
                             df["tiktok_followers"].fillna(0).sum()
            print(f"  Total followers tracked: {total_followers:,.0f}")

    else:
        print("No players with social links found")


if __name__ == "__main__":
    asyncio.run(main())
