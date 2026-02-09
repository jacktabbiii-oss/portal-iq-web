"""
Social Media Data Collector

Collects social media metrics and engagement data for players.

Data Sources (in priority order):
1. On3 NIL data (has aggregate follower counts)
2. Scraped roster social links (player_social_links.csv)
3. Manual lookup via platform APIs (future)
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import requests

try:
    from ..utils.config import Config
except ImportError:
    Config = None

logger = logging.getLogger(__name__)


class SocialMediaCollector:
    """Collects social media metrics for NIL valuation."""

    def __init__(self, config: Optional["Config"] = None, data_dir: Optional[str] = None):
        """
        Initialize the social media collector.

        Args:
            config: Configuration object with API keys and settings
            data_dir: Path to data directory with cached social data
        """
        self.config = config or (Config() if Config else None)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Portal-IQ/1.0 (Research)"
        })

        # Find data directory
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            current = Path(__file__).parent
            while current.parent != current:
                if (current / "data").exists():
                    self.data_dir = current / "data"
                    break
                current = current.parent
            else:
                self.data_dir = Path("data")

        # Cache loaded data
        self._on3_data = None
        self._social_links = None

    def _load_on3_data(self) -> pd.DataFrame:
        """Load On3 data which includes follower counts."""
        if self._on3_data is not None:
            return self._on3_data

        paths = [
            self.data_dir / "raw" / "on3" / "nil_100_latest.csv",
            self.data_dir / "processed" / "on3_all_nil_rankings.csv",
            self.data_dir / "processed" / "nil_performance_merged.csv",
        ]

        for path in paths:
            if path.exists():
                try:
                    self._on3_data = pd.read_csv(path)
                    logger.info(f"Loaded On3 data from {path}: {len(self._on3_data)} players")
                    return self._on3_data
                except Exception as e:
                    logger.warning(f"Failed to load {path}: {e}")

        self._on3_data = pd.DataFrame()
        return self._on3_data

    def _load_social_links(self) -> pd.DataFrame:
        """Load scraped social links from roster pages."""
        if self._social_links is not None:
            return self._social_links

        path = self.data_dir / "processed" / "player_social_links.csv"
        if path.exists():
            try:
                self._social_links = pd.read_csv(path)
                logger.info(f"Loaded social links: {len(self._social_links)} players")
                return self._social_links
            except Exception as e:
                logger.warning(f"Failed to load social links: {e}")

        self._social_links = pd.DataFrame()
        return self._social_links

    def _lookup_player_in_on3(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Look up player social data from On3."""
        df = self._load_on3_data()
        if df.empty:
            return None

        # Try exact match first
        name_col = "name" if "name" in df.columns else "player_name"
        if name_col not in df.columns:
            return None

        match = df[df[name_col].str.lower() == player_name.lower()]
        if match.empty:
            # Try partial match
            match = df[df[name_col].str.contains(player_name, case=False, na=False)]

        if match.empty:
            return None

        row = match.iloc[0]

        # Extract follower counts
        return {
            "instagram_followers": int(row.get("instagram_followers", 0) or 0),
            "twitter_followers": int(row.get("twitter_followers", 0) or 0),
            "tiktok_followers": int(row.get("tiktok_followers", 0) or 0),
            "total_followers": int(row.get("followers", 0) or 0),
        }

    def _lookup_player_in_social_links(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Look up player from scraped social links."""
        df = self._load_social_links()
        if df.empty:
            return None

        match = df[df["name"].str.lower() == player_name.lower()]
        if match.empty:
            match = df[df["name"].str.contains(player_name, case=False, na=False)]

        if match.empty:
            return None

        row = match.iloc[0]

        return {
            "instagram_url": row.get("instagram_url"),
            "instagram_handle": row.get("instagram_handle"),
            "instagram_followers": int(row.get("instagram_followers", 0) or 0),
            "twitter_url": row.get("twitter_url"),
            "twitter_handle": row.get("twitter_handle"),
            "twitter_followers": int(row.get("twitter_followers", 0) or 0),
            "tiktok_url": row.get("tiktok_url"),
            "tiktok_handle": row.get("tiktok_handle"),
            "tiktok_followers": int(row.get("tiktok_followers", 0) or 0),
        }

    def get_player_social_metrics(
        self,
        player_name: str,
        platforms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get social media metrics for a player.

        Checks cached data sources first:
        1. On3 NIL data (aggregate followers)
        2. Scraped roster social links
        3. Falls back to placeholder if no data found

        Args:
            player_name: Player name
            platforms: List of platforms to check (default: all)

        Returns:
            Dictionary with social media metrics
        """
        if platforms is None:
            platforms = ["twitter", "instagram", "tiktok"]

        metrics = {
            "player_name": player_name,
            "total_followers": 0,
            "platforms": {},
            "engagement_rate": 0.0,
            "data_source": "none",
            "last_updated": datetime.now().isoformat(),
        }

        # Try On3 data first (has aggregate follower counts)
        on3_data = self._lookup_player_in_on3(player_name)
        if on3_data and on3_data.get("total_followers", 0) > 0:
            metrics["total_followers"] = on3_data["total_followers"]
            metrics["data_source"] = "on3"
            metrics["platforms"] = {
                "instagram": {"followers": on3_data.get("instagram_followers", 0)},
                "twitter": {"followers": on3_data.get("twitter_followers", 0)},
                "tiktok": {"followers": on3_data.get("tiktok_followers", 0)},
            }
            return metrics

        # Try scraped social links
        social_data = self._lookup_player_in_social_links(player_name)
        if social_data:
            total = 0
            for platform in platforms:
                key = f"{platform}_followers"
                followers = social_data.get(key, 0)
                total += followers
                metrics["platforms"][platform] = {
                    "followers": followers,
                    "handle": social_data.get(f"{platform}_handle"),
                    "url": social_data.get(f"{platform}_url"),
                }
            metrics["total_followers"] = total
            if total > 0:
                metrics["data_source"] = "scraped"
                return metrics

        # Fall back to platform lookups
        for platform in platforms:
            platform_data = self._get_platform_metrics(player_name, platform)
            metrics["platforms"][platform] = platform_data
            metrics["total_followers"] += platform_data.get("followers", 0)

        # Calculate average engagement rate
        engagement_rates = [
            p.get("engagement_rate", 0)
            for p in metrics["platforms"].values()
            if p.get("engagement_rate", 0) > 0
        ]
        if engagement_rates:
            metrics["engagement_rate"] = sum(engagement_rates) / len(engagement_rates)

        return metrics

    def _get_platform_metrics(
        self,
        player_name: str,
        platform: str,
    ) -> Dict[str, Any]:
        """
        Get metrics for a specific platform.

        Currently a placeholder - could be extended to use APIs:
        - Instagram: Requires Facebook Graph API
        - Twitter/X: Requires Twitter API v2
        - TikTok: Requires TikTok Display API

        Args:
            player_name: Player name
            platform: Platform name

        Returns:
            Dictionary with platform metrics
        """
        # TODO: Implement actual API calls when keys are available
        return {
            "followers": 0,
            "following": 0,
            "posts": 0,
            "engagement_rate": 0.0,
            "verified": False,
        }

    def estimate_social_value(
        self,
        followers: int,
        engagement_rate: float = 2.0,
        verified: bool = False,
        position: Optional[str] = None,
    ) -> float:
        """
        Estimate NIL value component from social media presence.

        Based on industry data:
        - Top CFB players (5M+ followers) command $500K-1M+ in social-driven NIL
        - Mid-tier (500K-2M) typically $100K-$300K social value
        - Rising stars (50K-500K) typically $10K-$100K
        - Most players (<50K) have minimal social-driven NIL

        Args:
            followers: Total follower count
            engagement_rate: Average engagement rate (default 2.0%)
            verified: Whether account is verified
            position: Player position (QBs have higher social value)

        Returns:
            Estimated social media value contribution
        """
        if followers <= 0:
            return 0.0

        # Tiered value per follower (more followers = lower marginal value)
        if followers >= 5_000_000:
            # Elite tier (Travis Hunter, Arch Manning level)
            base_value = 600_000 + (followers - 5_000_000) * 0.02
        elif followers >= 1_000_000:
            # Star tier
            base_value = 200_000 + (followers - 1_000_000) * 0.10
        elif followers >= 500_000:
            # Rising star tier
            base_value = 75_000 + (followers - 500_000) * 0.25
        elif followers >= 100_000:
            # Emerging tier
            base_value = 15_000 + (followers - 100_000) * 0.15
        elif followers >= 50_000:
            # Notable tier
            base_value = 5_000 + (followers - 50_000) * 0.20
        elif followers >= 10_000:
            # Base tier
            base_value = 500 + (followers - 10_000) * 0.11
        else:
            # Minimal tier
            base_value = followers * 0.05

        # Engagement multiplier (higher engagement = more valuable)
        if engagement_rate > 5.0:
            engagement_mult = 1.5
        elif engagement_rate > 3.0:
            engagement_mult = 1.25
        elif engagement_rate > 1.5:
            engagement_mult = 1.1
        elif engagement_rate < 0.5:
            engagement_mult = 0.7  # Low engagement penalty
        else:
            engagement_mult = 1.0

        # Verification bonus (verified accounts more credible for sponsors)
        verification_mult = 1.2 if verified else 1.0

        # Position bonus (QBs have more marketable social presence)
        position_mult = 1.0
        if position:
            position = position.upper()
            if position == "QB":
                position_mult = 1.3
            elif position in ["WR", "RB"]:
                position_mult = 1.1

        value = base_value * engagement_mult * verification_mult * position_mult

        # Cap at reasonable maximum
        return min(value, 1_500_000)

    def get_social_value_for_player(self, player_name: str, position: Optional[str] = None) -> float:
        """
        Get estimated social media NIL value for a player.

        Convenience method that combines lookup and valuation.

        Args:
            player_name: Player name
            position: Player position (optional, for position bonus)

        Returns:
            Estimated social media value
        """
        metrics = self.get_player_social_metrics(player_name)
        return self.estimate_social_value(
            followers=metrics.get("total_followers", 0),
            engagement_rate=metrics.get("engagement_rate", 2.0),
            position=position,
        )

    def enrich_players_with_social(self, players_df: pd.DataFrame) -> pd.DataFrame:
        """
        Bulk enrich a player DataFrame with social media data.

        Args:
            players_df: DataFrame with 'name' or 'player_name' column

        Returns:
            DataFrame with added social columns
        """
        result = players_df.copy()

        # Find name column
        name_col = None
        for col in ["name", "player_name", "Name"]:
            if col in result.columns:
                name_col = col
                break

        if not name_col:
            logger.warning("No name column found in DataFrame")
            return result

        # Find position column
        pos_col = None
        for col in ["position", "pos", "Position"]:
            if col in result.columns:
                pos_col = col
                break

        # Add social columns
        result["social_followers"] = 0
        result["social_value"] = 0.0
        result["social_data_source"] = "none"

        for idx, row in result.iterrows():
            player_name = row[name_col]
            position = row[pos_col] if pos_col else None

            metrics = self.get_player_social_metrics(player_name)
            result.at[idx, "social_followers"] = metrics.get("total_followers", 0)
            result.at[idx, "social_data_source"] = metrics.get("data_source", "none")
            result.at[idx, "social_value"] = self.estimate_social_value(
                followers=metrics.get("total_followers", 0),
                engagement_rate=metrics.get("engagement_rate", 2.0),
                position=position,
            )

        return result

    def get_trending_players(
        self,
        limit: int = 20,
    ) -> pd.DataFrame:
        """
        Get currently trending college football players on social media.

        Args:
            limit: Number of players to return

        Returns:
            DataFrame with trending players
        """
        columns = [
            "player_name",
            "school",
            "position",
            "platform",
            "trend_score",
            "mentions",
            "sentiment",
        ]
        return pd.DataFrame(columns=columns)

    def analyze_sentiment(
        self,
        player_name: str,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Analyze social media sentiment around a player.

        Args:
            player_name: Player name
            days: Number of days to analyze

        Returns:
            Dictionary with sentiment analysis
        """
        return {
            "player_name": player_name,
            "period_days": days,
            "overall_sentiment": 0.0,
            "positive_ratio": 0.0,
            "negative_ratio": 0.0,
            "neutral_ratio": 0.0,
            "total_mentions": 0,
        }
