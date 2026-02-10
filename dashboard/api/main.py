"""Portal IQ API - Main FastAPI Application.

Provides REST endpoints for integrating Portal IQ data with external
applications like playmakervc.com.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd

# Import Portal IQ utilities
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.data_loader import (
    get_nil_players,
    get_portal_players,
    get_team_rankings,
    search_players,
    get_pff_grades,
    get_database_stats,
)
from utils.player_comparison import PlayerComparison, get_player_comps_for_card
from utils.validation import sanitize_player_name, sanitize_search_query
from utils.logging_config import get_logger, log_api_call

logger = get_logger("portal_iq.api")


# =============================================================================
# Pydantic Models
# =============================================================================

class PlayerBase(BaseModel):
    """Base player information."""
    name: str
    position: Optional[str] = None
    team: Optional[str] = None


class PlayerProfile(PlayerBase):
    """Full player profile with NIL and performance data."""
    nil_value: Optional[float] = None
    portaliq_value: Optional[float] = None
    stars: Optional[float] = None
    pff_overall: Optional[float] = None
    school: Optional[str] = None
    headshot_url: Optional[str] = None
    height_display: Optional[str] = None
    weight: Optional[float] = None


class PlayerNIL(BaseModel):
    """NIL valuation data."""
    name: str
    nil_value: Optional[float] = None
    portaliq_value: Optional[float] = None
    on3_nil_value: Optional[float] = None
    confidence: Optional[str] = None
    is_predicted: bool = True
    value_low: Optional[float] = None
    value_high: Optional[float] = None


class PlayerComparison(BaseModel):
    """Player comparison result."""
    name: str
    team: Optional[str] = None
    similarity: float
    pff_overall: Optional[float] = None


class PortalPlayer(PlayerBase):
    """Transfer portal player data."""
    origin_school: Optional[str] = None
    destination_school: Optional[str] = None
    status: Optional[str] = None
    portal_year: Optional[int] = None
    nil_value: Optional[float] = None
    stars: Optional[float] = None


class SearchResult(BaseModel):
    """Search result with source."""
    name: str
    position: Optional[str] = None
    team: Optional[str] = None
    nil_value: Optional[float] = None
    data_source: str


class WatchlistItem(BaseModel):
    """Watchlist item."""
    player_name: str
    notes: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.utcnow)


class APIStats(BaseModel):
    """API/database statistics."""
    total_players: int
    portal_players: int
    nil_valuations: int
    schools: int
    last_updated: str


# =============================================================================
# Authentication
# =============================================================================

# API Key validation
API_KEYS = set(os.getenv("PORTAL_IQ_API_KEYS", "").split(","))
POCKETBASE_JWT_SECRET = os.getenv("POCKETBASE_JWT_SECRET", "")


async def verify_api_key(x_api_key: str = Header(None)) -> str:
    """Verify API key from header.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        Valid API key

    Raises:
        HTTPException: If API key is invalid
    """
    # Allow requests without API key in development
    if os.getenv("PORTAL_IQ_ENV", "development") == "development":
        return "dev-mode"

    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return x_api_key


async def verify_jwt_token(authorization: str = Header(None)) -> Optional[Dict]:
    """Verify JWT token from Authorization header.

    Supports tokens from playmakervc.com or other integrated apps.

    Args:
        authorization: Bearer token from Authorization header

    Returns:
        Decoded token payload or None

    Raises:
        HTTPException: If token is invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    if not POCKETBASE_JWT_SECRET:
        # JWT validation disabled
        return {"sub": "anonymous"}

    try:
        import jwt
        payload = jwt.decode(token, POCKETBASE_JWT_SECRET, algorithms=["HS256"])
        return payload
    except Exception as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# =============================================================================
# FastAPI App
# =============================================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Portal IQ API",
        description="REST API for Portal IQ - Transfer Portal & NIL Intelligence",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )

    # CORS for playmakervc.com and other integrations
    allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
    if not allowed_origins or allowed_origins == [""]:
        allowed_origins = [
            "https://playmakervc.com",
            "https://www.playmakervc.com",
            "http://localhost:3000",
            "http://localhost:8501",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    return app


app = create_app()


# =============================================================================
# Health & Stats Endpoints
# =============================================================================

@app.get("/api/v1/health")
async def health_check():
    """Check API health status."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/v1/stats", response_model=APIStats)
async def get_stats(api_key: str = Depends(verify_api_key)):
    """Get database statistics."""
    stats = get_database_stats()
    return APIStats(
        total_players=stats.get("total_players", 0),
        portal_players=stats.get("portal_players", 0),
        nil_valuations=stats.get("nil_valuations", 0),
        schools=stats.get("schools", 0),
        last_updated=stats.get("last_updated", "Unknown")
    )


# =============================================================================
# Player Endpoints
# =============================================================================

@app.get("/api/v1/players/search", response_model=List[SearchResult])
async def search_players_endpoint(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    """Search for players by name.

    Args:
        q: Search query (minimum 2 characters)
        limit: Maximum results to return

    Returns:
        List of matching players
    """
    start = datetime.utcnow()

    query = sanitize_search_query(q)
    results = search_players(query)

    if results.empty:
        log_api_call("/players/search", "GET", 200, 0)
        return []

    results = results.head(limit)

    response = []
    for _, row in results.iterrows():
        response.append(SearchResult(
            name=row.get("name", ""),
            position=row.get("position"),
            team=row.get("team") or row.get("school"),
            nil_value=row.get("nil_value"),
            data_source=row.get("data_source", "unknown")
        ))

    duration = (datetime.utcnow() - start).total_seconds() * 1000
    log_api_call("/players/search", "GET", 200, duration)

    return response


@app.get("/api/v1/players/{player_name}/profile")
async def get_player_profile(
    player_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Get comprehensive player profile matching UnifiedPlayer interface.

    Args:
        player_name: Player name (URL encoded)

    Returns:
        Comprehensive player data including NIL, PFF grades/stats, portal status, career data
    """
    name = sanitize_player_name(player_name)

    # Try NIL data first (most comprehensive)
    nil_df = get_nil_players()
    if not nil_df.empty:
        match = nil_df[nil_df["name"].str.lower() == name.lower()]
        if not match.empty:
            player = match.iloc[0]

            # Build comprehensive PFF object
            pff_data = {
                # All PFF grades
                "pff_overall": safe_float(player.get("pff_overall")),
                "pff_offense": safe_float(player.get("pff_offense")),
                "pff_defense": safe_float(player.get("pff_defense")),
                "pff_passing": safe_float(player.get("pff_passing")),
                "pff_rushing": safe_float(player.get("pff_rushing")),
                "pff_receiving": safe_float(player.get("pff_receiving")),
                "pff_pass_block": safe_float(player.get("pff_pass_block") or player.get("grades_pass_block")),
                "pff_run_block": safe_float(player.get("pff_run_block") or player.get("grades_run_block")),
                "pff_pass_rush": safe_float(player.get("pff_pass_rush")),
                "pff_coverage": safe_float(player.get("pff_coverage")),
                "pff_run_defense": safe_float(player.get("pff_run_defense")),
                "pff_tackling": safe_float(player.get("pff_tackling")),

                # Volume
                "games_played": safe_int(player.get("games_played")),

                # QB stats
                "completion_pct": safe_float(player.get("completion_pct")),
                "passer_rating": safe_float(player.get("passer_rating")),
                "big_time_throw_pct": safe_float(player.get("big_time_throw_pct")),
                "turnover_worthy_play_pct": safe_float(player.get("turnover_worthy_play_pct")),
                "avg_depth_of_target": safe_float(player.get("avg_depth_of_target")),

                # RB stats
                "elusive_rating": safe_float(player.get("elusive_rating")),
                "yaco_per_attempt": safe_float(player.get("yaco_per_attempt")),
                "breakaway_pct": safe_float(player.get("breakaway_pct") or player.get("breakaway_percent")),
                "missed_tackles_forced": safe_int(player.get("missed_tackles_forced")),
                "breakaway_yards": safe_int(player.get("breakaway_yards")),

                # WR/TE stats
                "yards_per_route_run": safe_float(player.get("yards_per_route_run")),
                "drop_rate": safe_float(player.get("drop_rate")),
                "contested_catch_rate": safe_float(player.get("contested_catch_rate")),
                "targeted_qb_rating": safe_float(player.get("targeted_qb_rating")),
                "targets": safe_int(player.get("targets")),
                "receptions": safe_int(player.get("receptions")),
                "rec_yards": safe_int(player.get("receiving_yards")),

                # Pass rush stats (Edge/DL)
                "pass_rush_win_rate": safe_float(player.get("pass_rush_win_rate")),
                "pass_rushing_productivity": safe_float(player.get("pass_rushing_productivity")),
                "pressures": safe_int(player.get("pressures")),
                "hits": safe_int(player.get("hits")),
                "hurries": safe_int(player.get("hurries")),
                "batted_passes": safe_int(player.get("batted_passes")),
                "sacks": safe_int(player.get("sacks")),

                # Coverage stats (DB)
                "targets_coverage": safe_int(player.get("targets_coverage")),
                "receptions_coverage": safe_int(player.get("receptions_coverage")),
                "interceptions_coverage": safe_int(player.get("interceptions_coverage")),
                "pass_break_ups": safe_int(player.get("pass_break_ups")),
                "forced_incompletion_rate": safe_float(player.get("forced_incompletion_rate")),
                "passer_rating_allowed": safe_float(player.get("qb_rating_against")),
                "yards_per_coverage_snap": safe_float(player.get("yards_per_coverage_snap")),
                "man_grades_coverage_defense": safe_float(player.get("man_grades_coverage_defense")),
                "zone_grades_coverage_defense": safe_float(player.get("zone_grades_coverage_defense")),

                # Blocking stats
                "pass_blocking_efficiency": safe_float(player.get("pass_blocking_efficiency")),
                "pressures_allowed": safe_int(player.get("pressures_allowed")),

                # Defense stats
                "tackles": safe_int(player.get("tackles")),
                "assists": safe_int(player.get("assists")),
                "interceptions": safe_int(player.get("interceptions")),
                "missed_tackle_rate": safe_float(player.get("missed_tackle_rate")),

                # Special teams - Kicking
                "total_made": safe_int(player.get("total_made")),
                "pat_made": safe_int(player.get("pat_made")),
                "twenty_made": safe_int(player.get("twenty_made")),
                "thirty_made": safe_int(player.get("thirty_made")),
                "forty_made": safe_int(player.get("forty_made")),
                "fifty_made": safe_int(player.get("fifty_made")),
                "touchbacks": safe_int(player.get("touchbacks")),

                # Special teams - Punting
                "attempts_punt": safe_int(player.get("attempts_punt")),
                "punt_avg_yards": safe_float(player.get("average_yards_per_attempt")),
                "punt_net_avg": safe_float(player.get("average_net_yards")),
                "inside_twenties": safe_int(player.get("inside_twenties")),
                "average_hangtime": safe_float(player.get("average_hangtime")),

                # Special teams - Returns
                "kickoff_attempts": safe_int(player.get("kickoff_attempts")),
                "kickoff_yards": safe_int(player.get("kickoff_yards")),
                "kickoff_touchdowns": safe_int(player.get("kickoff_touchdowns")),
                "punt_attempts": safe_int(player.get("punt_attempts")),
                "punt_yards": safe_int(player.get("punt_yards")),
                "punt_touchdowns": safe_int(player.get("punt_touchdowns")),

                # Production stats (generic)
                "yards": safe_int(player.get("yards")),
                "touchdowns": safe_int(player.get("touchdowns")),
            }

            # Remove None values
            pff_data = {k: v for k, v in pff_data.items() if v is not None}

            return {
                # Core identity
                "name": player.get("name", name),
                "position": player.get("position"),
                "school": player.get("school") or player.get("team"),
                "headshot_url": player.get("headshot_url"),
                "height": safe_int(player.get("height")),
                "weight": safe_int(player.get("weight")),
                "stars": safe_int(player.get("stars")),
                "class_year": player.get("class_year") or player.get("year"),
                "conference": player.get("conference"),
                "division": player.get("division"),
                "jersey": player.get("jersey"),

                # NIL
                "nil_value": safe_int(player.get("nil_value")),
                "nil_tier": player.get("nil_tier"),
                "is_predicted": bool(player.get("is_predicted", False)),
                "confidence": player.get("confidence"),
                "valuation_source": player.get("valuation_source") or "CustomNILValuator",

                # PFF (comprehensive)
                "pff": pff_data if pff_data else None,

                # WAR
                "war": safe_float(player.get("war")),
                "war_low": safe_float(player.get("war_low")),
                "war_high": safe_float(player.get("war_high")),
                "war_confidence": player.get("war_confidence"),

                # Portal status
                "in_portal": bool(player.get("in_portal", False)),
                "portal_status": player.get("portal_status"),
                "origin_school": player.get("origin_school"),
                "destination_school": player.get("destination_school"),
                "portal_year": player.get("portal_year"),

                # School context
                "school_tier": player.get("school_tier"),
                "school_multiplier": safe_float(player.get("school_multiplier")),

                # Career stats
                "passing_yards": safe_int(player.get("passing_yards")),
                "passing_tds": safe_int(player.get("passing_tds")),
                "passing_ints": safe_int(player.get("passing_ints")),
                "rushing_yards": safe_int(player.get("rushing_yards")),
                "rushing_tds": safe_int(player.get("rushing_tds")),
                "rushing_attempts": safe_int(player.get("rushing_attempts")),
                "receiving_yards": safe_int(player.get("receiving_yards")),
                "receiving_tds": safe_int(player.get("receiving_tds")),
                "tackles": safe_int(player.get("tackles")),
                "assists": safe_int(player.get("assists")),
                "sacks": safe_int(player.get("sacks")),
                "interceptions": safe_int(player.get("interceptions")),
            }

    # Try portal data
    portal_df = get_portal_players()
    if not portal_df.empty:
        match = portal_df[portal_df["name"].str.lower() == name.lower()]
        if not match.empty:
            player = match.iloc[0]

            # Build PFF object from portal data
            pff_data = {
                "pff_overall": safe_float(player.get("pff_overall")),
                "pff_offense": safe_float(player.get("pff_offense")),
                "pff_defense": safe_float(player.get("pff_defense")),
            }
            pff_data = {k: v for k, v in pff_data.items() if v is not None}

            return {
                # Core identity
                "name": player.get("name", name),
                "position": player.get("position"),
                "school": player.get("destination_school") or player.get("origin_school"),
                "headshot_url": player.get("headshot_url"),
                "height": safe_int(player.get("height")),
                "weight": safe_int(player.get("weight")),
                "stars": safe_int(player.get("stars")),
                "class_year": player.get("class_year") or player.get("year"),

                # NIL
                "nil_value": safe_int(player.get("nil_value")),
                "nil_tier": player.get("nil_tier"),

                # PFF
                "pff": pff_data if pff_data else None,

                # Portal status
                "in_portal": True,  # Always true if found in portal data
                "portal_status": player.get("portal_status"),
                "origin_school": player.get("origin_school"),
                "destination_school": player.get("destination_school"),
                "portal_year": player.get("portal_year"),
            }

    raise HTTPException(status_code=404, detail="Player not found")


@app.get("/api/v1/players/{player_name}/nil", response_model=PlayerNIL)
async def get_player_nil(
    player_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Get player NIL valuation.

    Args:
        player_name: Player name

    Returns:
        NIL valuation data
    """
    name = sanitize_player_name(player_name)

    nil_df = get_nil_players()
    if nil_df.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    match = nil_df[nil_df["name"].str.lower() == name.lower()]
    if match.empty:
        # Try portal data
        portal_df = get_portal_players()
        match = portal_df[portal_df["name"].str.lower() == name.lower()]

    if match.empty:
        raise HTTPException(status_code=404, detail="Player not found")

    player = match.iloc[0]

    return PlayerNIL(
        name=player.get("name", name),
        nil_value=player.get("nil_value"),
        portaliq_value=player.get("portaliq_value"),
        on3_nil_value=player.get("on3_nil_value"),
        confidence=player.get("confidence"),
        is_predicted=player.get("is_predicted", True),
        value_low=player.get("value_low"),
        value_high=player.get("value_high"),
    )


@app.get("/api/v1/players/{player_name}/stats")
async def get_player_stats(
    player_name: str,
    season: int = Query(2025, description="Season year"),
    api_key: str = Depends(verify_api_key)
):
    """Get comprehensive player statistics with all PFF data.

    Returns detailed stats in the format expected by the frontend:
    - PFF grades (overall, offense, defense, position-specific)
    - Passing stats (yards, TDs, completion %, passer rating, etc.)
    - Rushing stats (yards, TDs, elusive rating, breakaway %, etc.)
    - Receiving stats (yards, TDs, targets, catch rate, etc.)
    - Pass rush stats (sacks, pressures, hits, hurries, etc.)
    - Coverage stats (QB rating against, targets allowed, etc.)
    - Blocking stats (pass/run block grades, pressures allowed, etc.)
    - Tackling stats (tackles, assists, missed tackle rate, etc.)

    Args:
        player_name: Player name
        season: Season year (default: 2025)

    Returns:
        Comprehensive player statistics
    """
    name = sanitize_player_name(player_name)

    # Load from NIL data (has all comprehensive stats)
    nil_df = get_nil_players()
    if nil_df.empty:
        raise HTTPException(status_code=404, detail="Player data not available")

    match = nil_df[nil_df["name"].str.lower() == name.lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")

    player = match.iloc[0]

    def safe_float(val, default=None):
        """Convert to float, return None if NaN."""
        if pd.isna(val):
            return default
        return float(val)

    def safe_int(val, default=None):
        """Convert to int, return None if NaN."""
        if pd.isna(val):
            return default
        return int(val)

    # Build response matching frontend PlayerStats interface
    return {
        "name": player.get("name"),
        "position": player.get("position"),
        "school": player.get("school"),
        "headshot_url": player.get("headshot_url"),
        "season": season,
        "nil_value": safe_float(player.get("nil_value")),
        "nil_tier": player.get("nil_tier"),
        "stars": safe_int(player.get("stars")),
        "height": safe_float(player.get("height")),
        "weight": safe_float(player.get("weight")),
        "games_played": safe_int(player.get("games_played")),

        # PFF Grades
        "pff": {
            "overall": safe_float(player.get("pff_overall")),
            "offense": safe_float(player.get("pff_offense")),
            "defense": safe_float(player.get("pff_defense")),
            "passing": safe_float(player.get("pff_passing")),
            "rushing": safe_float(player.get("pff_rushing")),
            "receiving": safe_float(player.get("pff_receiving")),
            "pass_block": safe_float(player.get("grades_pass_block")),
            "run_block": safe_float(player.get("grades_run_block")),
            "pass_rush": safe_float(player.get("pff_pass_rush")),
            "coverage": safe_float(player.get("pff_coverage")),
        },

        # Passing Stats
        "passing": {
            "yards": safe_int(player.get("passing_yards")),
            "touchdowns": safe_int(player.get("passing_tds")),
            "passer_rating": safe_float(player.get("passer_rating")),
            "completion_pct": safe_float(player.get("completion_pct")),
            "big_time_throw_pct": safe_float(player.get("big_time_throw_pct")),
        },

        # Rushing Stats
        "rushing": {
            "yards": safe_int(player.get("rushing_yards")),
            "touchdowns": safe_int(player.get("rushing_tds")),
            "yards_per_carry": safe_float(player.get("ypc")),
            "attempts": safe_int(player.get("rushing_attempts")),
            "elusive_rating": safe_float(player.get("elusive_rating")),
            "breakaway_yards": safe_int(player.get("breakaway_yards")),
            "breakaway_pct": safe_float(player.get("breakaway_percent")),
            "missed_tackles_forced": safe_int(player.get("missed_tackles_forced")),
            "yards_after_contact": safe_int(player.get("yaco")),
            "yaco_per_attempt": safe_float(player.get("yaco_per_attempt")),
        },

        # Receiving Stats
        "receiving": {
            "yards": safe_int(player.get("receiving_yards")),
            "touchdowns": safe_int(player.get("receiving_tds")),
            "receptions": safe_int(player.get("receptions")),
            "targets": safe_int(player.get("targets")),
            "drop_rate": safe_float(player.get("drop_rate")),
            "yards_per_route_run": safe_float(player.get("yards_per_route_run")),
        },

        # Pass Rush Stats
        "pass_rush": {
            "sacks": safe_float(player.get("sacks")),
            "pressures": safe_int(player.get("pressures")),
            "hits": safe_int(player.get("hits")),
            "hurries": safe_int(player.get("hurries")),
            "batted_passes": safe_int(player.get("batted_passes")),
        },

        # Coverage Stats
        "coverage": {
            "passer_rating_allowed": safe_float(player.get("qb_rating_against")),
            "targets_allowed": safe_int(player.get("targets_coverage")),
            "completions_allowed": safe_int(player.get("receptions_coverage")),
            "interceptions": safe_int(player.get("interceptions")),
            "pass_breakups": safe_int(player.get("pass_break_ups")),
        },

        # Blocking Stats
        "blocking": {
            "pressures_allowed": safe_int(player.get("pressures_allowed")),
            "sacks_allowed": safe_int(player.get("sacks_allowed")),
        },

        # Tackling Stats
        "tackling": {
            "tackles": safe_int(player.get("tackles")),
            "assists": safe_int(player.get("assists")),
        },
    }


@app.get("/api/v1/players/{player_name}/similar")
async def get_similar_players(
    player_name: str,
    limit: int = Query(5, ge=1, le=20),
    portal_only: bool = Query(False),
    api_key: str = Depends(verify_api_key)
):
    """Get players similar to the specified player.

    Args:
        player_name: Player name
        limit: Number of similar players to return
        portal_only: Only return players in transfer portal

    Returns:
        List of similar players with similarity scores
    """
    name = sanitize_player_name(player_name)

    pff_df = get_pff_grades()
    portal_df = get_portal_players() if portal_only else None

    comps = get_player_comps_for_card(name, pff_df, portal_df, num_comps=limit)

    if not comps:
        raise HTTPException(status_code=404, detail="Player not found or no comparisons available")

    return comps


@app.get("/api/v1/players/{player_name}/comparisons")
async def get_player_comparisons(
    player_name: str,
    include_nfl: bool = Query(True),
    include_college: bool = Query(True),
    limit: int = Query(5, ge=1, le=20),
    api_key: str = Depends(verify_api_key)
):
    """Get NFL and college player comparisons based on statistical similarity.

    Returns historically similar players from both NFL and college.
    """
    name = sanitize_player_name(player_name)

    # Get player data
    nil_df = get_nil_players()
    if nil_df.empty:
        raise HTTPException(status_code=404, detail="Player data not available")

    match = nil_df[nil_df["name"].str.lower() == name.lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")

    # For now, return similar players from same position
    # TODO: Implement full NFL/college comparison logic
    player = match.iloc[0]
    position = player.get("position")

    similar_players = nil_df[
        (nil_df["position"] == position) &
        (nil_df["name"].str.lower() != name.lower())
    ].head(limit)

    college_comps = []
    for _, row in similar_players.iterrows():
        college_comps.append({
            "name": row.get("name"),
            "school_or_team": row.get("school"),
            "position": row.get("position"),
            "similarity": 85.0,  # Placeholder
            "league": "NCAA",
            "seasons": [2025],
            "matching_stats": {}
        })

    return {
        "player": name,
        "position": position,
        "nfl_comparisons": [] if not include_nfl else [],
        "college_comparisons": college_comps if include_college else [],
        "message": "Player comparisons"
    }


@app.get("/api/v1/players/{player_name}/elite-profile")
async def get_player_elite_profile(
    player_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Get elite athlete profile with measurables and bonuses."""
    name = sanitize_player_name(player_name)

    nil_df = get_nil_players()
    if nil_df.empty:
        raise HTTPException(status_code=404, detail="Player data not available")

    match = nil_df[nil_df["name"].str.lower() == name.lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")

    player = match.iloc[0]

    # Identify elite traits based on comprehensive PFF stats
    elite_traits = []
    elite_bonus = 0.0

    position = player.get("position", "")

    # RB elite traits
    if position == "HB":
        if pd.notna(player.get("elusive_rating")) and player.get("elusive_rating", 0) > 100:
            elite_traits.append("Elite Elusiveness (>100)")
            elite_bonus += 0.5
        if pd.notna(player.get("breakaway_percent")) and player.get("breakaway_percent", 0) > 30:
            elite_traits.append("Explosive (>30% breakaway)")
            elite_bonus += 0.4

    # DB elite traits
    elif position in ["CB", "S"]:
        if pd.notna(player.get("qb_rating_against")) and player.get("qb_rating_against", 999) < 50:
            elite_traits.append("Shutdown Coverage (<50 QBR)")
            elite_bonus += 0.6
        if pd.notna(player.get("pass_break_ups")) and player.get("pass_break_ups", 0) > 8:
            elite_traits.append("Ball Hawk (>8 PBU)")
            elite_bonus += 0.3

    # Edge elite traits
    elif position in ["ED", "DE"]:
        hits = player.get("hits", 0) or 0
        hurries = player.get("hurries", 0) or 0
        total_disruptions = hits + hurries
        if total_disruptions > 50:
            elite_traits.append(f"Pass Rush Terror ({total_disruptions} disruptions)")
            elite_bonus += 0.7

    # OL elite traits
    elif position in ["OL", "OT", "OG", "C", "T", "G"]:
        if pd.notna(player.get("grades_pass_block")) and player.get("grades_pass_block", 0) > 85:
            elite_traits.append("Elite Pass Protection (>85 grade)")
            elite_bonus += 0.6

    return {
        "player": name,
        "position": position,
        "elite_traits": elite_traits,
        "elite_trait_count": len(elite_traits),
        "elite_bonus": elite_bonus,
        "draft_adjustment": 0.0,
        "measurables": {
            "height": safe_float(player.get("height")),
            "weight": safe_float(player.get("weight"))
        },
        "thresholds": {}
    }


@app.get("/api/v1/players/{player_name}/career")
async def get_player_career(
    player_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Get career stats across multiple seasons."""
    name = sanitize_player_name(player_name)

    nil_df = get_nil_players()
    if nil_df.empty:
        raise HTTPException(status_code=404, detail="Player data not available")

    match = nil_df[nil_df["name"].str.lower() == name.lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")

    player = match.iloc[0]

    # For now, return current season only
    # TODO: Load multi-season data when available
    current_season = {
        "season": 2025,
        "school": player.get("school"),
        "position": player.get("position"),
        "games_played": safe_int(player.get("games_played")),
        "passing_yards": safe_int(player.get("passing_yards")),
        "rushing_yards": safe_int(player.get("rushing_yards")),
        "receiving_yards": safe_int(player.get("receiving_yards")),
        "pff_overall": safe_float(player.get("pff_overall"))
    }

    return {
        "player_name": name,
        "college_seasons": [current_season],
        "nfl_seasons": [],
        "combine_data": {},
        "total_seasons": 1
    }


@app.get("/api/v1/draft/project/{player_name}")
async def get_draft_projection(
    player_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Get NFL draft projection for a player."""
    name = sanitize_player_name(player_name)

    nil_df = get_nil_players()
    if nil_df.empty:
        raise HTTPException(status_code=404, detail="Player data not available")

    match = nil_df[nil_df["name"].str.lower() == name.lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")

    player = match.iloc[0]
    position = player.get("position", "")
    pff_overall = safe_float(player.get("pff_overall"), 60.0)

    # Simple draft projection based on PFF grade
    if pff_overall >= 90:
        draft_grade = 95
        draft_round = 1
        projected_pick = 15
    elif pff_overall >= 80:
        draft_grade = 85
        draft_round = 2
        projected_pick = 50
    elif pff_overall >= 70:
        draft_grade = 75
        draft_round = 4
        projected_pick = 120
    else:
        draft_grade = 65
        draft_round = 6
        projected_pick = 200

    return {
        "player": name,
        "position": position,
        "draft_grade": draft_grade,
        "draft_letter_grade": "A" if draft_grade >= 90 else "B" if draft_grade >= 80 else "C",
        "projected_round": draft_round,
        "projected_pick": projected_pick,
        "pick_range": f"Round {draft_round}",
        "draft_probability": 0.8 if draft_grade >= 70 else 0.5,
        "elite_bonus": 0.0,
        "elite_traits": [],
        "elite_adjustment": 0.0,
        "rookie_contract_estimate": 5000000 if draft_round <= 2 else 1000000,
        "career_earnings_estimate": 20000000 if draft_round <= 2 else 5000000,
        "expected_draft_value": draft_grade * 100000
    }


@app.get("/api/v1/draft/comparables/{player_name}")
async def get_draft_comparables(
    player_name: str,
    limit: int = Query(5, ge=1, le=20),
    api_key: str = Depends(verify_api_key)
):
    """Get historical draft comparables for a player."""
    name = sanitize_player_name(player_name)

    nil_df = get_nil_players()
    if nil_df.empty:
        raise HTTPException(status_code=404, detail="Player data not available")

    match = nil_df[nil_df["name"].str.lower() == name.lower()]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"Player '{name}' not found")

    # TODO: Load actual draft data and find comparables
    # For now, return empty list
    return {
        "comparables": []
    }


# Helper functions (add at module level if not exists)
def safe_float(val, default=None):
    """Convert to float, return default if NaN."""
    if pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def safe_int(val, default=None):
    """Convert to int, return default if NaN."""
    if pd.isna(val):
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


# =============================================================================
# Portal Endpoints
# =============================================================================

@app.get("/api/v1/portal/recent", response_model=List[PortalPlayer])
async def get_recent_portal(
    days: int = Query(7, ge=1, le=30),
    status: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    api_key: str = Depends(verify_api_key)
):
    """Get recent portal activity.

    Args:
        days: Number of days to look back
        status: Filter by status (Committed, Entered, etc.)
        position: Filter by position
        limit: Maximum results

    Returns:
        List of recent portal players
    """
    df = get_portal_players()

    if df.empty:
        return []

    # Filter by status if provided
    if status:
        df = df[df["status"].str.lower() == status.lower()]

    # Filter by position if provided
    if position:
        df = df[df["position"].str.upper() == position.upper()]

    # Limit results
    df = df.head(limit)

    results = []
    for _, row in df.iterrows():
        results.append(PortalPlayer(
            name=row.get("name", ""),
            position=row.get("position"),
            team=row.get("destination_school") or row.get("origin_school"),
            origin_school=row.get("origin_school"),
            destination_school=row.get("destination_school"),
            status=row.get("status"),
            portal_year=row.get("portal_year"),
            nil_value=row.get("nil_value"),
            stars=row.get("stars"),
        ))

    return results


@app.get("/api/v1/portal/search", response_model=List[PortalPlayer])
async def search_portal(
    q: Optional[str] = None,
    position: Optional[str] = None,
    min_stars: Optional[float] = Query(None, ge=0, le=5),
    max_nil: Optional[float] = None,
    min_nil: Optional[float] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    api_key: str = Depends(verify_api_key)
):
    """Search portal players with filters.

    Args:
        q: Name search query
        position: Filter by position
        min_stars: Minimum star rating
        max_nil: Maximum NIL value
        min_nil: Minimum NIL value
        status: Portal status
        limit: Maximum results

    Returns:
        List of matching portal players
    """
    df = get_portal_players()

    if df.empty:
        return []

    # Apply filters
    if q:
        query = sanitize_search_query(q)
        df = df[df["name"].str.contains(query, case=False, na=False)]

    if position:
        df = df[df["position"].str.upper() == position.upper()]

    if min_stars is not None:
        df = df[df["stars"] >= min_stars]

    if status:
        df = df[df["status"].str.lower() == status.lower()]

    if min_nil is not None:
        df = df[df["nil_value"] >= min_nil]

    if max_nil is not None:
        df = df[df["nil_value"] <= max_nil]

    df = df.head(limit)

    results = []
    for _, row in df.iterrows():
        results.append(PortalPlayer(
            name=row.get("name", ""),
            position=row.get("position"),
            team=row.get("destination_school") or row.get("origin_school"),
            origin_school=row.get("origin_school"),
            destination_school=row.get("destination_school"),
            status=row.get("status"),
            portal_year=row.get("portal_year"),
            nil_value=row.get("nil_value"),
            stars=row.get("stars"),
        ))

    return results


@app.get("/api/v1/portal/teams", response_model=List[Dict[str, Any]])
async def get_team_rankings_endpoint(
    year: int = Query(2026, ge=2020, le=2030),
    limit: int = Query(25, ge=1, le=134),
    api_key: str = Depends(verify_api_key)
):
    """Get team portal rankings.

    Args:
        year: Portal year
        limit: Number of teams

    Returns:
        List of teams with ranking data
    """
    df = get_team_rankings(year=year)

    if df.empty:
        return []

    df = df.head(limit)

    results = []
    for _, row in df.iterrows():
        results.append({
            "rank": row.get("rank"),
            "name": row.get("name"),
            "overall_score": row.get("overall_score"),
            "players": row.get("players"),
            "avg_rating": row.get("avg_rating"),
        })

    return results


# =============================================================================
# Frontend Compatibility Endpoints (for Next.js frontend)
# =============================================================================

@app.get("/api/nil/leaderboard")
async def get_nil_leaderboard(
    position: Optional[str] = None,
    school: Optional[str] = None,
    conference: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    api_key: str = Depends(verify_api_key)
):
    """Get NIL leaderboard for the frontend dashboard.

    Returns players sorted by NIL valuation with optional filters.
    """
    df = get_nil_players()

    if df.empty:
        return {"status": "success", "data": {"players": [], "total": 0}}

    # Apply filters
    if position:
        df = df[df["position"].str.upper() == position.upper()]
    if school:
        df = df[df["school"].str.lower().str.contains(school.lower(), na=False)]
    if conference:
        df = df[df.get("conference", "").str.lower().str.contains(conference.lower(), na=False)]

    # Sort by NIL value
    if "nil_value" in df.columns:
        df = df.sort_values("nil_value", ascending=False)

    total = len(df)
    df = df.head(limit)

    players = []
    for i, (_, row) in enumerate(df.iterrows()):
        nil_val = row.get("nil_value", 0) or 0
        players.append({
            "rank": i + 1,
            "player_id": str(row.get("player_id", f"player_{i}")),
            "player_name": row.get("name", ""),
            "position": row.get("position", ""),
            "school": row.get("school", row.get("team", "")),
            "valuation": nil_val,
            "nil_tier": _get_nil_tier(nil_val),
            "social_followers": row.get("social_followers"),
            "headshot_url": row.get("headshot_url"),
        })

    return {"status": "success", "data": {"players": players, "total": total}}


def _get_nil_tier(value: float) -> str:
    """Get NIL tier based on valuation."""
    if value >= 1000000:
        return "Elite"
    elif value >= 500000:
        return "Premium"
    elif value >= 100000:
        return "High"
    elif value >= 50000:
        return "Mid"
    else:
        return "Emerging"


@app.get("/api/portal/active")
async def get_active_portal_players(
    position: Optional[str] = None,
    origin_school: Optional[str] = None,
    origin_conference: Optional[str] = None,
    min_stars: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    api_key: str = Depends(verify_api_key)
):
    """Get active transfer portal players for the frontend.

    Returns players currently in the portal with optional filters.
    """
    df = get_portal_players()

    if df.empty:
        return {"status": "success", "data": []}

    # Apply filters
    if position:
        df = df[df["position"].str.upper() == position.upper()]
    if origin_school:
        df = df[df["origin_school"].str.lower().str.contains(origin_school.lower(), na=False)]
    if origin_conference and "origin_conference" in df.columns:
        df = df[df["origin_conference"].str.lower().str.contains(origin_conference.lower(), na=False)]
    if min_stars:
        df = df[df["stars"] >= min_stars]
    if status and status != "all":
        if status == "available":
            df = df[~df["status"].str.lower().isin(["committed", "withdrawn"])]
        else:
            df = df[df["status"].str.lower() == status.lower()]

    df = df.head(limit)

    players = []
    for _, row in df.iterrows():
        players.append({
            "player_id": str(row.get("player_id", "")),
            "player_name": row.get("name", ""),
            "position": row.get("position", ""),
            "origin_school": row.get("origin_school", ""),
            "origin_conference": row.get("origin_conference"),
            "destination_school": row.get("destination_school"),
            "stars": row.get("stars"),
            "entry_date": str(row.get("entry_date", "")) if row.get("entry_date") else None,
            "status": _normalize_status(row.get("status", "available")),
            "nil_valuation": row.get("nil_value") or row.get("nil_valuation"),
            "days_in_portal": row.get("days_in_portal"),
            "headshot_url": row.get("headshot_url"),
        })

    return {"status": "success", "data": {"players": players, "total": len(players)}}


def _normalize_status(status: str) -> str:
    """Normalize portal status to frontend expected values."""
    status_lower = str(status).lower()
    if "commit" in status_lower:
        return "committed"
    elif "withdraw" in status_lower:
        return "withdrawn"
    else:
        return "available"


@app.get("/api/search/status")
async def get_search_status():
    """Get AI search availability status."""
    import os
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    # Get dataset counts
    nil_df = get_nil_players()
    portal_df = get_portal_players()
    pff_df = get_pff_grades()

    datasets = {
        "nil_valuations": {"loaded": not nil_df.empty, "records": len(nil_df)},
        "portal_players": {"loaded": not portal_df.empty, "records": len(portal_df)},
        "pff_grades": {"loaded": not pff_df.empty, "records": len(pff_df)},
    }

    return {
        "status": "success",
        "data": {
            "available": bool(anthropic_key),
            "anthropic_configured": bool(anthropic_key),
            "datasets_loaded": sum(1 for d in datasets.values() if d["loaded"]),
            "datasets": datasets
        }
    }


@app.post("/api/search")
async def ai_search(
    request: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """AI-powered search endpoint.

    Uses Anthropic Claude to answer questions about players, NIL, and portal.
    """
    import os
    query = request.get("query", "")
    context = request.get("context", "")

    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not anthropic_key:
        return {
            "status": "success",
            "data": {
                "response": "AI search is not configured. Please set the ANTHROPIC_API_KEY environment variable.",
                "sources": [],
                "players_mentioned": [],
                "data_used": []
            }
        }

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)

        # Get relevant data context
        nil_df = get_nil_players()
        portal_df = get_portal_players()

        # Build data context for the AI
        data_context = "Available data:\n"

        if not nil_df.empty:
            top_nil = nil_df.nlargest(10, "nil_value")[["name", "position", "school", "nil_value"]].to_string()
            data_context += f"\nTop NIL Players:\n{top_nil}\n"

        if not portal_df.empty:
            recent_portal = portal_df.head(10)[["name", "position", "origin_school", "destination_school", "status"]].to_string()
            data_context += f"\nRecent Portal Activity:\n{recent_portal}\n"

        system_prompt = f"""You are Portal IQ's AI Assistant, an expert on college football NIL valuations and the transfer portal.

{data_context}

Previous conversation context:
{context}

Answer questions about:
- NIL valuations and projections
- Transfer portal players and activity
- Player comparisons and analytics
- Team recruiting and portal strategies

Be concise and data-driven. Reference specific players and values when available."""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": query}]
        )

        ai_response = response.content[0].text

        return {
            "status": "success",
            "data": {
                "response": ai_response,
                "sources": ["Portal IQ Database", "NIL Valuations", "Transfer Portal Data"],
                "players_mentioned": [],
                "data_used": ["nil_valuations", "portal_players"]
            }
        }
    except Exception as e:
        logger.error(f"AI search error: {e}")
        return {
            "status": "success",
            "data": {
                "response": f"I encountered an error processing your request. Please try again.",
                "sources": [],
                "players_mentioned": [],
                "data_used": []
            }
        }


# =============================================================================
# Webhook Endpoints (for playmakervc.com notifications)
# =============================================================================

class WebhookSubscription(BaseModel):
    """Webhook subscription request."""
    url: str
    events: List[str]  # player.entered_portal, player.committed, nil_value.updated
    secret: Optional[str] = None


# In-memory webhook storage (use database in production)
_webhook_subscriptions: Dict[str, WebhookSubscription] = {}


@app.post("/api/v1/webhooks/subscribe")
async def subscribe_webhook(
    subscription: WebhookSubscription,
    api_key: str = Depends(verify_api_key)
):
    """Subscribe to webhook events.

    Args:
        subscription: Webhook subscription details

    Returns:
        Subscription confirmation
    """
    import uuid
    sub_id = str(uuid.uuid4())
    _webhook_subscriptions[sub_id] = subscription

    logger.info(f"Webhook subscription created: {sub_id} for events {subscription.events}")

    return {
        "subscription_id": sub_id,
        "events": subscription.events,
        "status": "active"
    }


@app.delete("/api/v1/webhooks/{subscription_id}")
async def unsubscribe_webhook(
    subscription_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Unsubscribe from webhook events."""
    if subscription_id in _webhook_subscriptions:
        del _webhook_subscriptions[subscription_id]
        return {"status": "unsubscribed"}

    raise HTTPException(status_code=404, detail="Subscription not found")


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
