"""
On3 NIL News Scraper

Scrapes NIL news articles for AI analysis and deal tracking.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# NIL News Pages
ON3_NEWS_PAGES = {
    "nil_main": "https://www.on3.com/nil/",
    "nil_deals_news": "https://www.on3.com/nil/category/college-nil-deals/news/",
    "nil_deals": "https://www.on3.com/nil/deals/",
    "sports_business": "https://www.on3.com/nil/category/sports-business/news/",
    "transfer_portal_news": "https://www.on3.com/transfer-portal/news/",
}


class On3NewsScraper:
    """Scrapes On3 news articles."""

    def __init__(self):
        self.cookies_path = project_root / "data" / "cache" / "on3_cookies.json"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })
        self._load_cookies()

    def _load_cookies(self):
        if self.cookies_path.exists():
            with open(self.cookies_path, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                self.session.cookies.set(
                    cookie.get('name', ''),
                    cookie.get('value', ''),
                    domain=cookie.get('domain', '.on3.com'),
                )
            print(f"Loaded {len(cookies)} cookies")

    def fetch_page(self, url: str) -> dict:
        """Fetch page and extract __NEXT_DATA__ JSON."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', response.text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception as e:
            print(f"  Error: {e}")
        return {}

    def extract_articles(self, data: dict, source: str) -> list:
        """Extract news articles from page data."""
        articles = []
        props = data.get('props', {}).get('pageProps', {})

        # On3 uses articles.list structure
        articles_data = props.get('articles', {})
        if isinstance(articles_data, dict):
            article_list = articles_data.get('list', [])
        elif isinstance(articles_data, list):
            article_list = articles_data
        else:
            article_list = []

        # Also try other paths
        if not article_list:
            article_list = (
                props.get('news', {}).get('list', []) or
                props.get('stories', {}).get('list', []) or
                props.get('feed', {}).get('list', []) or
                []
            )

        for item in article_list:
            try:
                if isinstance(item, dict):
                    # Get author name
                    author = item.get('author', {})
                    author_name = author.get('name', '') if isinstance(author, dict) else str(author)

                    # Build full URL
                    url = item.get('fullUrl', '') or item.get('url', '') or item.get('slug', '')
                    if url and not url.startswith('http'):
                        url = f"https://www.on3.com{url}"

                    article = {
                        'title': item.get('title') or item.get('headline') or '',
                        'summary': item.get('body', '')[:500] if item.get('body') else item.get('excerpt', ''),
                        'url': url,
                        'date': item.get('postDate') or item.get('publishedAt') or item.get('date') or '',
                        'author': author_name,
                        'is_premium': item.get('isPremium', False),
                        'source': source,
                        'type': 'article',
                    }
                    if article['title']:
                        articles.append(article)
            except Exception:
                continue

        # Also check for deals
        deals = props.get('deals', {}).get('list', []) or props.get('nilDeals', []) or []
        for deal in deals:
            try:
                if isinstance(deal, dict):
                    person = deal.get('person', {}) or {}
                    org = deal.get('organization', {}) or {}

                    article = {
                        'title': f"NIL Deal: {person.get('name', 'Unknown')}",
                        'summary': deal.get('description') or deal.get('details') or f"Deal with {org.get('name', 'Unknown')}",
                        'url': f"https://www.on3.com/db/{person.get('slug', '')}/",
                        'date': deal.get('date') or deal.get('announcedAt') or '',
                        'author': '',
                        'is_premium': False,
                        'player_name': person.get('name', ''),
                        'deal_value': deal.get('value') or deal.get('amount'),
                        'brand': org.get('name', ''),
                        'source': source,
                        'type': 'deal',
                    }
                    if article['title'] != 'NIL Deal: Unknown':
                        articles.append(article)
            except Exception:
                continue

        return articles

    def scrape_all_news(self) -> pd.DataFrame:
        """Scrape all news pages."""
        all_articles = []

        print("=" * 70)
        print("ON3 NIL NEWS SCRAPER")
        print("=" * 70)

        for name, url in ON3_NEWS_PAGES.items():
            print(f"\n[{name}] {url}")

            data = self.fetch_page(url)
            if not data:
                print("  Failed to fetch")
                continue

            articles = self.extract_articles(data, source=name)
            print(f"  Found {len(articles)} items")

            all_articles.extend(articles)
            time.sleep(1)

        df = pd.DataFrame(all_articles)
        if not df.empty:
            df = df.drop_duplicates(subset=['title'], keep='first')

        return df


def main():
    scraper = On3NewsScraper()
    df = scraper.scrape_all_news()

    print(f"\n{'=' * 70}")
    print(f"TOTAL: {len(df)} news items scraped")
    print("=" * 70)

    if not df.empty:
        # Summary
        print("\nItems by source:")
        for src in df['source'].unique():
            count = len(df[df['source'] == src])
            print(f"  {src}: {count}")

        print("\nItems by type:")
        for t in df['type'].unique():
            count = len(df[df['type'] == t])
            print(f"  {t}: {count}")

        # Show recent articles
        print("\nRecent Articles/Deals:")
        print("-" * 70)
        for _, row in df.head(15).iterrows():
            title = row['title'][:60] if len(row['title']) > 60 else row['title']
            print(f"  [{row['type']}] {title}")

        # Save
        output_path = project_root / "data" / "processed" / "on3_nil_news.csv"
        df.to_csv(output_path, index=False)
        print(f"\nSaved to {output_path}")

        # Also save as JSON for easier AI processing
        json_path = project_root / "data" / "processed" / "on3_nil_news.json"
        df.to_json(json_path, orient='records', indent=2)
        print(f"Saved JSON to {json_path}")


if __name__ == "__main__":
    main()
