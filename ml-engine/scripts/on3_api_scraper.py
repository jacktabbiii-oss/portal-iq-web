"""
On3 API Scraper - Using requests instead of browser automation

This approach uses saved cookies and makes direct HTTP requests to On3's
internal API endpoints, avoiding bot detection.

Usage:
    1. First run with --export-cookies to save cookies from your browser
    2. Then run normally to scrape data
"""

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import requests
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from data_collection.college.on3_scraper import On3Scraper


class On3APIScraper:
    """Scrapes On3 using direct API calls with session cookies."""

    # On3's internal API endpoints (discovered from network inspection)
    BASE_API = "https://www.on3.com/api"

    def __init__(self, cookies_path: str = None):
        self.cookies_path = cookies_path or str(project_root / "data" / "cache" / "on3_cookies.json")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.on3.com/",
        })
        self._load_cookies()

    def _load_cookies(self):
        """Load cookies from file."""
        if os.path.exists(self.cookies_path):
            with open(self.cookies_path, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                self.session.cookies.set(
                    cookie.get('name', ''),
                    cookie.get('value', ''),
                    domain=cookie.get('domain', '.on3.com'),
                )
            print(f"Loaded {len(cookies)} cookies")
        else:
            print(f"No cookies found at {self.cookies_path}")
            print("Run with --export-cookies first")

    def fetch_nil_rankings(self, page: int = 1, limit: int = 100) -> dict:
        """Fetch NIL rankings page data."""
        # On3's page uses Next.js - fetch the page and extract __NEXT_DATA__
        url = f"https://www.on3.com/nil/rankings/player/nil-100/?page={page}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Extract __NEXT_DATA__ JSON from HTML
            import re
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                nil_list = data.get('props', {}).get('pageProps', {}).get('nilRankings', {}).get('list', [])
                return {'players': nil_list, 'count': len(nil_list)}

        except Exception as e:
            print(f"Error fetching page {page}: {e}")

        return {'players': [], 'count': 0}

    def fetch_transfer_portal(self, page: int = 1) -> dict:
        """Fetch transfer portal data."""
        # Try different portal URL formats
        urls_to_try = [
            f"https://www.on3.com/transfer-portal/football/?page={page}",
            f"https://www.on3.com/db/transfer-portal/football/?page={page}",
            f"https://www.on3.com/college/football/transfer-portal/?page={page}",
        ]

        for url in urls_to_try:
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    # Extract __NEXT_DATA__
                    import re
                    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', response.text, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        # Look for portal data in various paths
                        props = data.get('props', {}).get('pageProps', {})
                        portal_list = (
                            props.get('transfers', {}).get('list', []) or
                            props.get('portalPlayers', []) or
                            props.get('transferPortal', {}).get('list', []) or
                            []
                        )
                        if portal_list:
                            print(f"  Found portal data at: {url}")
                            return {'entries': portal_list, 'count': len(portal_list)}
            except Exception as e:
                continue

        return {'entries': [], 'count': 0}

    def scrape_all_nil(self, max_pages: int = 10) -> list:
        """Scrape all NIL rankings."""
        all_players = []

        print("="*60)
        print("SCRAPING ON3 NIL RANKINGS (API Method)")
        print("="*60)

        for page in range(1, max_pages + 1):
            print(f"\nPage {page}...")
            result = self.fetch_nil_rankings(page=page)
            count = result['count']
            print(f"  Found {count} players")

            if count == 0:
                break

            # Parse players
            for item in result['players']:
                person = item.get('person', {})
                valuation = item.get('valuation', {})
                commit_status = person.get('commitStatus', {})
                committed_org = commit_status.get('committedOrganization', {}) if commit_status else {}

                all_players.append({
                    'name': person.get('name', 'Unknown'),
                    'school': committed_org.get('name', 'Unknown') if committed_org else 'Unknown',
                    'position': person.get('positionAbbreviation', 'Unknown'),
                    'nil_valuation': valuation.get('valuation', 0),
                    'nil_rank': valuation.get('rank'),
                    'class_year': commit_status.get('classRank') if commit_status else None,
                    'recruiting_stars': person.get('rating', {}).get('stars') if person.get('rating') else None,
                    'followers': valuation.get('followers', 0),
                    'profile_url': f"https://www.on3.com/db/{person.get('slug', '')}/",
                    'headshot_url': person.get('defaultAssetUrl', ''),
                })

            time.sleep(1)  # Rate limiting

        return all_players


async def export_cookies_from_browser():
    """Export cookies from Edge browser to JSON file."""
    print("Opening Edge to export cookies...")
    print("Make sure you're logged in to On3!")

    cookies_path = project_root / "data" / "cache" / "on3_cookies.json"

    async with On3Scraper(headless=False) as scraper:
        # Navigate to On3 to get all cookies
        await scraper.page.goto("https://www.on3.com/nil/rankings/player/nil-100/", wait_until='networkidle')
        await asyncio.sleep(3)

        # Get cookies
        cookies = await scraper._context.cookies()

        # Save to file
        with open(cookies_path, 'w') as f:
            json.dump(cookies, f, indent=2)

        print(f"\nSaved {len(cookies)} cookies to {cookies_path}")
        print("You can now run the scraper without --export-cookies")


def main():
    parser = argparse.ArgumentParser(description="On3 API Scraper")
    parser.add_argument('--export-cookies', action='store_true', help='Export cookies from browser')
    parser.add_argument('--nil-pages', type=int, default=10, help='Max pages of NIL rankings to scrape')
    args = parser.parse_args()

    if args.export_cookies:
        asyncio.run(export_cookies_from_browser())
        return

    # Run scraper
    scraper = On3APIScraper()
    players = scraper.scrape_all_nil(max_pages=args.nil_pages)

    print(f"\n{'='*60}")
    print(f"TOTAL: {len(players)} players scraped")
    print("="*60)

    if players:
        # Show top 15
        sorted_players = sorted(players, key=lambda p: p.get('nil_valuation') or 0, reverse=True)[:15]
        print("\nTop 15 by NIL Value:")
        for i, p in enumerate(sorted_players, 1):
            val = f"${p['nil_valuation']:,.0f}" if p['nil_valuation'] else "N/A"
            print(f"{i:2}. {val:>12} | {p['name']:25} | {p['position']:4} | {p['school']}")

        # Save
        df = pd.DataFrame(players)
        output_path = project_root / "data" / "processed" / "on3_nil_rankings.csv"
        df.to_csv(output_path, index=False)
        print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
