"""
Full On3 Scraper - NIL Rankings + Transfer Portal

Scrapes multiple pages of NIL data and transfer portal entries.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

import pandas as pd
from dataclasses import asdict
from data_collection.college.on3_scraper import On3Scraper


async def scrape_nil_rankings(scraper, max_pages=10):
    """Scrape NIL rankings across multiple pages."""
    all_players = []

    print("=" * 60)
    print("SCRAPING ON3 NIL RANKINGS")
    print("=" * 60)

    for page in range(1, max_pages + 1):
        url = f"https://www.on3.com/nil/rankings/player/nil-100/?page={page}"
        print(f"\nPage {page}: Fetching...")

        try:
            await scraper.page.goto(url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)

            players = await scraper._extract_nil_from_json()
            print(f"  Found {len(players)} players")

            if not players:
                print("  No more players, stopping.")
                break

            all_players.extend(players)

        except Exception as e:
            print(f"  Error: {e}")
            break

    return all_players


async def scrape_transfer_portal(scraper, max_pages=20):
    """Scrape transfer portal across multiple pages."""
    print("\n" + "=" * 60)
    print("SCRAPING TRANSFER PORTAL")
    print("=" * 60)

    portal_entries = await scraper.scrape_transfer_portal(year=2025, pages=max_pages)
    return portal_entries


async def main():
    print("On3 Full Data Scraper")
    print("Using your Edge profile for authentication")
    print()

    async with On3Scraper(headless=False) as scraper:
        # Scrape NIL rankings (up to 10 pages = ~1000 players)
        nil_players = await scrape_nil_rankings(scraper, max_pages=10)

        print(f"\n{'='*60}")
        print(f"NIL RANKINGS: {len(nil_players)} total players")
        print("=" * 60)

        if nil_players:
            # Show top 15
            print("\nTop 15 by NIL Value:")
            sorted_players = sorted(nil_players, key=lambda p: p.nil_valuation or 0, reverse=True)[:15]
            for i, p in enumerate(sorted_players, 1):
                val = f"${p.nil_valuation:,.0f}" if p.nil_valuation else "N/A"
                print(f"{i:2}. {val:>12} | {p.name:25} | {p.position:4} | {p.school}")

            # Save NIL data
            df = pd.DataFrame([asdict(p) for p in nil_players])
            output_path = project_root / "data" / "processed" / "on3_nil_rankings.csv"
            df.to_csv(output_path, index=False)
            print(f"\nSaved to {output_path}")

        # Scrape transfer portal
        portal_entries = await scrape_transfer_portal(scraper, max_pages=10)

        print(f"\n{'='*60}")
        print(f"TRANSFER PORTAL: {len(portal_entries)} total entries")
        print("=" * 60)

        if portal_entries:
            in_portal = len([e for e in portal_entries if e.transfer_status == "In Portal"])
            committed = len([e for e in portal_entries if e.transfer_status != "In Portal"])
            print(f"  Still available: {in_portal}")
            print(f"  Committed: {committed}")

        print("\n" + "=" * 60)
        print("SCRAPING COMPLETE!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
