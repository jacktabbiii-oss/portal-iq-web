"""
Data Collection Module for Portal IQ

This module handles data collection from various sources including:
- CFB stats and game data
- NIL valuations and deals
- Recruiting rankings
- Transfer portal entries
- Social media metrics
- NFL draft history
"""

from .cfb_stats import CFBStatsCollector
from .cfb_nil import NILDataCollector
from .cfb_recruiting import RecruitingDataCollector
from .cfb_portal import PortalDataCollector
from .social_media import SocialMediaCollector
from .draft_history import DraftHistoryCollector

__all__ = [
    "CFBStatsCollector",
    "NILDataCollector",
    "RecruitingDataCollector",
    "PortalDataCollector",
    "SocialMediaCollector",
    "DraftHistoryCollector",
]
