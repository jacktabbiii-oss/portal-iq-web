"""
Custom NIL Valuation Model

A proprietary NIL valuation system based on measurable player attributes:
- On-field performance and production
- Value to team (win impact by position)
- Market factors (school brand, conference, media market)
- Social media reach and engagement
- Recruiting profile and potential

This model creates valuations WITHOUT relying on scraped deal data.
Instead, it builds a bottoms-up estimate of what a player SHOULD be worth.

The model can be calibrated against known deals when available.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class NILValuation:
    """Output of NIL valuation model."""
    player_name: str
    total_valuation: float
    valuation_tier: str  # mega, premium, solid, moderate, entry

    # Component breakdowns
    performance_value: float
    team_value: float
    market_value: float
    social_value: float
    potential_value: float

    # Confidence and explanation
    confidence: str  # high, medium, low
    factors: Dict[str, float]  # Individual factor contributions
    explanation: str


class CustomNILValuator:
    """
    Proprietary NIL valuation based on measurable factors.

    Formula:
    NIL Value = (Performance Score × Position Multiplier × School Multiplier)
                + Social Media Value
                + Potential Premium
                × Market Adjustment

    Each component is calculated from available data.
    """

    # ==========================================================================
    # POSITION VALUE WEIGHTS
    # Based on typical NIL market demand by position
    # ==========================================================================
    POSITION_BASE_VALUES = {
        "QB": 500_000,      # Highest demand, face of program
        "WR": 150_000,      # High visibility, skill position
        "RB": 120_000,      # Skill position, shorter career
        "TE": 100_000,      # Versatile, growing value
        "EDGE": 100_000,    # Premium defensive position
        "CB": 90_000,       # Coverage skills valued
        "S": 80_000,        # Secondary leader
        "LB": 75_000,       # Defensive anchor
        "DL": 70_000,       # Interior presence
        "OL": 60_000,       # Less visibility but critical
        "K": 30_000,        # Specialist
        "P": 25_000,        # Specialist
        "LS": 15_000,       # Specialist
        "ATH": 100_000,     # Versatile, depends on usage
    }

    # ==========================================================================
    # SCHOOL TIER MULTIPLIERS
    # Based on brand value, NIL collective strength, media exposure
    # ==========================================================================
    SCHOOL_MULTIPLIERS = {
        # Tier 5: Blue Bloods (massive NIL operations)
        "Alabama": 3.0, "Ohio State": 3.0, "Georgia": 2.8, "Texas": 3.0,
        "USC": 2.5, "Michigan": 2.5, "Notre Dame": 2.5, "Clemson": 2.3,
        "Oklahoma": 2.3, "LSU": 2.3,

        # Tier 4: Elite programs
        "Penn State": 2.0, "Oregon": 2.2, "Tennessee": 2.0, "Florida": 1.9,
        "Texas A&M": 2.0, "Miami": 1.9, "Auburn": 1.8, "Wisconsin": 1.7,

        # Tier 3: Strong Power 4
        "UCLA": 1.6, "Florida State": 1.6, "Arkansas": 1.5, "Ole Miss": 1.6,
        "South Carolina": 1.5, "Kentucky": 1.4, "NC State": 1.4, "Iowa": 1.4,

        # Tier 2: Mid Power 4
        "Michigan State": 1.3, "Virginia Tech": 1.3, "Louisville": 1.3,
        "Baylor": 1.3, "Kansas State": 1.2, "Pittsburgh": 1.2, "Syracuse": 1.2,

        # Tier 1: G5 and smaller
        "Boise State": 1.0, "Memphis": 0.9, "UCF": 1.0, "SMU": 1.0,
        "Tulane": 0.8, "Liberty": 0.8, "App State": 0.7,
    }
    DEFAULT_SCHOOL_MULTIPLIER = 1.0

    # ==========================================================================
    # CONFERENCE MULTIPLIERS
    # Applied when school not in list
    # ==========================================================================
    CONFERENCE_MULTIPLIERS = {
        "SEC": 1.8,
        "Big Ten": 1.7,
        "Big 12": 1.3,
        "ACC": 1.3,
        "Pac-12": 1.2,  # Legacy
        "American": 0.9,
        "Mountain West": 0.8,
        "Sun Belt": 0.7,
        "MAC": 0.6,
        "Conference USA": 0.6,
        "FCS": 0.4,
    }
    DEFAULT_CONFERENCE_MULTIPLIER = 0.8

    # ==========================================================================
    # SOCIAL MEDIA VALUATION
    # CPM-based calculation for sponsorship value
    # ==========================================================================
    SOCIAL_CPM_RATES = {
        "instagram": 12.0,   # $ per 1000 impressions
        "tiktok": 8.0,
        "twitter": 4.0,
        "youtube": 18.0,
    }
    ENGAGEMENT_RATES = {
        "instagram": 0.03,   # 3% of followers see content
        "tiktok": 0.05,      # Higher engagement
        "twitter": 0.01,
        "youtube": 0.08,
    }
    POSTS_PER_MONTH = {
        "instagram": 8,
        "tiktok": 12,
        "twitter": 15,
        "youtube": 2,
    }

    # ==========================================================================
    # RECRUITING PREMIUM
    # Higher-rated recruits command premium even without production yet
    # ==========================================================================
    STAR_PREMIUMS = {
        5: 200_000,   # 5-star gets $200K floor
        4: 50_000,    # 4-star gets $50K floor
        3: 10_000,    # 3-star gets $10K floor
        2: 5_000,
        1: 0,
        0: 0,
    }

    # ==========================================================================
    # TIER THRESHOLDS
    # ==========================================================================
    TIERS = {
        "mega": 1_000_000,
        "premium": 500_000,
        "solid": 100_000,
        "moderate": 25_000,
        "entry": 0,
    }

    def __init__(self, calibration_factor: float = 1.0):
        """
        Initialize the valuator.

        Args:
            calibration_factor: Multiply all valuations by this factor
                               to calibrate against known market data
        """
        self.calibration_factor = calibration_factor

    def calculate_valuation(
        self,
        player_name: str,
        position: str,
        school: str,
        conference: Optional[str] = None,

        # Performance stats
        games_played: int = 0,
        games_started: int = 0,
        passing_yards: int = 0,
        passing_tds: int = 0,
        rushing_yards: int = 0,
        rushing_tds: int = 0,
        receiving_yards: int = 0,
        receiving_tds: int = 0,
        tackles: int = 0,
        sacks: float = 0,
        interceptions: int = 0,
        pff_grade: Optional[float] = None,

        # Advanced RB stats (NEW)
        elusive_rating: Optional[float] = None,
        breakaway_yards: Optional[int] = None,
        breakaway_percent: Optional[float] = None,
        missed_tackles_forced: Optional[int] = None,

        # DB coverage stats (NEW)
        targets_allowed: Optional[int] = None,
        receptions_allowed: Optional[int] = None,
        qb_rating_against: Optional[float] = None,
        pass_break_ups: Optional[int] = None,

        # Pass rush stats (NEW)
        hits: Optional[int] = None,
        hurries: Optional[int] = None,
        batted_passes: Optional[int] = None,

        # Blocking grades (NEW)
        pass_block_grade: Optional[float] = None,
        run_block_grade: Optional[float] = None,
        pressures_allowed: Optional[int] = None,

        # Social media
        instagram_followers: int = 0,
        twitter_followers: int = 0,
        tiktok_followers: int = 0,
        youtube_subscribers: int = 0,

        # Recruiting
        recruiting_stars: int = 0,
        national_rank: Optional[int] = None,

        # Other factors
        is_starter: bool = False,
        years_remaining: int = 1,
        awards: List[str] = None,
    ) -> NILValuation:
        """
        Calculate NIL valuation for a player.

        Returns detailed breakdown of valuation components.
        """
        factors = {}

        # ==========================================================================
        # 1. BASE POSITION VALUE
        # ==========================================================================
        position_group = self._normalize_position(position)
        base_value = self.POSITION_BASE_VALUES.get(position_group, 50_000)
        factors["position_base"] = base_value

        # ==========================================================================
        # 2. PERFORMANCE MULTIPLIER
        # ==========================================================================
        perf_multiplier = self._calculate_performance_multiplier(
            position_group, games_played, games_started,
            passing_yards, passing_tds, rushing_yards, rushing_tds,
            receiving_yards, receiving_tds, tackles, sacks, interceptions,
            pff_grade,
            # Advanced stats for elite trait detection
            elusive_rating, breakaway_yards, breakaway_percent, missed_tackles_forced,
            targets_allowed, receptions_allowed, qb_rating_against, pass_break_ups,
            hits, hurries, batted_passes,
            pass_block_grade, run_block_grade, pressures_allowed
        )
        performance_value = base_value * perf_multiplier
        factors["performance_multiplier"] = perf_multiplier
        factors["performance_value"] = performance_value

        # ==========================================================================
        # 3. SCHOOL/MARKET MULTIPLIER
        # ==========================================================================
        # Normalize school name to title case for lookup (data is ALL CAPS)
        school_normalized = school.title() if school else "Unknown"
        school_mult = self.SCHOOL_MULTIPLIERS.get(school_normalized, None)
        if school_mult is None:
            school_mult = self.CONFERENCE_MULTIPLIERS.get(
                conference, self.DEFAULT_CONFERENCE_MULTIPLIER
            )
        market_value = performance_value * school_mult
        factors["school_multiplier"] = school_mult
        factors["market_value"] = market_value

        # ==========================================================================
        # 4. SOCIAL MEDIA VALUE
        # ==========================================================================
        social_value = self._calculate_social_value(
            instagram_followers, twitter_followers,
            tiktok_followers, youtube_subscribers
        )
        factors["social_value"] = social_value

        # ==========================================================================
        # 5. POTENTIAL/RECRUITING PREMIUM
        # ==========================================================================
        potential_value = self._calculate_potential_premium(
            recruiting_stars, national_rank, years_remaining
        )
        factors["potential_value"] = potential_value

        # ==========================================================================
        # 6. STARTER BONUS
        # ==========================================================================
        starter_bonus = 1.3 if is_starter else 1.0
        factors["starter_bonus"] = starter_bonus

        # ==========================================================================
        # 7. AWARDS BONUS
        # ==========================================================================
        awards_bonus = self._calculate_awards_bonus(awards or [])
        factors["awards_bonus"] = awards_bonus

        # ==========================================================================
        # FINAL CALCULATION
        # ==========================================================================
        total = (
            (market_value * starter_bonus)
            + social_value
            + potential_value
            + awards_bonus
        ) * self.calibration_factor

        # Ensure minimum based on stars
        star_floor = self.STAR_PREMIUMS.get(recruiting_stars, 0)
        total = max(total, star_floor)

        # Round to nearest $1000
        total = round(total / 1000) * 1000

        # Determine tier
        tier = self._get_tier(total)

        # Determine confidence
        confidence = self._assess_confidence(
            games_played, instagram_followers + twitter_followers + tiktok_followers,
            pff_grade is not None
        )

        # Generate explanation
        explanation = self._generate_explanation(
            player_name, position_group, school, total, factors
        )

        return NILValuation(
            player_name=player_name,
            total_valuation=total,
            valuation_tier=tier,
            performance_value=performance_value,
            team_value=market_value,
            market_value=market_value,
            social_value=social_value,
            potential_value=potential_value,
            confidence=confidence,
            factors=factors,
            explanation=explanation,
        )

    def _normalize_position(self, position: str) -> str:
        """Map position to standard group."""
        position = position.upper().strip()
        mappings = {
            "QUARTERBACK": "QB", "RUNNINGBACK": "RB", "HB": "RB", "FB": "RB",
            "RECEIVER": "WR", "WIDE RECEIVER": "WR", "SE": "WR", "FL": "WR",
            "TIGHT END": "TE",
            "OFFENSIVE LINE": "OL", "OT": "OL", "OG": "OL", "C": "OL", "T": "OL", "G": "OL",
            "DEFENSIVE LINE": "DL", "DT": "DL", "DE": "DL", "NT": "DL",
            "OUTSIDE LINEBACKER": "EDGE", "OLB": "EDGE", "RUSH": "EDGE",
            "LINEBACKER": "LB", "ILB": "LB", "MLB": "LB",
            "CORNERBACK": "CB", "DB": "CB",
            "SAFETY": "S", "FS": "S", "SS": "S",
            "KICKER": "K", "PK": "K",
            "PUNTER": "P",
            "LONG SNAPPER": "LS",
            "ATHLETE": "ATH",
        }
        return mappings.get(position, position if position in self.POSITION_BASE_VALUES else "ATH")

    def _calculate_performance_multiplier(
        self, position: str, games: int, starts: int,
        pass_yds: int, pass_tds: int, rush_yds: int, rush_tds: int,
        rec_yds: int, rec_tds: int, tackles: int, sacks: float, ints: int,
        pff_grade: Optional[float],
        # Advanced stats for elite trait detection
        elusive_rating: Optional[float] = None,
        breakaway_yards: Optional[int] = None,
        breakaway_percent: Optional[float] = None,
        missed_tackles_forced: Optional[int] = None,
        targets_allowed: Optional[int] = None,
        receptions_allowed: Optional[int] = None,
        qb_rating_against: Optional[float] = None,
        pass_break_ups: Optional[int] = None,
        hits: Optional[int] = None,
        hurries: Optional[int] = None,
        batted_passes: Optional[int] = None,
        pass_block_grade: Optional[float] = None,
        run_block_grade: Optional[float] = None,
        pressures_allowed: Optional[int] = None,
    ) -> float:
        """
        Calculate performance multiplier based on PRODUCTION FIRST + ELITE TRAITS.

        Philosophy: Stats are king. PFF grade is a modifier, not the foundation.
        A backup with 25 snaps and a 90 grade is NOT worth more than a
        productive starter with 800 snaps and a 75 grade.

        NEW: Elite trait bonuses reward difference-makers beyond basic production.
        """
        if games == 0:
            return 0.3  # Minimal multiplier for no games

        mult = 1.0
        has_production = False

        # =============================================================================
        # STEP 1: PRODUCTION-BASED MULTIPLIER (Primary Factor)
        # =============================================================================
        if position == "QB":
            # QBs: yards, TDs, efficiency
            if pass_yds > 3000:
                mult += 1.2
                has_production = True
            elif pass_yds > 2000:
                mult += 0.8
                has_production = True
            elif pass_yds > 1000:
                mult += 0.4
                has_production = True

            if pass_tds > 25:
                mult += 0.6
                has_production = True
            elif pass_tds > 15:
                mult += 0.4
                has_production = True
            elif pass_tds > 10:
                mult += 0.2
                has_production = True

            # Dual threat bonus
            if rush_yds > 500:
                mult += 0.4
                has_production = True

        elif position in ["RB"]:
            if rush_yds > 1000:
                mult += 0.9
                has_production = True
            elif rush_yds > 500:
                mult += 0.5
                has_production = True
            elif rush_yds > 250:
                mult += 0.2
                has_production = True

            if rush_tds > 10:
                mult += 0.5
                has_production = True
            elif rush_tds > 5:
                mult += 0.3
                has_production = True

            # Receiving bonus
            if rec_yds > 300:
                mult += 0.3
                has_production = True

        elif position == "WR":
            if rec_yds > 1000:
                mult += 1.0
                has_production = True
            elif rec_yds > 600:
                mult += 0.6
                has_production = True
            elif rec_yds > 300:
                mult += 0.3
                has_production = True

            if rec_tds > 10:
                mult += 0.5
                has_production = True
            elif rec_tds > 5:
                mult += 0.3
                has_production = True

        elif position == "TE":
            if rec_yds > 600:
                mult += 0.7
                has_production = True
            elif rec_yds > 300:
                mult += 0.4
                has_production = True

            if rec_tds > 5:
                mult += 0.4
                has_production = True

        elif position in ["EDGE", "DL"]:
            if sacks > 10:
                mult += 0.9
                has_production = True
            elif sacks > 5:
                mult += 0.5
                has_production = True
            elif sacks > 2:
                mult += 0.3
                has_production = True

        elif position == "LB":
            if tackles > 100:
                mult += 0.7
                has_production = True
            elif tackles > 70:
                mult += 0.4
                has_production = True
            elif tackles > 40:
                mult += 0.2
                has_production = True

            if sacks > 3:
                mult += 0.3
                has_production = True

        elif position in ["CB", "S"]:
            if ints > 5:
                mult += 0.8
                has_production = True
            elif ints > 2:
                mult += 0.4
                has_production = True

            if tackles > 50:
                mult += 0.3
                has_production = True

        elif position == "OL":
            # O-line rarely get production stats, rely on grades
            if pass_block_grade or run_block_grade:
                has_production = True  # Grades count as production for OL

        # =============================================================================
        # STEP 1.5: ELITE TRAIT BONUSES (NEW - Comprehensive PFF Stats)
        # Reward difference-makers beyond basic production
        # =============================================================================

        # RB ELITE TRAITS: Elusiveness + Explosiveness
        if position == "RB":
            if elusive_rating is not None:
                if elusive_rating > 100:
                    mult += 0.5  # Elite contact balance (top 10%)
                    has_production = True
                elif elusive_rating > 75:
                    mult += 0.3  # Above average elusiveness
                    has_production = True
                elif elusive_rating > 50:
                    mult += 0.15  # Solid elusiveness

            if breakaway_percent is not None:
                if breakaway_percent > 30:
                    mult += 0.4  # Explosive home-run threat
                    has_production = True
                elif breakaway_percent > 20:
                    mult += 0.2  # Good explosiveness

            if missed_tackles_forced is not None and games > 0:
                mtf_per_game = missed_tackles_forced / games
                if mtf_per_game > 3:
                    mult += 0.3  # Consistently breaks tackles
                    has_production = True
                elif mtf_per_game > 2:
                    mult += 0.15

        # DB ELITE TRAITS: Shutdown Coverage
        elif position in ["CB", "S"]:
            if qb_rating_against is not None:
                if qb_rating_against < 50:
                    mult += 0.6  # True shutdown corner/safety (elite)
                    has_production = True
                elif qb_rating_against < 70:
                    mult += 0.4  # Excellent coverage
                    has_production = True
                elif qb_rating_against < 90:
                    mult += 0.2  # Good coverage

            if targets_allowed and receptions_allowed and targets_allowed > 0:
                completion_pct = (receptions_allowed / targets_allowed) * 100
                if completion_pct < 50:
                    mult += 0.4  # Lockdown coverage
                    has_production = True
                elif completion_pct < 60:
                    mult += 0.2  # Strong coverage

            if pass_break_ups is not None:
                if pass_break_ups > 8:
                    mult += 0.3  # Ball hawk
                    has_production = True
                elif pass_break_ups > 5:
                    mult += 0.15

        # EDGE/DL ELITE TRAITS: Pass Rush Dominance
        elif position in ["EDGE", "DL"]:
            total_disruptions = 0
            if hits is not None:
                total_disruptions += hits
            if hurries is not None:
                total_disruptions += hurries

            if total_disruptions > 0:
                if total_disruptions > 50:
                    mult += 0.7  # Pass rush terror (elite)
                    has_production = True
                elif total_disruptions > 35:
                    mult += 0.5  # Consistent pressure
                    has_production = True
                elif total_disruptions > 20:
                    mult += 0.3  # Good pass rusher

            if batted_passes is not None:
                if batted_passes > 5:
                    mult += 0.2  # Length and awareness
                    has_production = True

        # O-LINE ELITE TRAITS: Protection Mastery
        elif position == "OL":
            if pass_block_grade is not None:
                if pass_block_grade > 85:
                    mult += 0.6  # Elite pass protector
                    has_production = True
                elif pass_block_grade > 75:
                    mult += 0.4  # Excellent pass protection
                    has_production = True
                elif pass_block_grade > 65:
                    mult += 0.2  # Good pass protection

            if run_block_grade is not None:
                if run_block_grade > 80:
                    mult += 0.5  # Elite run blocker
                    has_production = True
                elif run_block_grade > 70:
                    mult += 0.3  # Excellent run blocking
                    has_production = True
                elif run_block_grade > 60:
                    mult += 0.15  # Good run blocking

            if pressures_allowed is not None and games > 0:
                pressures_per_game = pressures_allowed / games
                if pressures_per_game < 0.5:
                    mult += 0.4  # Clean sheets (elite)
                    has_production = True
                elif pressures_per_game < 1.0:
                    mult += 0.2  # Good protection

        # =============================================================================
        # STEP 2: GAMES PLAYED SCALING (Guardrail for volume)
        # =============================================================================
        games_scale = min(games / 10.0, 1.2)  # Scale up to 1.2x for 10+ games
        if games < 6:
            games_scale *= 0.6  # Heavy penalty for < 6 games
        elif games < 8:
            games_scale *= 0.8  # Moderate penalty for < 8 games

        mult *= games_scale

        # =============================================================================
        # STEP 3: PFF GRADE MODIFIER (Secondary - Only Matters with Production)
        # =============================================================================
        if pff_grade and has_production:
            # PFF grade only helps if you actually produced
            # Scale bonus based on games played
            pff_bonus = 0.0
            if pff_grade > 90:
                pff_bonus = 0.3
            elif pff_grade > 80:
                pff_bonus = 0.2
            elif pff_grade > 70:
                pff_bonus = 0.1

            # Scale PFF bonus by games (no bonus for < 6 games)
            if games >= 10:
                mult += pff_bonus
            elif games >= 8:
                mult += pff_bonus * 0.7
            elif games >= 6:
                mult += pff_bonus * 0.4
            # else: no PFF bonus for < 6 games

        elif pff_grade and not has_production:
            # High grade but no production? Small bonus only
            if pff_grade > 85 and games >= 8:
                mult += 0.1  # Minimal bonus for potential

        # =============================================================================
        # STEP 4: STARTER BONUS
        # =============================================================================
        start_rate = starts / max(games, 1)
        if start_rate > 0.8:
            mult += 0.2

        return max(mult, 0.3)  # Minimum multiplier

    def _calculate_social_value(
        self, ig: int, tw: int, tt: int, yt: int
    ) -> float:
        """Calculate annual social media sponsorship value."""
        total = 0.0

        # Instagram value
        if ig > 0:
            impressions = ig * self.ENGAGEMENT_RATES["instagram"] * self.POSTS_PER_MONTH["instagram"] * 12
            total += impressions * self.SOCIAL_CPM_RATES["instagram"] / 1000

        # TikTok value
        if tt > 0:
            impressions = tt * self.ENGAGEMENT_RATES["tiktok"] * self.POSTS_PER_MONTH["tiktok"] * 12
            total += impressions * self.SOCIAL_CPM_RATES["tiktok"] / 1000

        # Twitter value
        if tw > 0:
            impressions = tw * self.ENGAGEMENT_RATES["twitter"] * self.POSTS_PER_MONTH["twitter"] * 12
            total += impressions * self.SOCIAL_CPM_RATES["twitter"] / 1000

        # YouTube value
        if yt > 0:
            impressions = yt * self.ENGAGEMENT_RATES["youtube"] * self.POSTS_PER_MONTH["youtube"] * 12
            total += impressions * self.SOCIAL_CPM_RATES["youtube"] / 1000

        return total

    def _calculate_potential_premium(
        self, stars: int, national_rank: Optional[int], years_remaining: int
    ) -> float:
        """Calculate premium for recruiting profile and remaining eligibility."""
        premium = self.STAR_PREMIUMS.get(stars, 0)

        # Top recruit bonus
        if national_rank and national_rank <= 10:
            premium += 100_000
        elif national_rank and national_rank <= 50:
            premium += 50_000
        elif national_rank and national_rank <= 100:
            premium += 25_000

        # Years remaining multiplier (more years = more total value)
        year_mult = 1.0 + (years_remaining - 1) * 0.1  # +10% per extra year
        premium *= year_mult

        return premium

    def _calculate_awards_bonus(self, awards: List[str]) -> float:
        """Calculate bonus for awards and accolades."""
        bonus = 0

        award_values = {
            "heisman": 500_000,
            "heisman finalist": 200_000,
            "all-american": 150_000,
            "first-team all-conference": 75_000,
            "conference player of year": 100_000,
            "freshman all-american": 50_000,
            "all-conference": 40_000,
        }

        for award in awards:
            award_lower = award.lower()
            for key, value in award_values.items():
                if key in award_lower:
                    bonus += value
                    break

        return bonus

    def _get_tier(self, value: float) -> str:
        """Get valuation tier."""
        for tier, threshold in self.TIERS.items():
            if value >= threshold:
                return tier
        return "entry"

    def _assess_confidence(
        self, games: int, total_followers: int, has_pff: bool
    ) -> str:
        """Assess confidence in valuation."""
        score = 0
        if games >= 10: score += 2
        elif games >= 5: score += 1
        if total_followers > 50000: score += 1
        if has_pff: score += 1

        if score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        return "low"

    def _generate_explanation(
        self, name: str, position: str, school: str,
        total: float, factors: Dict
    ) -> str:
        """Generate human-readable explanation."""
        parts = [
            f"{name} ({position}, {school})",
            f"Valuation: ${total:,.0f}",
            f"",
            f"Breakdown:",
            f"  Base position value: ${factors.get('position_base', 0):,.0f}",
            f"  Performance multiplier: {factors.get('performance_multiplier', 1):.2f}x",
            f"  School/market multiplier: {factors.get('school_multiplier', 1):.2f}x",
            f"  Social media value: ${factors.get('social_value', 0):,.0f}",
            f"  Potential premium: ${factors.get('potential_value', 0):,.0f}",
        ]
        return "\n".join(parts)

    def valuate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Valuate all players in a DataFrame.

        Expected columns: player_name, position, school, and various stats.
        Returns DataFrame with valuation columns added.
        """
        def safe_int(val, default=0):
            """Convert value to int, handling NaN."""
            if pd.isna(val) or val is None:
                return default
            try:
                return int(val)
            except (ValueError, TypeError):
                return default

        def safe_float(val, default=0.0):
            """Convert value to float, handling NaN."""
            if pd.isna(val) or val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        valuations = []

        for _, row in df.iterrows():
            # Map CSV column names to parameter names
            # CSV has: pff_overall, pff_offense, pff_defense, rec_yards, yards, touchdowns
            # Function expects: pff_grade, position-specific yards/TDs

            position = row.get("position", "ATH")

            # Use position-specific PFF grade when available
            pff_grade_val = None
            if position in ["QB"]:
                pff_grade_val = row.get("pff_passing") or row.get("pff_offense") or row.get("pff_overall")
            elif position in ["RB", "HB", "FB"]:
                pff_grade_val = row.get("pff_rushing") or row.get("pff_offense") or row.get("pff_overall")
            elif position in ["WR", "TE"]:
                pff_grade_val = row.get("pff_receiving") or row.get("pff_offense") or row.get("pff_overall")
            elif position in ["OL", "OT", "OG", "C", "T", "G"]:
                pff_grade_val = row.get("pff_pass_block") or row.get("pff_run_block") or row.get("pff_offense") or row.get("pff_overall")
            elif position in ["ED", "DL", "DT", "DE", "NT"]:
                pff_grade_val = row.get("pff_pass_rush") or row.get("pff_defense") or row.get("pff_overall")
            elif position in ["LB", "OLB", "ILB", "MLB"]:
                pff_grade_val = row.get("pff_run_defense") or row.get("pff_tackling") or row.get("pff_defense") or row.get("pff_overall")
            elif position in ["CB", "S", "FS", "SS", "DB"]:
                pff_grade_val = row.get("pff_coverage") or row.get("pff_defense") or row.get("pff_overall")
            else:
                pff_grade_val = row.get("pff_overall")

            if pd.notna(pff_grade_val):
                pff_grade_val = float(pff_grade_val)
            else:
                pff_grade_val = None

            # Infer position-specific stats from generic columns
            # "yards" and "touchdowns" are position-dependent
            yards_val = safe_int(row.get("yards"))
            tds_val = safe_int(row.get("touchdowns"))

            # For QB: yards = passing yards, TDs = passing TDs
            passing_yards_val = yards_val if position == "QB" else 0
            passing_tds_val = tds_val if position == "QB" else 0

            # For RB: yards = rushing yards, TDs = rushing TDs
            rushing_yards_val = yards_val if position in ["RB", "HB", "FB"] else 0
            rushing_tds_val = tds_val if position in ["RB", "HB", "FB"] else 0

            # For WR/TE: use rec_yards explicitly, TDs = receiving TDs
            receiving_yards_val = safe_int(row.get("rec_yards"))
            receiving_tds_val = tds_val if position in ["WR", "TE"] else 0

            val = self.calculate_valuation(
                player_name=row.get("player_name", row.get("name", "Unknown")),
                position=position,
                school=row.get("school", "Unknown"),
                conference=row.get("conference"),
                games_played=safe_int(row.get("games_played")),
                games_started=safe_int(row.get("games_started")),
                passing_yards=passing_yards_val,
                passing_tds=passing_tds_val,
                rushing_yards=rushing_yards_val,
                rushing_tds=rushing_tds_val,
                receiving_yards=receiving_yards_val,
                receiving_tds=receiving_tds_val,
                tackles=safe_int(row.get("tackles")),
                sacks=safe_float(row.get("sacks")),
                interceptions=safe_int(row.get("interceptions")),
                pff_grade=pff_grade_val,
                # Advanced RB stats (comprehensive PFF)
                elusive_rating=safe_float(row.get("elusive_rating")) if pd.notna(row.get("elusive_rating")) else None,
                breakaway_yards=safe_int(row.get("breakaway_yards")) if pd.notna(row.get("breakaway_yards")) else None,
                breakaway_percent=safe_float(row.get("breakaway_percent")) if pd.notna(row.get("breakaway_percent")) else None,
                missed_tackles_forced=safe_int(row.get("missed_tackles_forced")) if pd.notna(row.get("missed_tackles_forced")) else None,
                # DB coverage stats (comprehensive PFF)
                targets_allowed=safe_int(row.get("targets_coverage")) if pd.notna(row.get("targets_coverage")) else None,
                receptions_allowed=safe_int(row.get("receptions_coverage")) if pd.notna(row.get("receptions_coverage")) else None,
                qb_rating_against=safe_float(row.get("qb_rating_against")) if pd.notna(row.get("qb_rating_against")) else None,
                pass_break_ups=safe_int(row.get("pass_break_ups")) if pd.notna(row.get("pass_break_ups")) else None,
                # Pass rush stats (comprehensive PFF)
                hits=safe_int(row.get("hits")) if pd.notna(row.get("hits")) else None,
                hurries=safe_int(row.get("hurries")) if pd.notna(row.get("hurries")) else None,
                batted_passes=safe_int(row.get("batted_passes")) if pd.notna(row.get("batted_passes")) else None,
                # Blocking grades (comprehensive PFF)
                pass_block_grade=safe_float(row.get("grades_pass_block")) if pd.notna(row.get("grades_pass_block")) else None,
                run_block_grade=safe_float(row.get("grades_run_block")) if pd.notna(row.get("grades_run_block")) else None,
                pressures_allowed=safe_int(row.get("pressures_allowed")) if pd.notna(row.get("pressures_allowed")) else None,
                instagram_followers=0,  # Not available in CSV
                twitter_followers=0,
                tiktok_followers=0,
                youtube_subscribers=0,
                recruiting_stars=safe_int(row.get("stars")),
                national_rank=None,  # Not available in CSV
                is_starter=False,  # Not available in CSV
                years_remaining=1,
            )
            valuations.append({
                "custom_nil_value": val.total_valuation,
                "nil_tier": val.valuation_tier,
                "performance_value": val.performance_value,
                "market_value": val.market_value,
                "social_value": val.social_value,
                "potential_value": val.potential_value,
                "valuation_confidence": val.confidence,
            })

        val_df = pd.DataFrame(valuations)
        return pd.concat([df.reset_index(drop=True), val_df], axis=1)


# Example usage
if __name__ == "__main__":
    valuator = CustomNILValuator()

    # Example: Travis Hunter
    result = valuator.calculate_valuation(
        player_name="Travis Hunter",
        position="CB",
        school="Colorado",
        conference="Big 12",
        games_played=12,
        games_started=12,
        interceptions=4,
        tackles=55,
        receiving_yards=1150,
        receiving_tds=14,
        pff_grade=92.5,
        instagram_followers=2_500_000,
        twitter_followers=500_000,
        tiktok_followers=1_000_000,
        recruiting_stars=5,
        national_rank=1,
        is_starter=True,
        years_remaining=1,
        awards=["Heisman", "First-Team All-American"],
    )

    print(result.explanation)
    print(f"\nTotal: ${result.total_valuation:,.0f}")
    print(f"Tier: {result.valuation_tier}")
    print(f"Confidence: {result.confidence}")
