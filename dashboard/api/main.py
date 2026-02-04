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


@app.get("/api/v1/players/{player_name}/profile", response_model=PlayerProfile)
async def get_player_profile(
    player_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Get full player profile.

    Args:
        player_name: Player name (URL encoded)

    Returns:
        Player profile with NIL, performance, and physical data
    """
    name = sanitize_player_name(player_name)

    # Try NIL data first
    nil_df = get_nil_players()
    if not nil_df.empty:
        match = nil_df[nil_df["name"].str.lower() == name.lower()]
        if not match.empty:
            player = match.iloc[0]
            return PlayerProfile(
                name=player.get("name", name),
                position=player.get("position"),
                team=player.get("team") or player.get("school"),
                nil_value=player.get("nil_value"),
                portaliq_value=player.get("portaliq_value"),
                stars=player.get("stars"),
                pff_overall=player.get("pff_overall"),
                school=player.get("school"),
                headshot_url=player.get("headshot_url"),
                height_display=player.get("height_display"),
                weight=player.get("weight"),
            )

    # Try portal data
    portal_df = get_portal_players()
    if not portal_df.empty:
        match = portal_df[portal_df["name"].str.lower() == name.lower()]
        if not match.empty:
            player = match.iloc[0]
            return PlayerProfile(
                name=player.get("name", name),
                position=player.get("position"),
                team=player.get("destination_school") or player.get("origin_school"),
                nil_value=player.get("nil_value"),
                portaliq_value=player.get("portaliq_value"),
                stars=player.get("stars"),
                pff_overall=player.get("pff_overall"),
                school=player.get("destination_school"),
                headshot_url=player.get("headshot_url"),
                height_display=player.get("height_display"),
                weight=player.get("weight"),
            )

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
