"""
Team Roster Social Media Scraper

Scrapes social media links from college team athletic websites.
Each school's athletic website often has player bio pages with social links.

Sources:
- School athletic websites (texassports.com, georgiadogs.com, etc.)
- ESPN player profile pages
- School roster pages with embedded social links

Usage:
    from src.data_collection.college.roster_social_scraper import RosterSocialScraper

    async with RosterSocialScraper() as scraper:
        socials = await scraper.scrape_team_socials("Ohio State")
        all_socials = await scraper.scrape_all_teams()
"""

import asyncio
import logging
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field

import pandas as pd

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PlayerSocial:
    """Social media data for a player."""
    name: str
    school: str
    position: Optional[str] = None
    instagram_url: Optional[str] = None
    instagram_handle: Optional[str] = None
    instagram_followers: Optional[int] = None
    twitter_url: Optional[str] = None
    twitter_handle: Optional[str] = None
    twitter_followers: Optional[int] = None
    tiktok_url: Optional[str] = None
    tiktok_handle: Optional[str] = None
    tiktok_followers: Optional[int] = None
    profile_url: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())


# School athletic website URLs (sample - expand as needed)
SCHOOL_ROSTER_URLS = {
    # SEC
    "Alabama": "https://rolltide.com/sports/football/roster",
    "Auburn": "https://auburntigers.com/sports/football/roster",
    "Florida": "https://floridagators.com/sports/football/roster",
    "Georgia": "https://georgiadogs.com/sports/football/roster",
    "Kentucky": "https://ukathletics.com/sports/football/roster",
    "LSU": "https://lsusports.net/sports/football/roster",
    "Mississippi State": "https://hailstate.com/sports/football/roster",
    "Missouri": "https://mutigers.com/sports/football/roster",
    "Ole Miss": "https://olemisssports.com/sports/football/roster",
    "South Carolina": "https://gamecocksonline.com/sports/football/roster",
    "Tennessee": "https://utsports.com/sports/football/roster",
    "Texas A&M": "https://12thman.com/sports/football/roster",
    "Vanderbilt": "https://vucommodores.com/sports/football/roster",
    "Arkansas": "https://arkansasrazorbacks.com/sports/football/roster",
    "Oklahoma": "https://soonersports.com/sports/football/roster",
    "Texas": "https://texassports.com/sports/football/roster",

    # Big Ten
    "Ohio State": "https://ohiostatebuckeyes.com/sports/m-footbl/roster/",
    "Michigan": "https://mgoblue.com/sports/football/roster",
    "Penn State": "https://gopsusports.com/sports/football/roster",
    "Wisconsin": "https://uwbadgers.com/sports/football/roster",
    "Iowa": "https://hawkeyesports.com/sports/football/roster",
    "Nebraska": "https://huskers.com/sports/football/roster",
    "Minnesota": "https://gophersports.com/sports/football/roster",
    "Purdue": "https://purduesports.com/sports/football/roster",
    "Illinois": "https://fightingillini.com/sports/football/roster",
    "Northwestern": "https://nusports.com/sports/football/roster",
    "Indiana": "https://iuhoosiers.com/sports/football/roster",
    "Maryland": "https://umterps.com/sports/football/roster",
    "Rutgers": "https://scarletknights.com/sports/football/roster",
    "Michigan State": "https://msuspartans.com/sports/football/roster",
    "Oregon": "https://goducks.com/sports/football/roster",
    "Washington": "https://gohuskies.com/sports/football/roster",
    "USC": "https://usctrojans.com/sports/football/roster",
    "UCLA": "https://uclabruins.com/sports/football/roster",

    # Big 12
    "Colorado": "https://cubuffs.com/sports/football/roster",
    "Arizona": "https://arizonawildcats.com/sports/football/roster",
    "Arizona State": "https://thesundevils.com/sports/football/roster",
    "Utah": "https://utahutes.com/sports/football/roster",
    "Kansas State": "https://kstatesports.com/sports/football/roster",
    "Kansas": "https://kuathletics.com/sports/football/roster",
    "Baylor": "https://baylorbears.com/sports/football/roster",
    "TCU": "https://gofrogs.com/sports/football/roster",
    "Iowa State": "https://cyclones.com/sports/football/roster",
    "BYU": "https://byucougars.com/sports/football/roster",
    "Cincinnati": "https://gobearcats.com/sports/football/roster",
    "UCF": "https://ucfknights.com/sports/football/roster",
    "Houston": "https://uhcougars.com/sports/football/roster",
    "West Virginia": "https://wvusports.com/sports/football/roster",
    "Texas Tech": "https://texastech.com/sports/football/roster",
    "Oklahoma State": "https://okstate.com/sports/football/roster",

    # ACC
    "Clemson": "https://clemsontigers.com/sports/football/roster",
    "Florida State": "https://seminoles.com/sports/football/roster",
    "Miami": "https://miamihurricanes.com/sports/football/roster",
    "NC State": "https://gopack.com/sports/football/roster",
    "North Carolina": "https://goheels.com/sports/football/roster",
    "Duke": "https://goduke.com/sports/football/roster",
    "Wake Forest": "https://godeacs.com/sports/football/roster",
    "Virginia": "https://virginiasports.com/sports/football/roster",
    "Virginia Tech": "https://hokiesports.com/sports/football/roster",
    "Boston College": "https://bceagles.com/sports/football/roster",
    "Syracuse": "https://cuse.com/sports/football/roster",
    "Louisville": "https://gocards.com/sports/football/roster",
    "Pittsburgh": "https://pittsburghpanthers.com/sports/football/roster",
    "Georgia Tech": "https://ramblinwreck.com/sports/football/roster",
    "Notre Dame": "https://und.com/sports/football/roster",
    "SMU": "https://smumustangs.com/sports/football/roster",
    "Stanford": "https://gostanford.com/sports/football/roster",
    "California": "https://calbears.com/sports/football/roster",
}


class RosterSocialScraper:
    """Scrapes social media links from team athletic websites."""

    # Common CSS selectors for social links on athletic sites
    SOCIAL_SELECTORS = {
        "instagram": [
            'a[href*="instagram.com"]',
            'a[class*="instagram"]',
            'a[aria-label*="Instagram" i]',
            '[data-social="instagram"]',
        ],
        "twitter": [
            'a[href*="twitter.com"]',
            'a[href*="x.com"]',
            'a[class*="twitter"]',
            'a[aria-label*="Twitter" i]',
            'a[aria-label*="X" i]',
            '[data-social="twitter"]',
        ],
        "tiktok": [
            'a[href*="tiktok.com"]',
            'a[class*="tiktok"]',
            'a[aria-label*="TikTok" i]',
            '[data-social="tiktok"]',
        ],
    }

    def __init__(self, data_dir: Optional[str] = None, headless: bool = True):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not installed. Run: pip install playwright && playwright install chromium")

        if data_dir is None:
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "data").exists():
                    data_dir = str(current / "data")
                    break
                current = current.parent
            else:
                data_dir = "data"

        self.data_dir = Path(data_dir)
        self.output_dir = self.data_dir / "processed"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

    async def __aenter__(self):
        await self._start_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_browser()

    async def _start_browser(self):
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await context.new_page()
        logger.info("Browser started")

    async def _close_browser(self):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    def _extract_handle_from_url(self, url: str, platform: str) -> Optional[str]:
        """Extract the username/handle from a social media URL."""
        if not url:
            return None

        patterns = {
            "instagram": r"instagram\.com/([a-zA-Z0-9_.]+)",
            "twitter": r"(?:twitter|x)\.com/([a-zA-Z0-9_]+)",
            "tiktok": r"tiktok\.com/@?([a-zA-Z0-9_.]+)",
        }

        pattern = patterns.get(platform)
        if pattern:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def scrape_team_roster(self, school: str) -> List[PlayerSocial]:
        """
        Scrape social media links from a team's roster page.

        Args:
            school: School name

        Returns:
            List of PlayerSocial objects
        """
        roster_url = SCHOOL_ROSTER_URLS.get(school)
        if not roster_url:
            logger.warning(f"No roster URL configured for {school}")
            return []

        logger.info(f"Scraping {school} roster: {roster_url}")
        players = []

        try:
            await self.page.goto(roster_url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Find player rows/cards - each site has different structure
            player_selectors = [
                'tr[class*="roster"]',
                'div[class*="roster-player"]',
                'div[class*="player-card"]',
                'li[class*="roster"]',
                'a[href*="/roster/"]',
                '.s-person-card',
                '[data-player]',
            ]

            player_elements = []
            for selector in player_selectors:
                elements = await self.page.query_selector_all(selector)
                if elements:
                    player_elements = elements
                    logger.info(f"Found {len(elements)} player elements with selector: {selector}")
                    break

            # If we found player elements, try to get bio URLs
            if player_elements:
                bio_urls = []
                for elem in player_elements:
                    # Try to find link to player bio page
                    link = await elem.query_selector('a[href*="bio"], a[href*="roster"], a[href*="player"]')
                    if link:
                        href = await link.get_attribute("href")
                        if href:
                            if not href.startswith("http"):
                                # Make absolute URL
                                base = roster_url.rsplit("/", 1)[0]
                                href = f"{base}/{href.lstrip('/')}"
                            bio_urls.append(href)

                # Visit each bio page to get social links
                for bio_url in bio_urls[:50]:  # Limit to 50 players per team
                    player = await self._scrape_player_bio(bio_url, school)
                    if player:
                        players.append(player)
                    await asyncio.sleep(0.5)  # Rate limiting

            # Fallback: try to extract socials directly from roster page
            if not players:
                logger.info(f"Trying fallback: extract socials from main roster page")
                players = await self._extract_socials_from_roster_page(school)

        except Exception as e:
            logger.error(f"Error scraping {school}: {e}")

        logger.info(f"Found {len(players)} players with social links for {school}")
        return players

    async def _scrape_player_bio(self, bio_url: str, school: str) -> Optional[PlayerSocial]:
        """Scrape social links from a player's bio page."""
        try:
            await self.page.goto(bio_url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(1)

            # Get player name
            name = None
            name_selectors = [
                'h1', 'h2.player-name', '.bio-name', '.s-person-name',
                '[class*="player-name"]', '[class*="athlete-name"]'
            ]
            for sel in name_selectors:
                elem = await self.page.query_selector(sel)
                if elem:
                    name = await elem.text_content()
                    if name:
                        name = name.strip()
                        break

            if not name:
                return None

            # Get position
            position = None
            pos_selectors = ['[class*="position"]', '.bio-position', 'span.position']
            for sel in pos_selectors:
                elem = await self.page.query_selector(sel)
                if elem:
                    position = await elem.text_content()
                    if position:
                        position = position.strip()
                        break

            # Extract social links
            socials = {}
            for platform, selectors in self.SOCIAL_SELECTORS.items():
                for sel in selectors:
                    elem = await self.page.query_selector(sel)
                    if elem:
                        href = await elem.get_attribute("href")
                        if href:
                            socials[f"{platform}_url"] = href
                            socials[f"{platform}_handle"] = self._extract_handle_from_url(href, platform)
                            break

            # Only return if we found at least one social link
            if any(socials.values()):
                return PlayerSocial(
                    name=name,
                    school=school,
                    position=position,
                    profile_url=bio_url,
                    instagram_url=socials.get("instagram_url"),
                    instagram_handle=socials.get("instagram_handle"),
                    twitter_url=socials.get("twitter_url"),
                    twitter_handle=socials.get("twitter_handle"),
                    tiktok_url=socials.get("tiktok_url"),
                    tiktok_handle=socials.get("tiktok_handle"),
                )

        except Exception as e:
            logger.debug(f"Error scraping bio {bio_url}: {e}")

        return None

    async def _extract_socials_from_roster_page(self, school: str) -> List[PlayerSocial]:
        """
        Fallback: extract social links embedded in roster table/grid.
        Some sites show social icons next to each player.
        """
        players = []

        try:
            # Find all rows that might have players
            rows = await self.page.query_selector_all('tr, div[class*="player"], .roster-item')

            for row in rows:
                # Try to get player name
                name_elem = await row.query_selector('a, [class*="name"]')
                if not name_elem:
                    continue

                name = await name_elem.text_content()
                if not name or len(name) < 3:
                    continue

                name = name.strip()

                # Check for social links in this row
                socials = {}
                for platform, selectors in self.SOCIAL_SELECTORS.items():
                    for sel in selectors:
                        elem = await row.query_selector(sel)
                        if elem:
                            href = await elem.get_attribute("href")
                            if href:
                                socials[f"{platform}_url"] = href
                                socials[f"{platform}_handle"] = self._extract_handle_from_url(href, platform)
                                break

                if any(socials.values()):
                    players.append(PlayerSocial(
                        name=name,
                        school=school,
                        instagram_url=socials.get("instagram_url"),
                        instagram_handle=socials.get("instagram_handle"),
                        twitter_url=socials.get("twitter_url"),
                        twitter_handle=socials.get("twitter_handle"),
                        tiktok_url=socials.get("tiktok_url"),
                        tiktok_handle=socials.get("tiktok_handle"),
                    ))

        except Exception as e:
            logger.debug(f"Fallback extraction error: {e}")

        return players

    async def fetch_follower_counts(self, players: List[PlayerSocial]) -> List[PlayerSocial]:
        """
        Fetch actual follower counts for players with social links.
        Note: This requires visiting each profile, so it's slow.

        Args:
            players: List of PlayerSocial with URLs

        Returns:
            Updated list with follower counts
        """
        logger.info(f"Fetching follower counts for {len(players)} players...")

        for i, player in enumerate(players):
            if player.instagram_url:
                followers = await self._get_instagram_followers(player.instagram_url)
                player.instagram_followers = followers

            if player.twitter_url:
                followers = await self._get_twitter_followers(player.twitter_url)
                player.twitter_followers = followers

            if player.tiktok_url:
                followers = await self._get_tiktok_followers(player.tiktok_url)
                player.tiktok_followers = followers

            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(players)}")

            await asyncio.sleep(1)  # Rate limiting

        return players

    async def _get_instagram_followers(self, url: str) -> Optional[int]:
        """Get follower count from Instagram profile."""
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(2)

            # Instagram blocks scraping, but sometimes we can get meta data
            content = await self.page.content()

            # Try to find follower count in page source
            patterns = [
                r'"edge_followed_by":\{"count":(\d+)\}',
                r'"follower_count":(\d+)',
                r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)\s*[Ff]ollowers',
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    count_str = match.group(1).replace(",", "")
                    return self._parse_count(count_str)

        except Exception as e:
            logger.debug(f"Instagram error: {e}")

        return None

    async def _get_twitter_followers(self, url: str) -> Optional[int]:
        """Get follower count from Twitter/X profile."""
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(2)

            # Try to find follower count
            selectors = [
                '[data-testid="primaryColumn"] a[href$="/followers"] span',
                '[class*="followers"] span',
            ]

            for sel in selectors:
                elem = await self.page.query_selector(sel)
                if elem:
                    text = await elem.text_content()
                    if text:
                        return self._parse_count(text)

        except Exception as e:
            logger.debug(f"Twitter error: {e}")

        return None

    async def _get_tiktok_followers(self, url: str) -> Optional[int]:
        """Get follower count from TikTok profile."""
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
            await asyncio.sleep(2)

            # TikTok follower count selector
            elem = await self.page.query_selector('[data-e2e="followers-count"]')
            if elem:
                text = await elem.text_content()
                if text:
                    return self._parse_count(text)

        except Exception as e:
            logger.debug(f"TikTok error: {e}")

        return None

    def _parse_count(self, text: str) -> Optional[int]:
        """Parse follower count from text like '1.2M', '500K', '10,000'."""
        if not text:
            return None

        text = text.strip().replace(",", "").upper()

        try:
            if "B" in text:
                return int(float(text.replace("B", "")) * 1_000_000_000)
            elif "M" in text:
                return int(float(text.replace("M", "")) * 1_000_000)
            elif "K" in text:
                return int(float(text.replace("K", "")) * 1_000)
            else:
                return int(float(text))
        except (ValueError, TypeError):
            return None

    async def scrape_all_teams(self, fetch_followers: bool = False) -> pd.DataFrame:
        """
        Scrape social data for all configured teams.

        Args:
            fetch_followers: Whether to fetch actual follower counts (slow)

        Returns:
            DataFrame with all player social data
        """
        all_players = []

        for i, school in enumerate(SCHOOL_ROSTER_URLS.keys()):
            logger.info(f"[{i+1}/{len(SCHOOL_ROSTER_URLS)}] Scraping {school}...")
            players = await self.scrape_team_roster(school)
            all_players.extend(players)

            # Save progress periodically
            if (i + 1) % 10 == 0:
                self._save_progress(all_players)

        if fetch_followers and all_players:
            all_players = await self.fetch_follower_counts(all_players)

        # Save final results
        df = pd.DataFrame([asdict(p) for p in all_players])
        if not df.empty:
            output_path = self.output_dir / "player_social_links.csv"
            df.to_csv(output_path, index=False)
            logger.info(f"Saved {len(df)} players to {output_path}")

        return df

    def _save_progress(self, players: List[PlayerSocial]):
        """Save intermediate progress."""
        df = pd.DataFrame([asdict(p) for p in players])
        output_path = self.output_dir / "player_social_links_progress.csv"
        df.to_csv(output_path, index=False)

    def load_social_data(self) -> pd.DataFrame:
        """Load previously scraped social data."""
        path = self.output_dir / "player_social_links.csv"
        if path.exists():
            return pd.read_csv(path)
        return pd.DataFrame()


async def main():
    """Test the scraper with a few teams."""
    print("Team Roster Social Media Scraper")
    print("=" * 50)

    async with RosterSocialScraper(headless=True) as scraper:
        # Test with a few teams
        test_teams = ["Colorado", "Ohio State", "Georgia"]

        for team in test_teams:
            print(f"\nScraping {team}...")
            players = await scraper.scrape_team_roster(team)
            print(f"Found {len(players)} players with social links")

            if players:
                print("\nSample players:")
                for p in players[:3]:
                    print(f"  {p.name} ({p.position})")
                    if p.instagram_handle:
                        print(f"    Instagram: @{p.instagram_handle}")
                    if p.twitter_handle:
                        print(f"    Twitter: @{p.twitter_handle}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
