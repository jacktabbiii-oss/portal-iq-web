#!/usr/bin/env python3
"""
Portal IQ Master Data Collection Script

Collects data from ALL available sources to build the most comprehensive
college football player database possible.

Sources Collected:
1. On3 - NIL valuations (ALL players, not just top 100)
2. On3 - Transfer Portal
3. On3 - Player profiles (detailed social, stats)
4. 247Sports - Composite rankings
5. 247Sports - Team talent composite
6. ESPN - Rosters with headshots
7. Team Athletic Sites - Social media links

Usage:
    # Collect all data (comprehensive, slow)
    python collect_all_data.py --all

    # Just On3 NIL data
    python collect_all_data.py --on3-nil

    # Just social media links
    python collect_all_data.py --social

    # Upload to R2 when done
    python collect_all_data.py --all --upload
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def collect_on3_nil(max_pages: int = 50):
    """Collect On3 NIL data for ALL ranked players."""
    logger.info("=" * 60)
    logger.info("COLLECTING: On3 Full NIL Rankings")
    logger.info("=" * 60)

    try:
        from data_collection.college.expanded_scraper import ExpandedScraper
    except ImportError:
        from src.data_collection.college.expanded_scraper import ExpandedScraper

    async with ExpandedScraper(headless=True) as scraper:
        players = await scraper.scrape_on3_full_nil(max_pages=max_pages)
        logger.info(f"Collected {len(players)} On3 NIL players")
        return len(players)


async def collect_on3_profiles(limit: int = 500):
    """Collect detailed On3 player profiles."""
    logger.info("=" * 60)
    logger.info("COLLECTING: On3 Player Profiles (Detailed)")
    logger.info("=" * 60)

    try:
        from data_collection.college.expanded_scraper import ExpandedScraper
    except ImportError:
        from src.data_collection.college.expanded_scraper import ExpandedScraper

    import pandas as pd
    from pathlib import Path

    # Load existing NIL data to get profile URLs
    data_dir = Path(__file__).parent.parent / "data"
    nil_path = data_dir / "processed" / "on3_all_nil_rankings.csv"

    if not nil_path.exists():
        logger.warning("Run --on3-nil first to get player URLs")
        return 0

    df = pd.read_csv(nil_path)
    urls = df[df["profile_url"].notna()]["profile_url"].tolist()[:limit]

    async with ExpandedScraper(headless=True) as scraper:
        profiles = await scraper.scrape_on3_player_profiles(urls, include_stats=True)
        logger.info(f"Collected {len(profiles)} detailed profiles")
        return len(profiles)


async def collect_transfer_portal():
    """Collect On3 transfer portal data."""
    logger.info("=" * 60)
    logger.info("COLLECTING: On3 Transfer Portal")
    logger.info("=" * 60)

    try:
        from data_collection.college.on3_scraper import On3Scraper
    except ImportError:
        from src.data_collection.college.on3_scraper import On3Scraper

    async with On3Scraper(headless=True) as scraper:
        entries = await scraper.scrape_transfer_portal(year=2025, pages=20)
        logger.info(f"Collected {len(entries)} transfer portal entries")
        return len(entries)


async def collect_247_rankings(years: list = None):
    """Collect 247Sports composite rankings."""
    if years is None:
        years = [2025, 2024, 2023]

    logger.info("=" * 60)
    logger.info("COLLECTING: 247Sports Composite Rankings")
    logger.info("=" * 60)

    try:
        from data_collection.college.expanded_scraper import ExpandedScraper
    except ImportError:
        from src.data_collection.college.expanded_scraper import ExpandedScraper

    total = 0
    async with ExpandedScraper(headless=True) as scraper:
        for year in years:
            players = await scraper.scrape_247_composite(year=year, max_pages=10)
            logger.info(f"  {year}: {len(players)} players")
            total += len(players)

    return total


async def collect_team_talent():
    """Collect 247Sports team talent composite."""
    logger.info("=" * 60)
    logger.info("COLLECTING: 247Sports Team Talent Composite")
    logger.info("=" * 60)

    try:
        from data_collection.college.expanded_scraper import ExpandedScraper
    except ImportError:
        from src.data_collection.college.expanded_scraper import ExpandedScraper

    async with ExpandedScraper(headless=True) as scraper:
        df = await scraper.scrape_247_team_talent(year=2025)
        logger.info(f"Collected {len(df)} team rankings")
        return len(df)


async def collect_espn_rosters():
    """Collect ESPN rosters with headshots."""
    logger.info("=" * 60)
    logger.info("COLLECTING: ESPN Rosters")
    logger.info("=" * 60)

    try:
        from data_collection.college.espn_fetcher import ESPNFetcher
    except ImportError:
        from src.data_collection.college.espn_fetcher import ESPNFetcher

    fetcher = ESPNFetcher()
    df = fetcher.fetch_all_rosters(save=True)
    logger.info(f"Collected {len(df)} ESPN roster entries")
    return len(df)


async def collect_social_links(teams: list = None):
    """Collect social media links from team roster pages."""
    logger.info("=" * 60)
    logger.info("COLLECTING: Team Roster Social Links")
    logger.info("=" * 60)

    try:
        from data_collection.college.roster_social_scraper import RosterSocialScraper, SCHOOL_ROSTER_URLS
    except ImportError:
        from src.data_collection.college.roster_social_scraper import RosterSocialScraper, SCHOOL_ROSTER_URLS

    if teams is None:
        teams = list(SCHOOL_ROSTER_URLS.keys())

    async with RosterSocialScraper(headless=True) as scraper:
        all_players = []
        for i, team in enumerate(teams):
            logger.info(f"[{i+1}/{len(teams)}] {team}")
            try:
                players = await scraper.scrape_team_roster(team)
                all_players.extend(players)
            except Exception as e:
                logger.warning(f"  Error: {e}")

        logger.info(f"Collected {len(all_players)} players with social links")
        return len(all_players)


def upload_to_r2():
    """Upload collected data to Cloudflare R2."""
    logger.info("=" * 60)
    logger.info("UPLOADING: To Cloudflare R2")
    logger.info("=" * 60)

    try:
        from utils.s3_storage import upload_to_r2 as r2_upload
    except ImportError:
        try:
            from src.utils.s3_storage import upload_to_r2 as r2_upload
        except ImportError:
            logger.warning("Could not import R2 upload function")
            return

    data_dir = Path(__file__).parent.parent / "data" / "processed"

    files_to_upload = [
        ("on3_all_nil_rankings.csv", "processed/on3_all_nil_rankings.csv"),
        ("on3_transfer_portal_current.csv", "processed/on3_transfer_portal_current.csv"),
        ("247_composite_2025.csv", "processed/247_composite_2025.csv"),
        ("247_team_talent_2025.csv", "processed/247_team_talent_2025.csv"),
        ("player_social_links.csv", "processed/player_social_links.csv"),
        ("espn_rosters.csv", "processed/espn_rosters.csv"),
    ]

    uploaded = 0
    for local_file, r2_path in files_to_upload:
        local_path = data_dir / local_file
        if local_path.exists():
            try:
                r2_upload(str(local_path), r2_path)
                logger.info(f"  Uploaded: {r2_path}")
                uploaded += 1
            except Exception as e:
                logger.warning(f"  Failed to upload {local_file}: {e}")
        else:
            logger.debug(f"  Skipping {local_file} (not found)")

    logger.info(f"Uploaded {uploaded} files to R2")


async def main():
    parser = argparse.ArgumentParser(description="Portal IQ Master Data Collection")
    parser.add_argument("--all", action="store_true", help="Collect all data (comprehensive)")
    parser.add_argument("--on3-nil", action="store_true", help="On3 full NIL rankings")
    parser.add_argument("--on3-profiles", action="store_true", help="On3 detailed profiles")
    parser.add_argument("--portal", action="store_true", help="Transfer portal data")
    parser.add_argument("--247", action="store_true", help="247Sports composite rankings")
    parser.add_argument("--team-talent", action="store_true", help="247Sports team talent")
    parser.add_argument("--espn", action="store_true", help="ESPN rosters")
    parser.add_argument("--social", action="store_true", help="Social media links from team sites")
    parser.add_argument("--upload", action="store_true", help="Upload results to R2")
    parser.add_argument("--pages", type=int, default=50, help="Max pages to scrape (default 50)")

    args = parser.parse_args()

    # If no specific source selected, show help
    if not any([args.all, args.on3_nil, args.on3_profiles, args.portal,
                getattr(args, '247'), args.team_talent, args.espn, args.social]):
        parser.print_help()
        return

    results = {}
    start_time = datetime.now()

    print("\n" + "=" * 60)
    print("PORTAL IQ DATA COLLECTION")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    # Collect data based on flags
    if args.all or args.on3_nil:
        results["on3_nil"] = await collect_on3_nil(max_pages=args.pages)

    if args.all or args.on3_profiles:
        results["on3_profiles"] = await collect_on3_profiles(limit=500)

    if args.all or args.portal:
        results["transfer_portal"] = await collect_transfer_portal()

    if args.all or getattr(args, '247'):
        results["247_composite"] = await collect_247_rankings()

    if args.all or args.team_talent:
        results["team_talent"] = await collect_team_talent()

    if args.all or args.espn:
        results["espn_rosters"] = await collect_espn_rosters()

    if args.all or args.social:
        results["social_links"] = await collect_social_links()

    # Upload if requested
    if args.upload:
        upload_to_r2()

    # Summary
    end_time = datetime.now()
    duration = end_time - start_time

    print("\n" + "=" * 60)
    print("DATA COLLECTION COMPLETE")
    print("=" * 60)
    print(f"Duration: {duration}")
    print("\nRecords Collected:")
    for source, count in results.items():
        print(f"  {source}: {count:,}")
    print(f"\nTotal: {sum(results.values()):,} records")

    if args.upload:
        print("\nData uploaded to Cloudflare R2")


if __name__ == "__main__":
    asyncio.run(main())
