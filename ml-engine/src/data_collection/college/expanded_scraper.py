"""
Expanded Data Collection for Portal IQ

Comprehensive scraping from multiple sources to build the most complete
college football player database possible.

Data Sources:
1. On3 - NIL valuations, recruiting, transfer portal, player profiles
2. 247Sports - Composite rankings, team talent scores
3. ESPN - Rosters, headshots, basic stats
4. Sports-Reference - Historical college/NFL stats
5. NFL Combine - Official measurables

Usage:
    from src.data_collection.college.expanded_scraper import ExpandedScraper

    async with ExpandedScraper() as scraper:
        # Scrape all On3 NIL data (not just top 100)
        nil_data = await scraper.scrape_on3_full_nil()

        # Scrape player profiles for detailed data
        profiles = await scraper.scrape_on3_player_profiles(player_urls)

        # Scrape 247Sports composite rankings
        rankings = await scraper.scrape_247_composite()
"""

import asyncio
import logging
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict, field

import pandas as pd

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes for Different Sources
# =============================================================================

@dataclass
class On3PlayerProfile:
    """Detailed On3 player profile data."""
    name: str
    school: str
    position: str
    # NIL Data
    nil_valuation: float = 0
    nil_rank: Optional[int] = None
    nil_deals_count: Optional[int] = None
    # Social Media
    instagram_handle: Optional[str] = None
    instagram_followers: Optional[int] = None
    twitter_handle: Optional[str] = None
    twitter_followers: Optional[int] = None
    tiktok_handle: Optional[str] = None
    tiktok_followers: Optional[int] = None
    total_followers: Optional[int] = None
    # Recruiting
    recruiting_stars: Optional[int] = None
    recruiting_rank_national: Optional[int] = None
    recruiting_rank_position: Optional[int] = None
    recruiting_rank_state: Optional[int] = None
    composite_rating: Optional[float] = None
    class_year: Optional[str] = None
    # Physical
    height: Optional[str] = None
    weight: Optional[int] = None
    hometown: Optional[str] = None
    high_school: Optional[str] = None
    # Stats (from On3 player page)
    games_played: Optional[int] = None
    stats_summary: Optional[Dict] = None
    # Meta
    profile_url: Optional[str] = None
    headshot_url: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Composite247Player:
    """247Sports composite ranking data."""
    name: str
    school: Optional[str] = None
    position: str = "ATH"
    # Rankings
    composite_rating: Optional[float] = None
    composite_stars: Optional[int] = None
    national_rank: Optional[int] = None
    position_rank: Optional[int] = None
    state_rank: Optional[int] = None
    # Ratings from different services
    on3_rating: Optional[float] = None
    rivals_rating: Optional[float] = None
    espn_rating: Optional[float] = None
    rating_247: Optional[float] = None
    # Physical
    height: Optional[str] = None
    weight: Optional[int] = None
    hometown: Optional[str] = None
    state: Optional[str] = None
    # Class
    class_year: Optional[int] = None
    # Meta
    profile_url: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class NILDeal:
    """Individual NIL deal data."""
    player_name: str
    school: str
    company: str
    deal_type: Optional[str] = None  # endorsement, autograph, appearance, etc.
    estimated_value: Optional[float] = None
    announced_date: Optional[str] = None
    source_url: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# On3 Data URLs
# =============================================================================

ON3_URLS = {
    # NIL Rankings (paginated - much more than 100 players)
    "nil_all": "https://www.on3.com/nil/rankings/player/all/football/",
    "nil_by_position": "https://www.on3.com/nil/rankings/player/all/football/{position}/",
    "nil_by_school": "https://www.on3.com/nil/rankings/player/team/{school_slug}/",

    # Transfer Portal
    "portal_all": "https://www.on3.com/db/transfer-portal/football/",
    "portal_by_position": "https://www.on3.com/db/transfer-portal/football/{position}/",

    # Recruiting Rankings
    "recruiting_class": "https://www.on3.com/db/rankings/player/all/{year}/football/",
    "team_recruiting": "https://www.on3.com/db/rankings/team/all/{year}/football/",

    # Team Pages
    "team_roster": "https://www.on3.com/teams/{school_slug}/football/roster/",
    "team_nil": "https://www.on3.com/nil/teams/{school_slug}/football/",

    # Player Profile
    "player_profile": "https://www.on3.com/db/{player_slug}/",
}

# 247Sports URLs
SPORTS247_URLS = {
    "composite_rankings": "https://247sports.com/Season/{year}-Football/CompositeRecruitRankings/",
    "transfer_portal": "https://247sports.com/Season/{year}-Football/TransferPortal/",
    "team_talent": "https://247sports.com/Season/{year}-Football/CollegeTeamTalentComposite/",
    "player_profile": "https://247sports.com/Player/{player_slug}/",
}


class ExpandedScraper:
    """
    Comprehensive scraper for multiple data sources.

    Focuses on getting as much data as possible from:
    - On3 (primary source for NIL)
    - 247Sports (composite rankings)
    - ESPN (rosters)
    """

    def __init__(self, data_dir: Optional[str] = None, headless: bool = True):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright required. Run: pip install playwright && playwright install chromium")

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
        self.raw_dir = self.data_dir / "raw" / "expanded"
        self.processed_dir = self.data_dir / "processed"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

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

        # Block ads/analytics
        await self.page.route("**/analytics**", lambda route: route.abort())
        await self.page.route("**/ads**", lambda route: route.abort())

        logger.info("Expanded scraper browser started")

    async def _close_browser(self):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser closed")

    # =========================================================================
    # On3 Full NIL Rankings (All Players, Not Just Top 100)
    # =========================================================================

    async def scrape_on3_full_nil(self, max_pages: int = 50) -> List[On3PlayerProfile]:
        """
        Scrape ALL On3 NIL rankings, not just the top 100.

        On3 has NIL valuations for thousands of players. This method
        paginates through all available pages.

        Args:
            max_pages: Maximum pages to scrape (50 players per page)

        Returns:
            List of On3PlayerProfile objects
        """
        logger.info(f"Scraping On3 full NIL rankings (up to {max_pages} pages)...")
        all_players = []

        for page_num in range(1, max_pages + 1):
            url = ON3_URLS["nil_all"]
            if page_num > 1:
                url += f"?page={page_num}"

            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                # Extract from __NEXT_DATA__ JSON
                content = await self.page.content()
                json_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', content, re.DOTALL)

                if not json_match:
                    logger.warning(f"No data found on page {page_num}")
                    break

                data = json.loads(json_match.group(1))
                nil_list = data.get('props', {}).get('pageProps', {}).get('nilRankings', {}).get('list', [])

                if not nil_list:
                    logger.info(f"No more players found at page {page_num}")
                    break

                for item in nil_list:
                    player = self._parse_on3_player(item)
                    if player:
                        all_players.append(player)

                logger.info(f"Page {page_num}: {len(nil_list)} players (total: {len(all_players)})")

                await asyncio.sleep(1)  # Rate limiting

            except Exception as e:
                logger.error(f"Error on page {page_num}: {e}")
                break

        # Save results
        if all_players:
            self._save_on3_players(all_players)

        return all_players

    def _parse_on3_player(self, item: Dict) -> Optional[On3PlayerProfile]:
        """Parse On3 player data from JSON."""
        try:
            person = item.get('person', {})
            valuation_data = item.get('valuation', {})

            name = person.get('name', 'Unknown')
            if not name or name == 'Unknown':
                return None

            # School
            school = 'Unknown'
            commit_status = person.get('commitStatus', {})
            if isinstance(commit_status, dict):
                org = commit_status.get('committedOrganization', {})
                if isinstance(org, dict):
                    school = org.get('name', 'Unknown')
                    # Clean school name
                    if school and ' ' in school:
                        parts = school.rsplit(' ', 1)
                        if len(parts) == 2 and parts[1].endswith('s'):
                            school = parts[0]

            # Position
            position = person.get('positionAbbreviation', 'ATH')
            if not position or position == 'Unknown':
                rating = person.get('rating', {})
                if isinstance(rating, dict):
                    position = rating.get('positionAbbr', 'ATH')

            # NIL data
            nil_value = valuation_data.get('valuation', 0) or 0
            nil_rank = valuation_data.get('rank')
            followers = valuation_data.get('followers', 0) or 0

            # Recruiting data
            rating_data = person.get('rating', {}) or {}
            stars = rating_data.get('stars')
            composite = rating_data.get('rating')
            nat_rank = rating_data.get('rankNational')
            pos_rank = rating_data.get('rankPosition')
            state_rank = rating_data.get('rankState')

            # Class year
            class_year = None
            if isinstance(commit_status, dict):
                class_year = commit_status.get('classRank')

            # Physical
            height = person.get('height')
            weight = person.get('weight')
            hometown = person.get('hometown', {})
            if isinstance(hometown, dict):
                hometown = f"{hometown.get('city', '')}, {hometown.get('state', '')}".strip(', ')
            else:
                hometown = None

            # Headshot
            headshot = person.get('defaultAssetUrl', '')

            return On3PlayerProfile(
                name=name,
                school=school,
                position=position,
                nil_valuation=nil_value,
                nil_rank=nil_rank,
                total_followers=followers,
                recruiting_stars=stars,
                composite_rating=composite,
                recruiting_rank_national=nat_rank,
                recruiting_rank_position=pos_rank,
                recruiting_rank_state=state_rank,
                class_year=class_year,
                height=height,
                weight=weight,
                hometown=hometown,
                headshot_url=headshot,
                profile_url=f"https://www.on3.com/db/{person.get('slug', '')}/",
            )

        except Exception as e:
            logger.debug(f"Error parsing player: {e}")
            return None

    def _save_on3_players(self, players: List[On3PlayerProfile]):
        """Save On3 players to CSV."""
        df = pd.DataFrame([asdict(p) for p in players])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Timestamped version
        path = self.raw_dir / f"on3_full_nil_{timestamp}.csv"
        df.to_csv(path, index=False)

        # Latest version
        latest = self.raw_dir / "on3_full_nil_latest.csv"
        df.to_csv(latest, index=False)

        # Processed version for API
        processed = self.processed_dir / "on3_all_nil_rankings.csv"
        df.to_csv(processed, index=False)

        logger.info(f"Saved {len(players)} On3 players to {path}")

    # =========================================================================
    # On3 Player Profiles (Detailed Data)
    # =========================================================================

    async def scrape_on3_player_profiles(
        self,
        player_urls: List[str],
        include_stats: bool = True,
    ) -> List[On3PlayerProfile]:
        """
        Scrape detailed player profiles from On3.

        This gets MORE data than the rankings pages:
        - Social media handles (not just counts)
        - High school info
        - Detailed stats
        - NIL deals

        Args:
            player_urls: List of On3 player profile URLs
            include_stats: Whether to scrape stats (slower)

        Returns:
            List of detailed On3PlayerProfile objects
        """
        logger.info(f"Scraping {len(player_urls)} On3 player profiles...")
        profiles = []

        for i, url in enumerate(player_urls):
            try:
                profile = await self._scrape_single_profile(url, include_stats)
                if profile:
                    profiles.append(profile)

                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{len(player_urls)}")

                await asyncio.sleep(1)  # Rate limiting

            except Exception as e:
                logger.warning(f"Error scraping {url}: {e}")

        return profiles

    async def _scrape_single_profile(
        self,
        url: str,
        include_stats: bool = True,
    ) -> Optional[On3PlayerProfile]:
        """Scrape a single On3 player profile page."""
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(1)

            content = await self.page.content()

            # Try to extract from __NEXT_DATA__
            json_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', content, re.DOTALL)

            if json_match:
                data = json.loads(json_match.group(1))
                person_data = data.get('props', {}).get('pageProps', {}).get('person', {})

                if person_data:
                    # Extract social media handles
                    social = person_data.get('social', {}) or {}
                    ig_handle = social.get('instagram')
                    tw_handle = social.get('twitter')
                    tt_handle = social.get('tiktok')

                    # Get follower counts from valuation
                    valuation = person_data.get('nilValuation', {}) or {}

                    # High school
                    hs = person_data.get('highSchool', {}) or {}
                    high_school = hs.get('name')

                    # Stats
                    stats_summary = None
                    if include_stats:
                        stats_data = person_data.get('stats', {}) or {}
                        if stats_data:
                            stats_summary = stats_data

                    return On3PlayerProfile(
                        name=person_data.get('name', 'Unknown'),
                        school=self._extract_school_from_profile(person_data),
                        position=person_data.get('positionAbbreviation', 'ATH'),
                        nil_valuation=valuation.get('valuation', 0) or 0,
                        nil_rank=valuation.get('rank'),
                        instagram_handle=ig_handle,
                        instagram_followers=valuation.get('instagramFollowers'),
                        twitter_handle=tw_handle,
                        twitter_followers=valuation.get('twitterFollowers'),
                        tiktok_handle=tt_handle,
                        tiktok_followers=valuation.get('tiktokFollowers'),
                        total_followers=valuation.get('followers', 0) or 0,
                        recruiting_stars=person_data.get('rating', {}).get('stars'),
                        recruiting_rank_national=person_data.get('rating', {}).get('rankNational'),
                        composite_rating=person_data.get('rating', {}).get('rating'),
                        height=person_data.get('height'),
                        weight=person_data.get('weight'),
                        hometown=self._extract_hometown(person_data),
                        high_school=high_school,
                        headshot_url=person_data.get('defaultAssetUrl'),
                        stats_summary=stats_summary,
                        profile_url=url,
                    )

        except Exception as e:
            logger.debug(f"Profile scrape error: {e}")

        return None

    def _extract_school_from_profile(self, person_data: Dict) -> str:
        """Extract school name from profile data."""
        commit = person_data.get('commitStatus', {}) or {}
        org = commit.get('committedOrganization', {}) or {}
        school = org.get('name', 'Unknown')

        # Clean up
        if school and ' ' in school:
            parts = school.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].endswith('s'):
                school = parts[0]

        return school

    def _extract_hometown(self, person_data: Dict) -> Optional[str]:
        """Extract hometown string."""
        ht = person_data.get('hometown', {})
        if isinstance(ht, dict):
            city = ht.get('city', '')
            state = ht.get('state', '')
            if city or state:
                return f"{city}, {state}".strip(', ')
        return None

    # =========================================================================
    # 247Sports Composite Rankings
    # =========================================================================

    async def scrape_247_composite(
        self,
        year: int = 2025,
        max_pages: int = 20,
    ) -> List[Composite247Player]:
        """
        Scrape 247Sports composite rankings.

        The composite is the industry-standard recruiting ranking that
        averages On3, Rivals, ESPN, and 247's own rankings.

        Args:
            year: Recruiting class year
            max_pages: Maximum pages to scrape

        Returns:
            List of Composite247Player objects
        """
        logger.info(f"Scraping 247Sports {year} composite rankings...")
        all_players = []

        for page_num in range(1, max_pages + 1):
            url = SPORTS247_URLS["composite_rankings"].format(year=year)
            if page_num > 1:
                url += f"?Page={page_num}"

            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                # Extract player rows
                rows = await self.page.query_selector_all('.rankings-page__list-item, .ri-page__list-item')

                if not rows:
                    logger.info(f"No more players at page {page_num}")
                    break

                for row in rows:
                    player = await self._parse_247_row(row, year)
                    if player:
                        all_players.append(player)

                logger.info(f"Page {page_num}: {len(rows)} players (total: {len(all_players)})")
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"247 page {page_num} error: {e}")
                break

        # Save
        if all_players:
            df = pd.DataFrame([asdict(p) for p in all_players])
            path = self.processed_dir / f"247_composite_{year}.csv"
            df.to_csv(path, index=False)
            logger.info(f"Saved {len(all_players)} players to {path}")

        return all_players

    async def _parse_247_row(self, row, year: int) -> Optional[Composite247Player]:
        """Parse a 247Sports ranking row."""
        try:
            # Name
            name_el = await row.query_selector('.ri-page__name-link, .rankings-page__name-link')
            name = await name_el.text_content() if name_el else None

            if not name:
                return None

            # Position
            pos_el = await row.query_selector('.position, .ri-page__position')
            position = await pos_el.text_content() if pos_el else "ATH"

            # Rating
            rating_el = await row.query_selector('.score, .ri-page__score')
            rating_text = await rating_el.text_content() if rating_el else None
            rating = float(rating_text) if rating_text else None

            # Stars
            stars_el = await row.query_selector('.ri-page__star-rating-wrapper')
            stars = 0
            if stars_el:
                filled = await stars_el.query_selector_all('.yellow, .gold, [class*="active"]')
                stars = len(filled) if filled else 3

            # Rankings
            rank_el = await row.query_selector('.rank-column, .ri-page__rank')
            nat_rank = None
            if rank_el:
                rank_text = await rank_el.text_content()
                if rank_text:
                    nat_rank = int(re.sub(r'\D', '', rank_text))

            # Profile URL
            link = await row.query_selector('a[href*="/Player/"]')
            profile_url = await link.get_attribute("href") if link else None
            if profile_url and not profile_url.startswith("http"):
                profile_url = f"https://247sports.com{profile_url}"

            return Composite247Player(
                name=name.strip(),
                position=position.strip() if position else "ATH",
                composite_rating=rating,
                composite_stars=stars,
                national_rank=nat_rank,
                class_year=year,
                profile_url=profile_url,
            )

        except Exception as e:
            logger.debug(f"247 row parse error: {e}")
            return None

    # =========================================================================
    # Team Talent Composite (School Rankings)
    # =========================================================================

    async def scrape_247_team_talent(self, year: int = 2025) -> pd.DataFrame:
        """
        Scrape 247Sports team talent composite.

        This ranks teams by total roster talent, useful for school tier calculations.

        Args:
            year: Season year

        Returns:
            DataFrame with team talent rankings
        """
        logger.info(f"Scraping 247Sports {year} team talent composite...")

        url = SPORTS247_URLS["team_talent"].format(year=year)
        teams = []

        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            rows = await self.page.query_selector_all('.rankings-page__list-item, tr.team-row')

            for row in rows:
                try:
                    # Team name
                    name_el = await row.query_selector('.team-name, a[href*="/college/"]')
                    name = await name_el.text_content() if name_el else None

                    if not name:
                        continue

                    # Rank
                    rank_el = await row.query_selector('.rank-column, td:first-child')
                    rank_text = await rank_el.text_content() if rank_el else None
                    rank = int(re.sub(r'\D', '', rank_text)) if rank_text else None

                    # Score
                    score_el = await row.query_selector('.score, .talent-score')
                    score_text = await score_el.text_content() if score_el else None
                    score = float(score_text.replace(',', '')) if score_text else None

                    # 5-stars, 4-stars, etc.
                    star_counts = {}
                    for stars in range(5, 1, -1):
                        star_el = await row.query_selector(f'.star-{stars}, [data-stars="{stars}"]')
                        if star_el:
                            count_text = await star_el.text_content()
                            star_counts[f"star_{stars}"] = int(count_text) if count_text else 0

                    teams.append({
                        "school": name.strip(),
                        "rank": rank,
                        "talent_score": score,
                        **star_counts,
                        "year": year,
                    })

                except Exception as e:
                    logger.debug(f"Team row error: {e}")

            logger.info(f"Scraped {len(teams)} teams")

        except Exception as e:
            logger.error(f"Team talent scrape error: {e}")

        df = pd.DataFrame(teams)
        if not df.empty:
            path = self.processed_dir / f"247_team_talent_{year}.csv"
            df.to_csv(path, index=False)

        return df

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    async def scrape_all_sources(self) -> Dict[str, int]:
        """
        Run comprehensive data collection from all sources.

        Returns:
            Dict with counts of scraped records per source
        """
        results = {}

        # On3 Full NIL
        logger.info("=== Scraping On3 Full NIL ===")
        on3_players = await self.scrape_on3_full_nil(max_pages=50)
        results["on3_nil"] = len(on3_players)

        # Get profile URLs for top players
        top_urls = [p.profile_url for p in on3_players[:500] if p.profile_url]

        # On3 Detailed Profiles (top 500)
        logger.info("=== Scraping On3 Player Profiles ===")
        profiles = await self.scrape_on3_player_profiles(top_urls[:100])  # Start with top 100
        results["on3_profiles"] = len(profiles)

        # 247 Composite Rankings
        logger.info("=== Scraping 247 Composite ===")
        for year in [2025, 2024, 2023]:
            composite = await self.scrape_247_composite(year=year, max_pages=10)
            results[f"247_composite_{year}"] = len(composite)

        # Team Talent
        logger.info("=== Scraping Team Talent ===")
        team_talent = await self.scrape_247_team_talent(year=2025)
        results["team_talent"] = len(team_talent)

        logger.info("=== Scraping Complete ===")
        for source, count in results.items():
            logger.info(f"  {source}: {count} records")

        return results


async def main():
    """Test the expanded scraper."""
    print("Portal IQ Expanded Data Scraper")
    print("=" * 50)

    async with ExpandedScraper(headless=True) as scraper:
        # Test On3 full NIL (first 5 pages)
        print("\nScraping On3 full NIL rankings (5 pages)...")
        players = await scraper.scrape_on3_full_nil(max_pages=5)
        print(f"Found {len(players)} players")

        if players:
            print("\nTop 10 by NIL value:")
            sorted_players = sorted(players, key=lambda p: p.nil_valuation, reverse=True)[:10]
            for i, p in enumerate(sorted_players, 1):
                print(f"  {i}. {p.name} ({p.school}) - ${p.nil_valuation:,.0f}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
