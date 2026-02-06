"""
Portal IQ API Routes

Endpoints for college football NIL valuation, transfer portal intelligence,
draft projections, and roster optimization.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
import logging

from ..auth import get_current_user, require_tier
from ...utils.s3_loader import load_nil_data, load_portal_data
from .schemas import (
    # NIL
    NILValuationRequest,
    NILValuationResponse,
    NILBulkValuationRequest,
    NILBulkValuationResponse,
    NILLeaderboardResponse,
    # Portal
    PortalPlayerResponse,
    PortalPredictionRequest,
    PortalPredictionResponse,
    PortalSearchRequest,
    AtRiskPlayersRequest,
    AtRiskPlayersResponse,
    # Draft
    DraftProjectionRequest,
    DraftProjectionResponse,
    DraftBoardResponse,
    # Roster
    RosterOptimizationRequest,
    RosterOptimizationResponse,
    RosterScenarioRequest,
    RosterScenarioResponse,
    # Comparison
    PlayerComparisonRequest,
    PlayerComparisonResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# NIL VALUATION ENDPOINTS
# =============================================================================

@router.post("/nil/valuate", response_model=NILValuationResponse)
async def valuate_player(
    request: NILValuationRequest,
    user: dict = Depends(get_current_user),
):
    """
    Get NIL market valuation for a single player.

    Returns estimated value with confidence intervals and breakdown.
    """
    logger.info(f"NIL valuation request for {request.player_name} by {user['email']}")

    # TODO: Call NIL valuator model
    # from ...models.portal_iq.nil_valuator import NILValuator
    # valuator = NILValuator()
    # result = valuator.value_player(request.dict())

    # Placeholder response
    return NILValuationResponse(
        player_name=request.player_name,
        valuation=500000,
        valuation_low=350000,
        valuation_high=700000,
        nil_tier="premium",
        breakdown={
            "base_position_value": 200000,
            "school_multiplier": 1.5,
            "social_media_value": 50000,
            "performance_bonus": 50000,
        },
        confidence=0.75,
    )


@router.post("/nil/bulk-valuate", response_model=NILBulkValuationResponse)
async def bulk_valuate_players(
    request: NILBulkValuationRequest,
    user: dict = Depends(require_tier("pro")),
):
    """
    Bulk NIL valuation for multiple players.

    Pro tier required.
    """
    logger.info(f"Bulk NIL valuation for {len(request.players)} players by {user['email']}")

    # TODO: Process bulk valuations
    valuations = []

    return NILBulkValuationResponse(
        valuations=valuations,
        total_value=0,
        count=len(request.players),
    )


@router.get("/nil/leaderboard")
async def get_nil_leaderboard(
    position: Optional[str] = Query(None, description="Filter by position"),
    school: Optional[str] = Query(None, description="Filter by school"),
    conference: Optional[str] = Query(None, description="Filter by conference"),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """
    Get top players by NIL valuation.
    """
    df = load_nil_data()

    if df.empty:
        return {"status": "success", "data": {"players": [], "total": 0}}

    # Apply filters
    if position:
        pos_col = "position" if "position" in df.columns else None
        if pos_col:
            df = df[df[pos_col].str.upper() == position.upper()]

    if school:
        school_col = next((c for c in df.columns if c in ["school", "team"]), None)
        if school_col:
            df = df[df[school_col].str.lower().str.contains(school.lower(), na=False)]

    # Sort by NIL value
    nil_col = next((c for c in df.columns if c in ["nil_value", "valuation", "nil_valuation"]), None)
    if nil_col:
        df = df.sort_values(nil_col, ascending=False)

    total = len(df)
    df = df.head(limit)

    # Build response
    players = []
    for i, (_, row) in enumerate(df.iterrows()):
        nil_val = row.get("nil_value") or row.get("valuation") or row.get("nil_valuation") or 0
        name = row.get("name") or row.get("player_name") or row.get("player") or ""

        players.append({
            "rank": i + 1,
            "player_id": str(row.get("player_id", f"player_{i}")),
            "player_name": name,
            "position": row.get("position", ""),
            "school": row.get("school") or row.get("team", ""),
            "valuation": float(nil_val) if nil_val else 0,
            "headshot_url": row.get("headshot_url"),
        })

    return {"status": "success", "data": {"players": players, "total": total}}


@router.get("/nil/tiers")
async def get_nil_tiers(user: dict = Depends(get_current_user)):
    """Get NIL tier definitions and thresholds."""
    return {
        "mega": {"min": 1000000, "label": "Mega ($1M+)"},
        "premium": {"min": 500000, "label": "Premium ($500K+)"},
        "solid": {"min": 100000, "label": "Solid ($100K+)"},
        "moderate": {"min": 25000, "label": "Moderate ($25K+)"},
        "entry": {"min": 0, "label": "Entry Level"},
    }


# =============================================================================
# TRANSFER PORTAL ENDPOINTS
# =============================================================================

@router.get("/portal/active")
async def get_active_portal_players(
    position: Optional[str] = Query(None),
    origin_school: Optional[str] = Query(None),
    origin_conference: Optional[str] = Query(None),
    min_stars: Optional[int] = Query(None, ge=1, le=5),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """
    Get currently active transfer portal players.
    """
    df = load_portal_data()

    if df.empty:
        return {"status": "success", "data": {"players": [], "total": 0}}

    # Apply filters
    if position:
        pos_col = "position" if "position" in df.columns else None
        if pos_col:
            df = df[df[pos_col].str.upper() == position.upper()]

    if origin_school:
        school_cols = ["from_school", "origin_school", "school"]
        school_col = next((c for c in school_cols if c in df.columns), None)
        if school_col:
            df = df[df[school_col].str.lower().str.contains(origin_school.lower(), na=False)]

    if min_stars:
        if "stars" in df.columns:
            df = df[df["stars"] >= min_stars]

    if status and status != "all":
        if "status" in df.columns:
            df = df[df["status"].str.lower().str.contains(status.lower(), na=False)]

    total = len(df)
    df = df.head(limit)

    # Build response
    players = []
    for i, (_, row) in enumerate(df.iterrows()):
        name = row.get("name") or row.get("player_name") or row.get("player") or ""
        nil_val = row.get("nil_value") or row.get("nil_valuation") or row.get("valuation") or 0
        origin = row.get("from_school") or row.get("origin_school") or row.get("school") or ""

        # Normalize status
        raw_status = str(row.get("status", "available")).lower()
        if "commit" in raw_status:
            normalized_status = "committed"
        elif "withdraw" in raw_status:
            normalized_status = "withdrawn"
        else:
            normalized_status = "available"

        players.append({
            "player_id": str(row.get("player_id", f"portal_{i}")),
            "player_name": name,
            "position": row.get("position", ""),
            "origin_school": origin,
            "destination_school": row.get("to_school") or row.get("destination_school"),
            "stars": int(row.get("stars", 3)) if row.get("stars") else None,
            "status": normalized_status,
            "nil_valuation": float(nil_val) if nil_val else 0,
            "entry_date": str(row.get("entry_date", "")) if row.get("entry_date") else None,
            "headshot_url": row.get("headshot_url"),
        })

    return {"status": "success", "data": {"players": players, "total": total}}


@router.post("/portal/predict", response_model=PortalPredictionResponse)
async def predict_portal_destination(
    request: PortalPredictionRequest,
    user: dict = Depends(get_current_user),
):
    """
    Predict likely transfer destinations for a portal player.
    """
    logger.info(f"Portal prediction for {request.player_name} by {user['email']}")

    # TODO: Call portal predictor model
    return PortalPredictionResponse(
        player_name=request.player_name,
        entry_probability=0.0,  # Already in portal
        likely_destinations=[],
        risk_factors=[],
    )


@router.post("/portal/at-risk", response_model=AtRiskPlayersResponse)
async def get_at_risk_players(
    request: AtRiskPlayersRequest,
    user: dict = Depends(get_current_user),
):
    """
    Identify players at risk of entering the transfer portal.

    Useful for programs to monitor their own roster.
    """
    logger.info(f"At-risk analysis for {request.school} by {user['email']}")

    # TODO: Call portal predictor for flight risk
    return AtRiskPlayersResponse(
        school=request.school,
        at_risk_players=[],
        total_at_risk=0,
    )


@router.get("/portal/team/{team}")
async def get_team_portal_activity(
    team: str,
    season: int = Query(2025),
    user: dict = Depends(get_current_user),
):
    """
    Get portal activity for a specific team.
    Shows incoming transfers, outgoing transfers, and net talent change.
    """
    df = load_portal_data()

    if df.empty:
        return {"status": "success", "data": {
            "team": team,
            "season": season,
            "incoming": [],
            "outgoing": [],
            "net_war": 0,
            "total_nil_invested": 0,
            "summary": {"incoming_count": 0, "outgoing_count": 0, "net_count": 0}
        }}

    team_lower = team.lower()

    # Helper to check school match
    def school_matches(school_val, target):
        if not school_val or not target:
            return False
        return target in str(school_val).lower()

    # Find incoming transfers (destination = this team, committed)
    dest_col = next((c for c in ["destination_school", "to_school", "dest_school"] if c in df.columns), None)
    status_col = "status" if "status" in df.columns else None

    incoming_df = df.copy()
    if dest_col:
        incoming_df = incoming_df[incoming_df[dest_col].apply(lambda x: school_matches(x, team_lower))]
    if status_col:
        incoming_df = incoming_df[incoming_df[status_col].str.lower().str.contains("commit", na=False)]

    # Find outgoing transfers (origin = this team)
    origin_cols = ["origin_school", "from_school", "school"]
    origin_col = next((c for c in origin_cols if c in df.columns), None)

    outgoing_df = df.copy()
    if origin_col:
        outgoing_df = outgoing_df[outgoing_df[origin_col].apply(lambda x: school_matches(x, team_lower))]

    # Build incoming list with WAR calculations
    incoming = []
    total_incoming_war = 0
    total_nil = 0

    for i, (_, row) in enumerate(incoming_df.iterrows()):
        name = row.get("name") or row.get("player_name") or ""
        nil_val = float(row.get("nil_value") or row.get("nil_valuation") or 0)
        position = row.get("position", "ATH")
        stars = int(row.get("stars", 3)) if row.get("stars") else 3

        # Calculate WAR (simplified version matching frontend algorithm)
        position_war = {"QB": 3.0, "WR": 1.2, "RB": 0.9, "EDGE": 1.5, "CB": 1.2, "OT": 1.0, "LB": 1.0, "S": 0.9, "TE": 0.8, "DT": 0.8}.get(position.upper(), 0.8)
        star_mult = {5: 2.0, 4: 1.5, 3: 1.0, 2: 0.6, 1: 0.3}.get(stars, 1.0)
        war = round(position_war * star_mult, 2)
        total_incoming_war += war
        total_nil += nil_val

        incoming.append({
            "player_name": name,
            "position": position,
            "origin_school": row.get("from_school") or row.get("origin_school") or "",
            "stars": stars,
            "nil_valuation": nil_val,
            "war": war,
            "status": "committed"
        })

    # Build outgoing list
    outgoing = []
    total_outgoing_war = 0

    for i, (_, row) in enumerate(outgoing_df.iterrows()):
        name = row.get("name") or row.get("player_name") or ""
        nil_val = float(row.get("nil_value") or row.get("nil_valuation") or 0)
        position = row.get("position", "ATH")
        stars = int(row.get("stars", 3)) if row.get("stars") else 3

        position_war = {"QB": 3.0, "WR": 1.2, "RB": 0.9, "EDGE": 1.5, "CB": 1.2, "OT": 1.0, "LB": 1.0, "S": 0.9, "TE": 0.8, "DT": 0.8}.get(position.upper(), 0.8)
        star_mult = {5: 2.0, 4: 1.5, 3: 1.0, 2: 0.6, 1: 0.3}.get(stars, 1.0)
        war = round(position_war * star_mult, 2)
        total_outgoing_war += war

        raw_status = str(row.get("status", "")).lower()
        status = "committed" if "commit" in raw_status else "available"
        dest = row.get("to_school") or row.get("destination_school") or ""

        outgoing.append({
            "player_name": name,
            "position": position,
            "destination_school": dest,
            "stars": stars,
            "nil_valuation": nil_val,
            "war": war,
            "status": status
        })

    net_war = round(total_incoming_war - total_outgoing_war, 2)

    return {"status": "success", "data": {
        "team": team,
        "season": season,
        "incoming": incoming,
        "outgoing": outgoing,
        "net_war": net_war,
        "total_nil_invested": total_nil,
        "summary": {
            "incoming_count": len(incoming),
            "outgoing_count": len(outgoing),
            "net_count": len(incoming) - len(outgoing),
            "incoming_war": round(total_incoming_war, 2),
            "outgoing_war": round(total_outgoing_war, 2)
        }
    }}


# =============================================================================
# DRAFT PROJECTION ENDPOINTS
# =============================================================================

@router.post("/draft/project", response_model=DraftProjectionResponse)
async def project_draft_outcome(
    request: DraftProjectionRequest,
    user: dict = Depends(get_current_user),
):
    """
    Get NFL draft projection for a college player.
    """
    logger.info(f"Draft projection for {request.player_name} by {user['email']}")

    # TODO: Call draft projector model
    return DraftProjectionResponse(
        player_name=request.player_name,
        draft_probability=0.5,
        projected_round=3,
        projected_pick=85,
        draft_grade=65.0,
        comparable_players=[],
        career_value_projection={
            "rookie_contract": 5000000,
            "career_earnings_potential": 25000000,
        },
    )


@router.get("/draft/board", response_model=DraftBoardResponse)
async def get_draft_board(
    position: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(get_current_user),
):
    """
    Get current draft board rankings.
    """
    return DraftBoardResponse(players=[], last_updated=None)


@router.get("/draft/team/{team}")
async def get_team_draft_history(
    team: str,
    years: int = Query(5, ge=1, le=20),
    user: dict = Depends(get_current_user),
):
    """
    Get historical draft picks from a school.
    """
    return {
        "team": team,
        "years": years,
        "picks": [],
        "total_picks": 0,
        "first_round_picks": 0,
    }


# =============================================================================
# ROSTER OPTIMIZATION ENDPOINTS
# =============================================================================

@router.post("/roster/optimize", response_model=RosterOptimizationResponse)
async def optimize_roster(
    request: RosterOptimizationRequest,
    user: dict = Depends(require_tier("pro")),
):
    """
    Optimize portal target selection within budget constraints.

    Pro tier required.
    """
    logger.info(f"Roster optimization for {request.school} by {user['email']}")

    # TODO: Call roster optimizer
    return RosterOptimizationResponse(
        status="success",
        selected_players=[],
        total_war=0,
        total_cost=0,
        budget_remaining=request.budget,
        projected_wins_added=0,
    )


@router.post("/roster/scenario", response_model=RosterScenarioResponse)
async def evaluate_roster_scenario(
    request: RosterScenarioRequest,
    user: dict = Depends(get_current_user),
):
    """
    Evaluate a specific roster scenario (additions/departures).
    """
    logger.info(f"Roster scenario evaluation for {request.school} by {user['email']}")

    return RosterScenarioResponse(
        school=request.school,
        scenario_name=request.name,
        current_projected_wins=8.0,
        new_projected_wins=8.0,
        win_delta=0.0,
        roster_grade="B",
        position_grades={},
    )


@router.get("/roster/{team}/needs")
async def get_roster_needs(
    team: str,
    user: dict = Depends(get_current_user),
):
    """
    Get position needs analysis for a team based on portal activity.
    """
    df = load_portal_data()

    if df.empty:
        return {"status": "success", "data": {
            "team": team,
            "needs": {},
            "priority_positions": [],
            "analysis": "No portal data available"
        }}

    team_lower = team.lower()

    def school_matches(school_val, target):
        if not school_val or not target:
            return False
        return target in str(school_val).lower()

    # Find outgoing by position
    origin_col = next((c for c in ["origin_school", "from_school", "school"] if c in df.columns), None)
    outgoing_df = df[df[origin_col].apply(lambda x: school_matches(x, team_lower))] if origin_col else df.head(0)

    # Find incoming by position
    dest_col = next((c for c in ["destination_school", "to_school"] if c in df.columns), None)
    incoming_df = df[df[dest_col].apply(lambda x: school_matches(x, team_lower))] if dest_col else df.head(0)
    if "status" in incoming_df.columns:
        incoming_df = incoming_df[incoming_df["status"].str.lower().str.contains("commit", na=False)]

    # Calculate net by position
    position_needs = {}
    all_positions = ["QB", "RB", "WR", "TE", "OT", "OG", "C", "EDGE", "DT", "LB", "CB", "S"]

    for pos in all_positions:
        out_count = len(outgoing_df[outgoing_df["position"].str.upper() == pos]) if "position" in outgoing_df.columns else 0
        in_count = len(incoming_df[incoming_df["position"].str.upper() == pos]) if "position" in incoming_df.columns else 0
        net = in_count - out_count

        need_level = "none"
        if net < -2:
            need_level = "critical"
        elif net < 0:
            need_level = "moderate"
        elif net == 0 and out_count > 0:
            need_level = "low"

        position_needs[pos] = {
            "incoming": in_count,
            "outgoing": out_count,
            "net": net,
            "need_level": need_level
        }

    # Identify priority positions
    priority = [pos for pos, data in position_needs.items() if data["need_level"] in ("critical", "moderate")]
    priority.sort(key=lambda p: position_needs[p]["net"])

    return {"status": "success", "data": {
        "team": team,
        "needs": position_needs,
        "priority_positions": priority[:5],
        "analysis": f"Team has {len(priority)} positions with transfer needs"
    }}


# =============================================================================
# PLAYER COMPARISON ENDPOINTS
# =============================================================================

@router.post("/compare/players", response_model=PlayerComparisonResponse)
async def compare_players(
    request: PlayerComparisonRequest,
    user: dict = Depends(get_current_user),
):
    """
    Compare multiple players across various metrics.
    """
    logger.info(f"Player comparison for {len(request.player_ids)} players by {user['email']}")

    return PlayerComparisonResponse(
        players=[],
        comparison_type=request.comparison_type,
        metrics={},
    )


# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================

@router.get("/config/school-tiers")
async def get_school_tiers(user: dict = Depends(get_current_user)):
    """Get school tier classifications."""
    return {
        "blue_blood": ["Alabama", "Ohio State", "USC", "Michigan", "Texas", "Oklahoma", "Notre Dame"],
        "elite": ["Georgia", "Clemson", "Oregon", "Penn State", "LSU", "Florida", "Florida State", "Tennessee"],
        # ... etc
    }


@router.get("/config/conference-tiers")
async def get_conference_tiers(user: dict = Depends(get_current_user)):
    """Get conference tier classifications."""
    return {
        "tier1": ["SEC", "Big Ten"],
        "tier2": ["Big 12", "ACC"],
        "tier3": ["American", "Mountain West", "Sun Belt", "MAC", "CUSA"],
    }
