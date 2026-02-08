"""API routes for Portal IQ.

All endpoints for NIL valuation, portal intelligence, draft projections,
and roster optimization.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Request


def safe_float(value, default: float = 0.0) -> Optional[float]:
    """Safely convert a value to float, handling string heights like '6' 4"'."""
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        value = value.strip()
        # Handle ESPN height format like "6' 4\""
        if "'" in value:
            try:
                parts = value.replace('"', '').split("'")
                feet = int(parts[0].strip())
                inches = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip() else 0
                return float(feet * 12 + inches)
            except (ValueError, IndexError):
                return None
        # Try direct float conversion
        try:
            return float(value)
        except ValueError:
            return None
    return default

# Import S3/R2 data loader for production data
from ..utils.s3_loader import (
    load_nil_data,
    load_nil_data_enriched,
    load_portal_data,
    load_portal_data_enriched,
    load_pff_grades,
    load_rosters,
    load_cfbd_stats,
    load_pff_stat,
    get_s3_diagnostics,
)

from .schemas import (
    # Base
    APIResponse,
    # NIL
    NILPredictRequest,
    NILPredictResponse,
    NILValueBreakdown,
    TransferImpactRequest,
    TransferImpactResponse,
    MarketReportRequest,
    MarketReportResponse,
    # Portal
    FlightRiskRequest,
    FlightRiskResponse,
    TeamReportRequest,
    TeamReportResponse,
    PortalFitRequest,
    PortalFitResponse,
    PortalRecommendationsRequest,
    PortalRecommendationsResponse,
    # Draft
    DraftProjectRequest,
    DraftProjectResponse,
    MockDraftRequest,
    MockDraftResponse,
    # Roster
    RosterOptimizeRequest,
    RosterOptimizeResponse,
    ScenarioRequest,
    ScenarioResponse,
    RosterReportResponse,
)

logger = logging.getLogger("portal_iq_api")

router = APIRouter()


# =============================================================================
# Helper Functions (must be defined before endpoints that use them)
# =============================================================================

def get_models(request: Request) -> Dict[str, Any]:
    """Get loaded models from app state."""
    return request.app.state.get_models()


async def require_api_key(request: Request) -> str:
    """Require API key authentication."""
    api_key = request.headers.get("X-API-Key")
    from fastapi import HTTPException

    # Get valid keys from environment only - no hardcoded keys in production
    import os
    from dotenv import load_dotenv
    load_dotenv()

    environment = os.getenv("ENVIRONMENT", "development")
    keys_env = os.getenv("PORTAL_IQ_API_KEYS", "")

    valid_keys = set()
    if keys_env:
        valid_keys.update(k.strip() for k in keys_env.split(",") if k.strip())

    # Only allow dev key in development mode
    if environment != "production" and not valid_keys:
        valid_keys.add("dev-key-123")

    if not api_key:
        raise HTTPException(status_code=401, detail={"error": "Missing API key", "message": "Include X-API-Key header"})
    if not valid_keys:
        raise HTTPException(status_code=503, detail={"error": "API keys not configured", "message": "PORTAL_IQ_API_KEYS environment variable is required"})
    if api_key not in valid_keys:
        raise HTTPException(status_code=401, detail={"error": "Invalid API key", "message": "The provided API key is not valid"})
    return api_key


def player_to_dataframe(player_data: Dict[str, Any]) -> pd.DataFrame:
    """Convert player profile dict to DataFrame for model input."""
    # Flatten nested structures
    flat_data = {
        "name": player_data.get("name"),
        "player_name": player_data.get("name"),
        "school": player_data.get("school"),
        "position": player_data.get("position"),
        "class_year": player_data.get("class_year", "Junior"),
        "eligibility_remaining": player_data.get("eligibility_remaining", 2),
        "overall_rating": player_data.get("overall_rating", 0.75),
        "is_starter": player_data.get("is_starter", True),
    }

    # Flatten stats
    if player_data.get("stats"):
        for key, value in player_data["stats"].items():
            flat_data[key] = value

    # Flatten social media
    if player_data.get("social_media"):
        for key, value in player_data["social_media"].items():
            flat_data[key] = value

    # Flatten recruiting
    if player_data.get("recruiting"):
        for key, value in player_data["recruiting"].items():
            flat_data[key] = value

    # Flatten measurables
    if player_data.get("measurables"):
        for key, value in player_data["measurables"].items():
            flat_data[key] = value

    return pd.DataFrame([flat_data])


# =============================================================================
# Debug Endpoints
# =============================================================================

@router.get(
    "/debug/s3",
    tags=["Debug"],
    summary="S3/R2 diagnostics",
    description="Check S3/R2 connection status and available files.",
)
async def debug_s3():
    """Debug endpoint to verify R2/S3 connection and data availability."""
    return get_s3_diagnostics()


@router.post(
    "/debug/clear-cache",
    tags=["Debug"],
    summary="Clear S3 data cache",
    description="Clear the in-memory S3 data cache to force reload from R2.",
)
async def clear_cache(api_key: str = Depends(require_api_key)):
    """Clear the S3 data cache to force reload fresh data from R2."""
    from ..utils.s3_loader import get_s3_loader
    loader = get_s3_loader()
    loader.clear_cache()
    return {
        "status": "success",
        "message": "S3 data cache cleared. Next request will reload from R2.",
    }


@router.get(
    "/stats/database",
    response_model=APIResponse,
    tags=["Stats"],
    summary="Database statistics",
    description="Get summary statistics about all data in the system.",
)
async def database_stats(
    request: Request,
    api_key: str = Depends(require_api_key),
):
    """Get database-wide statistics like total players, portal entries, etc."""
    from datetime import datetime

    stats = {
        "total_players": 0,
        "portal_players": 0,
        "new_portal_today": 0,
        "nil_valuations": 0,
        "schools": 0,
        "pff_records": 0,
        "models_updated": "Feb 3, 2026",
        "last_updated": datetime.now().strftime("%b %d, %Y %H:%M"),
        "data_version": "3.1.0",
    }

    # Load NIL valuations
    nil_df = load_nil_data()
    if not nil_df.empty:
        stats["nil_valuations"] = len(nil_df)
        name_col = 'name' if 'name' in nil_df.columns else 'player_name'
        if name_col in nil_df.columns:
            stats["total_players"] = len(nil_df[name_col].unique())
        # Count actual vs predicted
        if "is_predicted" in nil_df.columns:
            actual_count = (~nil_df["is_predicted"]).sum()
            stats["actual_nil_values"] = int(actual_count)
            stats["predicted_nil_values"] = len(nil_df) - int(actual_count)

    # Load portal data
    portal_df = load_portal_data()
    if not portal_df.empty:
        stats["portal_players"] = len(portal_df)
        # Count schools
        school_cols = ['from_school', 'to_school', 'origin_school', 'destination_school']
        schools = set()
        for col in school_cols:
            if col in portal_df.columns:
                schools.update(portal_df[col].dropna().unique())
        stats["schools"] = len(schools)
        # Count entries in last 24 hours
        if "commit_date" in portal_df.columns:
            today = datetime.now().strftime("%Y-%m-%d")
            stats["new_portal_today"] = len(portal_df[portal_df["commit_date"].astype(str).str.startswith(today)])

    # Load PFF grades
    pff_df = load_pff_grades()
    if not pff_df.empty:
        stats["pff_records"] = len(pff_df)

    return APIResponse(
        status="success",
        data=stats,
        message="Database statistics retrieved successfully"
    )


@router.get(
    "/pff/{player_name}",
    response_model=APIResponse,
    tags=["PFF"],
    summary="Get PFF stats for a player",
    description="Get detailed PFF statistics for a specific player.",
)
async def get_player_pff(
    request: Request,
    player_name: str,
    season: int = 2025,
    api_key: str = Depends(require_api_key),
):
    """Get comprehensive PFF stats for a specific player."""
    result = {
        "name": player_name,
        "season": season,
        "grades": None,
        "passing": None,
        "rushing": None,
        "receiving": None,
        "defense": None,
        "pass_rush": None,
    }

    # Load main PFF grades
    pff_df = load_pff_grades()
    if not pff_df.empty:
        name_col = 'name' if 'name' in pff_df.columns else 'player_name'
        if name_col in pff_df.columns:
            match = pff_df[pff_df[name_col].str.contains(player_name, case=False, na=False)]
            if not match.empty:
                result["grades"] = match.iloc[0].to_dict()

    # Load detailed PFF stats for each category
    for category, stat_type in [
        ("passing", "passing_summary"),
        ("rushing", "rushing_summary"),
        ("receiving", "receiving_summary"),
        ("defense", "defense_summary"),
        ("pass_rush", "pass_rush_summary"),
    ]:
        try:
            df = load_pff_stat(category, stat_type, season)
            if not df.empty:
                name_col = 'name' if 'name' in df.columns else 'player' if 'player' in df.columns else None
                if name_col:
                    match = df[df[name_col].str.contains(player_name, case=False, na=False)]
                    if not match.empty:
                        result[category] = match.iloc[0].to_dict()
        except Exception as e:
            logger.warning(f"Failed to load PFF {category} for {player_name}: {e}")

    return APIResponse(
        status="success",
        data=result,
        message=f"PFF stats for {player_name}"
    )


# =============================================================================
# NIL Endpoints
# =============================================================================

@router.post(
    "/nil/predict",
    response_model=APIResponse,
    tags=["NIL"],
    summary="Predict NIL value",
    description="Get NIL valuation prediction for a player with detailed breakdown.",
)
async def predict_nil(
    request: Request,
    body: NILPredictRequest,
    api_key: str = Depends(require_api_key),
):
    """Predict NIL value for a player.

    This is the primary endpoint PlaymakerVC calls to show NIL data on client profiles.
    """
    models = get_models(request)
    nil_valuator = models.get("nil_valuator")

    player_dict = body.player.model_dump()

    if nil_valuator is not None:
        try:
            player_df = player_to_dataframe(player_dict)
            predictions = nil_valuator.predict(player_df)

            if predictions and len(predictions) > 0:
                pred = predictions[0]

                response_data = NILPredictResponse(
                    player_name=body.player.name,
                    school=body.player.school,
                    position=body.player.position,
                    predicted_value=pred.get("predicted_value", 0),
                    value_tier=pred.get("tier", "moderate"),
                    tier_probabilities=pred.get("tier_probabilities", {}),
                    confidence=pred.get("confidence", 0.7),
                    value_breakdown=NILValueBreakdown(
                        base_value=pred.get("value_breakdown", {}).get("base_value", 0),
                        social_media_premium=pred.get("value_breakdown", {}).get("social_premium", 0),
                        school_brand_factor=pred.get("value_breakdown", {}).get("school_factor", 0),
                        position_market_factor=pred.get("value_breakdown", {}).get("position_factor", 0),
                        draft_potential_premium=pred.get("value_breakdown", {}).get("draft_premium", 0),
                    ),
                    comparable_players=pred.get("comparable_players", []),
                    percentile=pred.get("percentile"),
                )

                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.warning(f"ML NIL prediction failed: {e}, falling back to CustomNILValuator")
            # Fall through to CustomNILValuator below

    # Use CustomNILValuator for formula-based valuation (primary method or fallback)
    try:
        from ..models.custom_nil_valuator import CustomNILValuator

        custom_valuator = CustomNILValuator()

        # Extract stats - handle None values
        stats = player_dict.get("stats") or {}
        social = player_dict.get("social_media") or {}
        recruiting = player_dict.get("recruiting") or {}

        val = custom_valuator.calculate_valuation(
            player_name=player_dict.get("name", "Unknown"),
            position=player_dict.get("position", "ATH"),
            school=player_dict.get("school", "Unknown"),
            conference=player_dict.get("conference"),
            games_played=stats.get("games_played", 0),
            games_started=stats.get("games_started", 0),
            passing_yards=stats.get("passing_yards", 0),
            passing_tds=stats.get("passing_tds", 0),
            rushing_yards=stats.get("rushing_yards", 0),
            rushing_tds=stats.get("rushing_tds", 0),
            receiving_yards=stats.get("receiving_yards", 0),
            receiving_tds=stats.get("receiving_tds", 0),
            tackles=stats.get("tackles", 0),
            sacks=stats.get("sacks", 0),
            interceptions=stats.get("interceptions", 0),
            instagram_followers=social.get("instagram_followers", 0),
            twitter_followers=social.get("twitter_followers", 0),
            tiktok_followers=social.get("tiktok_followers", 0),
            recruiting_stars=recruiting.get("stars", 0),
            national_rank=recruiting.get("national_rank"),
            is_starter=player_dict.get("is_starter", True),
        )

        response_data = NILPredictResponse(
            player_name=body.player.name,
            school=body.player.school,
            position=body.player.position,
            predicted_value=val.total_valuation,
            value_tier=val.valuation_tier,
            tier_probabilities={val.valuation_tier: 0.8},
            confidence=0.75 if val.confidence == "high" else 0.6 if val.confidence == "medium" else 0.4,
            value_breakdown=NILValueBreakdown(
                base_value=val.factors.get("position_base", 0),
                social_media_premium=val.social_value,
                school_brand_factor=val.market_value - val.performance_value,
                position_market_factor=val.performance_value,
                draft_potential_premium=val.potential_value,
            ),
            comparable_players=[],
            percentile=50.0,
        )

        return APIResponse(
            status="success",
            data=response_data.model_dump(),
            message="Valuation from CustomNILValuator (performance-based)",
        )

    except Exception as e:
        import traceback
        logger.error(f"CustomNILValuator error: {e}\n{traceback.format_exc()}")

        # Final fallback to simple demo calculation
        demo_value = _calculate_demo_nil_value(player_dict)

        response_data = NILPredictResponse(
            player_name=body.player.name,
            school=body.player.school,
            position=body.player.position,
            predicted_value=demo_value,
            value_tier=_get_nil_tier(demo_value),
            tier_probabilities={"moderate": 0.6, "solid": 0.3, "entry": 0.1},
            confidence=0.65,
            value_breakdown=NILValueBreakdown(
                base_value=demo_value * 0.4,
                social_media_premium=demo_value * 0.2,
                school_brand_factor=demo_value * 0.2,
                position_market_factor=demo_value * 0.15,
                draft_potential_premium=demo_value * 0.05,
            ),
            comparable_players=[],
            percentile=50.0,
        )

        return APIResponse(
            status="success",
            data=response_data.model_dump(),
            message="Demo mode - fallback calculation",
        )


@router.post(
    "/nil/transfer-impact",
    response_model=APIResponse,
    tags=["NIL"],
    summary="Analyze transfer impact on NIL",
    description="Compare current NIL value vs projected value at a target school.",
)
async def transfer_impact(
    request: Request,
    body: TransferImpactRequest,
    api_key: str = Depends(require_api_key),
):
    """Analyze how transferring would impact a player's NIL value."""
    models = get_models(request)
    nil_valuator = models.get("nil_valuator")

    player_dict = body.player.model_dump()

    if nil_valuator is not None:
        try:
            result = nil_valuator.transfer_impact(
                player_to_dataframe(player_dict),
                body.target_school,
            )

            if result:
                response_data = TransferImpactResponse(
                    player_name=body.player.name,
                    current_school=body.player.school,
                    target_school=body.target_school,
                    current_value=result.get("current_value", 0),
                    projected_value=result.get("projected_value", 0),
                    value_change=result.get("value_change", 0),
                    value_change_pct=result.get("value_change_pct", 0),
                    factors=result.get("factors", {}),
                    recommendation=result.get("recommendation", ""),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Transfer impact error: {e}")

    # Demo fallback
    current = _calculate_demo_nil_value(player_dict)
    target_mult = _get_school_multiplier(body.target_school)
    current_mult = _get_school_multiplier(body.player.school)
    projected = current * (target_mult / current_mult) if current_mult else current

    response_data = TransferImpactResponse(
        player_name=body.player.name,
        current_school=body.player.school,
        target_school=body.target_school,
        current_value=current,
        projected_value=projected,
        value_change=projected - current,
        value_change_pct=((projected - current) / current * 100) if current else 0,
        factors={
            "market_size": "Market size adjustment",
            "program_brand": "Program brand factor",
        },
        recommendation="Transfer analysis based on market factors",
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode",
    )


@router.get(
    "/nil/leaderboard",
    response_model=APIResponse,
    tags=["NIL"],
    summary="NIL Leaderboard",
    description="Get top players ranked by NIL valuation.",
)
async def nil_leaderboard(
    request: Request,
    limit: int = 100,
    position: Optional[str] = None,
    conference: Optional[str] = None,
    tier: Optional[str] = None,
    enriched: bool = True,
    api_key: str = Depends(require_api_key),
):
    """Get NIL leaderboard with optional filters.

    Args:
        enriched: If True, includes PFF grades, CFBD stats, headshots, and measurables
    """
    # Load from R2/S3 with full enrichment (headshots, PFF, CFBD stats)
    df = load_nil_data_enriched() if enriched else load_nil_data()

    if df.empty:
        return APIResponse(
            status="error",
            message="No NIL data available. Check R2 connection or run sync_to_r2.py.",
            data={"players": [], "total": 0}
        )

    try:
        # Normalize column names - handle different CSV formats
        value_col = None
        for col in ['custom_nil_value', 'nil_value', 'nil_valuation', 'valuation']:
            if col in df.columns:
                value_col = col
                break
        if not value_col:
            value_col = 'custom_nil_value'  # default

        # Apply filters
        if position and 'position' in df.columns:
            df = df[df['position'].str.upper() == position.upper()]
        if conference and 'conference' in df.columns:
            df = df[df['conference'].str.lower() == conference.lower()]
        if tier and 'nil_tier' in df.columns:
            df = df[df['nil_tier'] == tier.lower()]

        # Sort by value descending
        if value_col in df.columns:
            df = df.sort_values(value_col, ascending=False)

        # Capture total count BEFORE limiting
        total_count = len(df)

        # Limit results
        df = df.head(limit)

        # Map column names to match frontend NILLeaderboardPlayer interface
        rename_map = {'valuation_confidence': 'confidence'}
        if value_col and value_col != 'valuation':
            rename_map[value_col] = 'valuation'
        df = df.rename(columns=rename_map)

        # Ensure player_name exists (some CSVs may have 'name' instead)
        if 'name' in df.columns and 'player_name' not in df.columns:
            df = df.rename(columns={'name': 'player_name'})

        # Build player list with all enriched data
        players = []
        for idx, row in df.iterrows():
            player = {
                "rank": idx + 1,
                "player_id": str(row.get('player_id', idx)),
                "player_name": row.get('player_name', 'Unknown'),
                "position": row.get('position', 'Unknown'),
                "school": row.get('school', 'Unknown'),
                "valuation": float(row.get('valuation', 0) or 0),
                "nil_tier": row.get('nil_tier', 'unknown'),
            }

            # Add optional fields
            if 'stars' in row and pd.notna(row.get('stars')):
                player["stars"] = int(row['stars'])
            if 'headshot_url' in row and pd.notna(row.get('headshot_url')):
                player["headshot_url"] = row['headshot_url']
            if 'conference' in row and pd.notna(row.get('conference')):
                player["conference"] = row['conference']

            # Add measurables (from enrichment) - safe conversion for string heights
            height_val = safe_float(row.get('height'))
            if height_val is not None:
                player["height"] = height_val
            weight_val = safe_float(row.get('weight'))
            if weight_val is not None:
                player["weight"] = weight_val

            # Add PFF grades (from enrichment)
            if 'pff_overall' in row and pd.notna(row.get('pff_overall')):
                player["pff_overall"] = float(row['pff_overall'])
            if 'pff_offense' in row and pd.notna(row.get('pff_offense')):
                player["pff_offense"] = float(row['pff_offense'])
            if 'pff_defense' in row and pd.notna(row.get('pff_defense')):
                player["pff_defense"] = float(row['pff_defense'])

            # Add CFBD stats (from enrichment)
            for stat in ['passing_yards', 'passing_tds', 'rushing_yards', 'rushing_tds',
                         'receiving_yards', 'receiving_tds', 'tackles', 'sacks']:
                if stat in row and pd.notna(row.get(stat)):
                    player[stat] = float(row[stat])

            # Add valuation breakdown if available
            if 'performance_value' in row and pd.notna(row.get('performance_value')):
                player["performance_value"] = float(row['performance_value'])
            if 'market_value' in row and pd.notna(row.get('market_value')):
                player["market_value"] = float(row['market_value'])
            if 'social_value' in row and pd.notna(row.get('social_value')):
                player["social_value"] = float(row['social_value'])

            players.append(player)

        return APIResponse(
            status="success",
            data={
                "players": players,
                "total": total_count,
                "filters_applied": {
                    "position": position,
                    "conference": conference,
                    "tier": tier,
                }
            }
        )

    except Exception as e:
        logger.error(f"Leaderboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/nil/market-report",
    response_model=APIResponse,
    tags=["NIL"],
    summary="NIL market report",
    description="Get market overview with average values, top players, and trends.",
)
async def market_report(
    request: Request,
    body: MarketReportRequest,
    api_key: str = Depends(require_api_key),
):
    """Generate NIL market report with optional position/conference filters."""
    # Load from R2/S3 with local fallback
    df = load_nil_data()

    if not df.empty:
        try:
            # Normalize value column name
            value_col = None
            for col in ['custom_nil_value', 'nil_value', 'nil_valuation', 'valuation']:
                if col in df.columns:
                    value_col = col
                    break
            if not value_col:
                value_col = 'custom_nil_value'

            # Apply filters
            filters = {}
            if body.position and 'position' in df.columns:
                df = df[df['position'].str.upper() == body.position.upper()]
                filters["position"] = body.position
            if body.conference and 'conference' in df.columns:
                df = df[df['conference'].str.lower() == body.conference.lower()]
                filters["conference"] = body.conference

            # Calculate stats
            total_players = len(df)
            average_value = df[value_col].mean() if total_players > 0 and value_col in df.columns else 0
            median_value = df[value_col].median() if total_players > 0 and value_col in df.columns else 0
            total_market_value = df[value_col].sum() if value_col in df.columns else 0

            # Value by tier
            value_by_tier = {}
            if 'nil_tier' in df.columns and value_col in df.columns:
                for tier in df['nil_tier'].unique():
                    tier_df = df[df['nil_tier'] == tier]
                    value_by_tier[tier] = {
                        "count": len(tier_df),
                        "avg_value": tier_df[value_col].mean()
                    }

            # Top players (map to frontend expected fields)
            top_df = df.nlargest(25, value_col) if value_col in df.columns else df.head(25)
            top_players = []
            for _, row in top_df.iterrows():
                player = {
                    "name": row.get('player_name', row.get('name', 'Unknown')),
                    "school": row.get('school', 'Unknown'),
                    "position": row.get('position', 'Unknown'),
                    "value": row.get(value_col, 0) if value_col else 0,
                }
                # Add optional fields if they exist
                if 'espn_headshot_url' in row and pd.notna(row['espn_headshot_url']):
                    player["headshot_url"] = row['espn_headshot_url']
                if 'nil_tier' in row:
                    player["tier"] = row['nil_tier']
                top_players.append(player)

            response_data = MarketReportResponse(
                filters_applied=filters,
                total_players=total_players,
                average_value=average_value,
                median_value=median_value,
                total_market_value=total_market_value,
                value_by_tier=value_by_tier,
                top_players=top_players,
                market_trends=[
                    f"Total market value: ${total_market_value:,.0f}",
                    f"Average player value: ${average_value:,.0f}",
                    f"Top valued positions: QB, WR, EDGE",
                ],
            )

            return APIResponse(
                status="success",
                data=response_data.model_dump(),
                message="Real data from valuations",
            )

        except Exception as e:
            logger.error(f"Market report CSV error: {e}")

    # Demo fallback if no CSV available
    models = get_models(request)
    nil_valuator = models.get("nil_valuator")

    if nil_valuator is not None:
        try:
            report = nil_valuator.generate_position_market_report(
                position=body.position,
                conference=body.conference,
            )
            if report:
                return APIResponse(status="success", data=report)
        except Exception as e:
            logger.error(f"Market report error: {e}")

    # Final demo fallback
    filters = {}
    if body.position:
        filters["position"] = body.position
    if body.conference:
        filters["conference"] = body.conference

    response_data = MarketReportResponse(
        filters_applied=filters,
        total_players=500,
        average_value=185000,
        median_value=75000,
        total_market_value=92500000,
        value_by_tier={
            "mega": {"count": 15, "avg_value": 1500000},
            "premium": {"count": 50, "avg_value": 600000},
            "solid": {"count": 100, "avg_value": 175000},
            "moderate": {"count": 150, "avg_value": 50000},
            "entry": {"count": 185, "avg_value": 15000},
        },
        top_players=[
            {"name": "Top QB", "school": "Georgia", "position": "QB", "value": 2500000},
            {"name": "Star WR", "school": "Ohio State", "position": "WR", "value": 1800000},
        ],
        market_trends=[
            "QB values increased 18% year-over-year",
            "Social media following driving premium valuations",
            "Blue blood schools command 2-3x market premium",
        ],
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode - run generate_nil_valuations.py for real data",
    )


# =============================================================================
# Portal Endpoints
# =============================================================================

@router.get(
    "/portal/active",
    response_model=APIResponse,
    tags=["Portal"],
    summary="Active portal players",
    description="Get list of players currently in the transfer portal.",
)
async def portal_active(
    request: Request,
    status: Optional[str] = None,
    position: Optional[str] = None,
    limit: int = 100,
    enriched: bool = True,
    api_key: str = Depends(require_api_key),
):
    """Get active portal players with optional filters.

    Args:
        enriched: If True, includes PFF grades, CFBD stats, headshots, and measurables
    """
    # Load from R2/S3 with full enrichment (headshots, PFF, CFBD stats)
    df = load_portal_data_enriched() if enriched else load_portal_data()

    if df.empty:
        return APIResponse(
            status="error",
            message="No portal data available. Check R2 connection.",
            data={"players": [], "total": 0}
        )

    try:

        # Apply filters
        if status and status.lower() != "all":
            if 'status' in df.columns:
                df = df[df['status'].str.lower() == status.lower()]
        if position:
            if 'position' in df.columns:
                df = df[df['position'].str.upper() == position.upper()]

        # Sort by NIL valuation or stars if available
        if 'nil_valuation' in df.columns:
            df = df.sort_values('nil_valuation', ascending=False)
        elif 'stars' in df.columns:
            df = df.sort_values('stars', ascending=False)

        # Capture total count BEFORE limiting
        total_count = len(df)

        # Limit results
        df = df.head(limit)

        # Map columns to match frontend PortalPlayer interface expectations
        players = []
        for idx, row in df.iterrows():
            # Determine status - map to frontend expected values
            raw_status = str(row.get('status', 'Active')).lower() if pd.notna(row.get('status')) else 'active'
            if 'committed' in raw_status:
                mapped_status = 'committed'
            elif 'withdrawn' in raw_status:
                mapped_status = 'withdrawn'
            else:
                mapped_status = 'available'

            player = {
                "player_id": str(idx),
                "player_name": row.get('name', row.get('player_name', 'Unknown')),
                "position": row.get('position', 'Unknown'),
                "origin_school": row.get('origin_school', row.get('from_school', row.get('school', 'Unknown'))),
                "destination_school": row.get('destination_school', row.get('to_school', None)) if pd.notna(row.get('destination_school', row.get('to_school'))) else None,
                "status": mapped_status,
                "nil_valuation": float(row.get('nil_value', row.get('nil_valuation', row.get('custom_nil_value', 0))) or 0),
                "stars": int(row.get('stars', 0) or 0),
            }
            # Add optional fields - headshots
            if 'headshot_url' in row and pd.notna(row.get('headshot_url')):
                player["headshot_url"] = row['headshot_url']
            if 'class_year' in row and pd.notna(row.get('class_year')):
                player["class_year"] = str(row['class_year'])
            if 'commit_date' in row and pd.notna(row.get('commit_date')):
                player["entry_date"] = str(row['commit_date'])

            # Add measurables (from enrichment) - safe conversion for string heights
            height_val = safe_float(row.get('height'))
            if height_val is not None:
                player["height"] = height_val
            weight_val = safe_float(row.get('weight'))
            if weight_val is not None:
                player["weight"] = weight_val

            # Add PFF grades (from enrichment)
            if 'pff_overall' in row and pd.notna(row.get('pff_overall')):
                player["pff_overall"] = float(row['pff_overall'])
            if 'pff_offense' in row and pd.notna(row.get('pff_offense')):
                player["pff_offense"] = float(row['pff_offense'])
            if 'pff_defense' in row and pd.notna(row.get('pff_defense')):
                player["pff_defense"] = float(row['pff_defense'])

            # Add CFBD stats (from enrichment) - offense
            for stat in ['passing_yards', 'passing_tds', 'rushing_yards', 'rushing_tds', 'receiving_yards', 'receiving_tds', 'receptions']:
                if stat in row and pd.notna(row.get(stat)):
                    player[stat] = float(row[stat])

            # Add CFBD stats (from enrichment) - defense
            for stat in ['tackles', 'sacks', 'tackles_for_loss', 'passes_defended']:
                if stat in row and pd.notna(row.get(stat)):
                    player[stat] = float(row[stat])

            players.append(player)

        return APIResponse(
            status="success",
            data={
                "players": players,
                "total": total_count,
                "source": "r2/on3_transfer_portal.csv",
                "filters_applied": {
                    "status": status,
                    "position": position,
                }
            }
        )

    except Exception as e:
        logger.error(f"Portal active error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/portal/flight-risk",
    response_model=APIResponse,
    tags=["Portal"],
    summary="Predict flight risk",
    description="Predict probability a player enters the transfer portal.",
)
async def flight_risk(
    request: Request,
    body: FlightRiskRequest,
    api_key: str = Depends(require_api_key),
):
    """Predict flight risk for a player."""
    models = get_models(request)
    portal_predictor = models.get("portal_predictor")

    player_dict = body.player.model_dump()
    if body.team_context:
        player_dict.update(body.team_context)

    if portal_predictor is not None:
        try:
            predictions = portal_predictor.predict_flight_risk(
                player_to_dataframe(player_dict)
            )

            if predictions and len(predictions) > 0:
                pred = predictions[0]

                response_data = FlightRiskResponse(
                    player_name=body.player.name,
                    school=body.player.school,
                    flight_risk_probability=pred.get("flight_risk_probability", 0.3),
                    risk_level=pred.get("risk_level", "moderate"),
                    risk_factors=pred.get("risk_factors", []),
                    retention_recommendations=pred.get("retention_recommendations", []),
                    estimated_replacement_cost=pred.get("replacement_cost", 100000),
                    comparable_transfers=pred.get("comparable_transfers", []),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Flight risk error: {e}")

    # Demo fallback
    risk_prob = 0.35
    if body.team_context and body.team_context.get("recent_coaching_change"):
        risk_prob += 0.2

    response_data = FlightRiskResponse(
        player_name=body.player.name,
        school=body.player.school,
        flight_risk_probability=risk_prob,
        risk_level="moderate" if risk_prob < 0.5 else "high",
        risk_factors=[
            {"factor": "playing_time", "impact": 0.15},
            {"factor": "nil_market", "impact": 0.10},
        ],
        retention_recommendations=[
            "Ensure competitive NIL compensation",
            "Discuss role in upcoming season",
        ],
        estimated_replacement_cost=150000,
        comparable_transfers=[],
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode",
    )


@router.post(
    "/portal/team-report",
    response_model=APIResponse,
    tags=["Portal"],
    summary="Team flight risk report",
    description="Get comprehensive flight risk analysis for entire roster.",
)
async def team_report(
    request: Request,
    body: TeamReportRequest,
    api_key: str = Depends(require_api_key),
):
    """Generate team-wide flight risk report."""
    models = get_models(request)
    portal_predictor = models.get("portal_predictor")

    if portal_predictor is not None:
        try:
            # Would need roster data - using placeholder
            report = portal_predictor.team_flight_risk_report(
                pd.DataFrame(),  # Would load from database
                body.school,
            )
            if report:
                return APIResponse(status="success", data=report)
        except Exception as e:
            logger.error(f"Team report error: {e}")

    # Demo fallback
    response_data = TeamReportResponse(
        school=body.school,
        analysis_date=datetime.utcnow(),
        total_roster_size=85,
        total_at_risk=8,
        critical_risk_players=[
            {"name": "WR1", "position": "WR", "risk": 0.78, "nil_value": 200000},
        ],
        high_risk_players=[
            {"name": "CB2", "position": "CB", "risk": 0.62, "nil_value": 150000},
            {"name": "RB1", "position": "RB", "risk": 0.58, "nil_value": 120000},
        ],
        estimated_wins_at_risk=1.8,
        total_retention_budget_needed=850000,
        position_vulnerability={
            "WR": {"count": 2, "avg_risk": 0.65},
            "CB": {"count": 2, "avg_risk": 0.55},
        },
        recommendations=[
            "Prioritize WR retention - highest flight risk position group",
            "Address CB depth concerns before portal window",
        ],
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode - provide roster data for full analysis",
    )


@router.post(
    "/portal/fit-score",
    response_model=APIResponse,
    tags=["Portal"],
    summary="Calculate portal fit",
    description="Score how well a portal player fits a target school.",
)
async def portal_fit(
    request: Request,
    body: PortalFitRequest,
    api_key: str = Depends(require_api_key),
):
    """Calculate fit score for portal player at target school."""
    models = get_models(request)
    portal_predictor = models.get("portal_predictor")

    player_dict = body.player.model_dump()

    if portal_predictor is not None:
        try:
            predictions = portal_predictor.predict_portal_fit(
                player_to_dataframe(player_dict),
                body.target_school,
            )

            if predictions and len(predictions) > 0:
                pred = predictions[0]

                response_data = PortalFitResponse(
                    player_name=body.player.name,
                    origin_school=body.player.school,
                    target_school=body.target_school,
                    fit_score=pred.get("fit_score", 0.7),
                    fit_grade=pred.get("fit_grade", "B"),
                    fit_breakdown=pred.get("fit_breakdown", {}),
                    projected_nil_at_target=pred.get("projected_nil", 100000),
                    projected_playing_time=pred.get("playing_time", "Starter"),
                    concerns=pred.get("concerns", []),
                    strengths=pred.get("strengths", []),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Portal fit error: {e}")

    # Demo fallback
    fit_score = 0.75
    response_data = PortalFitResponse(
        player_name=body.player.name,
        origin_school=body.player.school,
        target_school=body.target_school,
        fit_score=fit_score,
        fit_grade="B+" if fit_score >= 0.75 else "B",
        fit_breakdown={
            "scheme_fit": 0.80,
            "competition_level": 0.70,
            "geographic_fit": 0.75,
        },
        projected_nil_at_target=_calculate_demo_nil_value(player_dict) * _get_school_multiplier(body.target_school),
        projected_playing_time="Starter",
        concerns=["Adjustment to new system"],
        strengths=["Experience level", "Production history"],
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode",
    )


@router.post(
    "/portal/recommendations",
    response_model=APIResponse,
    tags=["Portal"],
    summary="Portal recommendations",
    description="Get ranked portal targets for a school based on needs and budget.",
)
async def portal_recommendations(
    request: Request,
    body: PortalRecommendationsRequest,
    api_key: str = Depends(require_api_key),
):
    """Get ranked portal transfer recommendations."""
    models = get_models(request)
    roster_optimizer = models.get("roster_optimizer")

    if roster_optimizer is not None:
        try:
            result = roster_optimizer.portal_shopping_list(
                school=body.school,
                roster_df=pd.DataFrame(),  # Would load from database
                budget_remaining=body.budget,
                positions_of_need=body.positions_of_need,
            )

            if result:
                response_data = PortalRecommendationsResponse(
                    school=body.school,
                    budget=body.budget,
                    targets=result.get("shopping_list", [])[:body.max_targets],
                    positions_prioritized=result.get("positions_prioritized", []),
                    budget_allocation_suggestion=result.get("position_needs", {}),
                    projected_roster_improvement=result.get("projected_improvement", 0),
                    acquisition_strategy=result.get("budget_strategy", ""),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Portal recommendations error: {e}")

    # Demo fallback
    positions = body.positions_of_need or ["QB", "EDGE", "CB"]

    demo_targets = []
    for i, pos in enumerate(positions[:5]):
        demo_targets.append({
            "name": f"Portal Target {i+1}",
            "position": pos,
            "origin_school": "Previous School",
            "projected_nil": body.budget * (0.3 - i * 0.05),
            "fit_score": 0.85 - i * 0.05,
            "win_impact": 0.8 - i * 0.1,
            "value_rating": 0.9 - i * 0.1,
        })

    response_data = PortalRecommendationsResponse(
        school=body.school,
        budget=body.budget,
        targets=demo_targets,
        positions_prioritized=positions,
        budget_allocation_suggestion={pos: body.budget / len(positions) for pos in positions},
        projected_roster_improvement=1.5,
        acquisition_strategy="Focus on elite talent at positions of need",
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode",
    )


# =============================================================================
# Draft Endpoints
# =============================================================================

@router.post(
    "/draft/project",
    response_model=APIResponse,
    tags=["Draft"],
    summary="Project draft position",
    description="Get NFL draft projection with contract and earnings estimates.",
)
async def draft_project(
    request: Request,
    body: DraftProjectRequest,
    api_key: str = Depends(require_api_key),
):
    """Project draft position and NFL value for a player."""
    models = get_models(request)
    draft_projector = models.get("draft_projector")

    player_dict = body.player.model_dump()

    if draft_projector is not None:
        try:
            predictions = draft_projector.predict(player_to_dataframe(player_dict))

            if predictions and len(predictions) > 0:
                pred = predictions[0]

                response_data = DraftProjectResponse(
                    player_name=body.player.name,
                    position=body.player.position,
                    draft_eligible=pred.get("draft_eligible", True),
                    projected_round=pred.get("projected_round"),
                    projected_pick_range=pred.get("projected_pick_range"),
                    draft_probability=pred.get("draft_probability", 0.5),
                    draft_grade=pred.get("draft_grade", "B"),
                    expected_draft_value=pred.get("expected_draft_value", 500),
                    rookie_contract_estimate=pred.get("rookie_contract", 5000000),
                    career_earnings_estimate=pred.get("career_earnings", 25000000),
                    strengths=pred.get("strengths", []),
                    weaknesses=pred.get("weaknesses", []),
                    comparable_prospects=pred.get("comparables", []),
                    stock_trend=pred.get("stock_trend", "stable"),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Draft projection error: {e}")

    # Demo fallback
    draft_prob = 0.4
    if player_dict.get("overall_rating", 0.75) >= 0.90:
        draft_prob = 0.85
    elif player_dict.get("overall_rating", 0.75) >= 0.85:
        draft_prob = 0.6

    response_data = DraftProjectResponse(
        player_name=body.player.name,
        position=body.player.position,
        draft_eligible=body.player.class_year in ["Junior", "Senior"],
        projected_round=3 if draft_prob > 0.5 else None,
        projected_pick_range="65-100" if draft_prob > 0.5 else None,
        draft_probability=draft_prob,
        draft_grade="B" if draft_prob > 0.5 else "C",
        expected_draft_value=500 if draft_prob > 0.5 else 100,
        rookie_contract_estimate=5000000 if draft_prob > 0.5 else 0,
        career_earnings_estimate=25000000 if draft_prob > 0.5 else 0,
        strengths=["Production", "Experience"],
        weaknesses=["Athleticism testing needed"],
        comparable_prospects=[],
        stock_trend="stable",
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode",
    )


@router.post(
    "/draft/mock",
    response_model=APIResponse,
    tags=["Draft"],
    summary="Generate mock draft",
    description="Generate full mock draft board for specified year and rounds.",
)
async def mock_draft(
    request: Request,
    body: MockDraftRequest,
    api_key: str = Depends(require_api_key),
):
    """Generate mock draft board."""
    models = get_models(request)
    draft_projector = models.get("draft_projector")

    if draft_projector is not None:
        try:
            result = draft_projector.generate_mock_draft(
                season_year=body.season_year,
                num_rounds=body.num_rounds,
            )

            if result:
                response_data = MockDraftResponse(
                    season_year=body.season_year,
                    num_rounds=body.num_rounds,
                    total_picks=result.get("total_picks", 0),
                    draft_board=result.get("draft_board", []),
                    position_distribution=result.get("position_distribution", {}),
                    top_prospects_by_position=result.get("top_by_position", {}),
                    generated_at=datetime.utcnow(),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Mock draft error: {e}")

    # Demo fallback
    picks_per_round = 32
    total_picks = body.num_rounds * picks_per_round

    demo_board = []
    positions = ["QB", "WR", "CB", "EDGE", "OT", "DT", "LB", "S", "RB", "TE"]
    for i in range(min(total_picks, 50)):  # Limit demo to 50 picks
        demo_board.append({
            "pick": i + 1,
            "round": (i // picks_per_round) + 1,
            "player": f"Prospect {i + 1}",
            "position": positions[i % len(positions)],
            "school": "University",
            "grade": "A" if i < 10 else "B" if i < 32 else "C",
        })

    response_data = MockDraftResponse(
        season_year=body.season_year,
        num_rounds=body.num_rounds,
        total_picks=total_picks,
        draft_board=demo_board,
        position_distribution={"QB": 5, "WR": 8, "CB": 6, "EDGE": 5},
        top_prospects_by_position={},
        generated_at=datetime.utcnow(),
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode",
    )


# =============================================================================
# Roster Endpoints
# =============================================================================

@router.post(
    "/roster/optimize",
    response_model=APIResponse,
    tags=["Roster"],
    summary="Optimize NIL budget",
    description="Get optimal NIL budget allocation across roster.",
)
async def roster_optimize(
    request: Request,
    body: RosterOptimizeRequest,
    api_key: str = Depends(require_api_key),
):
    """Optimize NIL budget allocation."""
    models = get_models(request)
    roster_optimizer = models.get("roster_optimizer")

    if roster_optimizer is not None:
        try:
            result = roster_optimizer.optimize_nil_budget(
                school=body.school,
                total_budget=body.total_budget,
                roster_df=pd.DataFrame(),  # Would load from database
                win_target=body.win_target,
            )

            if result:
                response_data = RosterOptimizeResponse(
                    school=body.school,
                    total_budget=body.total_budget,
                    total_allocated=result.get("total_allocated", 0),
                    budget_remaining=result.get("budget_remaining", 0),
                    expected_wins=result.get("expected_wins", 0),
                    optimization_status=result.get("optimization_status", "unknown"),
                    allocations=result.get("allocations", []),
                    position_breakdown=result.get("position_breakdown", {}),
                    retention_priorities=result.get("retention_priority", []),
                    efficiency_score=result.get("budget_efficiency", 0),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Roster optimization error: {e}")

    # Demo fallback
    allocated = body.total_budget * 0.92

    demo_allocations = [
        {"player": "QB1", "position": "QB", "recommended_nil": body.total_budget * 0.18},
        {"player": "WR1", "position": "WR", "recommended_nil": body.total_budget * 0.10},
        {"player": "EDGE1", "position": "EDGE", "recommended_nil": body.total_budget * 0.08},
    ]

    response_data = RosterOptimizeResponse(
        school=body.school,
        total_budget=body.total_budget,
        total_allocated=allocated,
        budget_remaining=body.total_budget - allocated,
        expected_wins=body.win_target or 9.0,
        optimization_status="demo",
        allocations=demo_allocations,
        position_breakdown={
            "QB": body.total_budget * 0.20,
            "WR": body.total_budget * 0.15,
            "EDGE": body.total_budget * 0.12,
        },
        retention_priorities=["QB1", "WR1"],
        efficiency_score=0.85,
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode - provide roster data for full optimization",
    )


@router.post(
    "/roster/scenario",
    response_model=APIResponse,
    tags=["Roster"],
    summary="Scenario analysis",
    description="Analyze win impact of roster changes (adds/removes).",
)
async def roster_scenario(
    request: Request,
    body: ScenarioRequest,
    api_key: str = Depends(require_api_key),
):
    """Analyze win impact of roster changes."""
    models = get_models(request)
    win_model = models.get("win_model")

    if win_model is not None:
        try:
            # Convert changes to format expected by model
            additions = []
            removals = []

            for change in body.changes:
                player_data = {
                    "name": change.name,
                    "position": change.position,
                    "overall_rating": change.overall_rating,
                    "nil_cost": change.nil_cost,
                }
                if change.action == "add":
                    additions.append(player_data)
                else:
                    removals.append(player_data)

            result = win_model.scenario_analysis(
                pd.DataFrame(),  # Current roster
                body.school,
                additions=additions,
                removals=removals,
            )

            if result:
                response_data = ScenarioResponse(
                    school=body.school,
                    changes_analyzed=len(body.changes),
                    current_projected_wins=result.get("current_wins", 8),
                    new_projected_wins=result.get("new_wins", 8),
                    win_delta=result.get("win_delta", 0),
                    total_nil_cost=result.get("total_cost", 0),
                    cost_per_win=result.get("cost_per_win"),
                    position_impacts=result.get("position_impacts", {}),
                    recommendation=result.get("recommendation", ""),
                    risks=result.get("risks", []),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Scenario analysis error: {e}")

    # Demo fallback
    win_delta = 0
    total_cost = 0
    position_impacts = {}

    for change in body.changes:
        impact = (change.overall_rating - 0.75) * 2
        if change.action == "remove":
            impact = -impact
        win_delta += impact
        total_cost += change.nil_cost or 0
        position_impacts[change.position] = impact

    response_data = ScenarioResponse(
        school=body.school,
        changes_analyzed=len(body.changes),
        current_projected_wins=8.5,
        new_projected_wins=8.5 + win_delta,
        win_delta=win_delta,
        total_nil_cost=total_cost,
        cost_per_win=total_cost / win_delta if win_delta > 0 else None,
        position_impacts=position_impacts,
        recommendation="Proceed" if win_delta > 0 else "Reconsider",
        risks=["Depth concerns"] if any(c.action == "remove" for c in body.changes) else [],
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode",
    )


@router.get(
    "/roster/{school}/report",
    response_model=APIResponse,
    tags=["Roster"],
    summary="Full roster report",
    description="Get comprehensive roster analysis report for a school.",
)
async def roster_report(
    request: Request,
    school: str,
    api_key: str = Depends(require_api_key),
):
    """Generate comprehensive roster report."""
    models = get_models(request)
    roster_optimizer = models.get("roster_optimizer")

    if roster_optimizer is not None:
        try:
            result = roster_optimizer.full_roster_report(school=school)

            if result:
                response_data = RosterReportResponse(
                    school=result.get("school", school),
                    school_tier=result.get("school_tier", "p4_mid"),
                    generated_at=datetime.utcnow(),
                    executive_summary=result.get("executive_summary", []),
                    roster_summary=result.get("sections", {}).get("roster_summary", {}),
                    nil_optimization=result.get("sections", {}).get("nil_optimization", {}),
                    portal_shopping=result.get("sections", {}).get("portal_shopping", {}),
                    flight_risk=result.get("sections", {}).get("flight_risk", {}),
                    win_projection=result.get("sections", {}).get("win_projection", {}),
                    gap_analysis=result.get("sections", {}).get("gap_analysis", {}),
                    output_files=result.get("output_files", {}),
                )
                return APIResponse(status="success", data=response_data.model_dump())

        except Exception as e:
            logger.error(f"Roster report error: {e}")

    # Demo fallback
    school_tier = _get_school_tier(school)

    response_data = RosterReportResponse(
        school=school,
        school_tier=school_tier,
        generated_at=datetime.utcnow(),
        executive_summary=[
            f"Analysis for {school} ({school_tier} tier)",
            "Provide roster data for complete analysis",
        ],
        roster_summary={"message": "Requires roster data"},
        nil_optimization={"message": "Requires roster data"},
        portal_shopping={"message": "Requires roster data"},
        flight_risk={"message": "Requires roster data"},
        win_projection={"message": "Requires roster data"},
        gap_analysis={"message": "Requires roster data"},
        output_files={},
    )

    return APIResponse(
        status="success",
        data=response_data.model_dump(),
        message="Demo mode - provide roster data for full report",
    )


# =============================================================================
# Demo Helper Functions
# =============================================================================

def _calculate_demo_nil_value(player_dict: Dict[str, Any]) -> float:
    """Calculate demo NIL value based on player attributes."""
    base_value = 50000

    # Position multiplier
    position_mult = {
        "QB": 3.0, "WR": 1.5, "RB": 1.2, "TE": 1.0,
        "OT": 0.9, "OG": 0.7, "C": 0.7,
        "EDGE": 1.3, "DT": 0.9, "LB": 0.8,
        "CB": 1.2, "S": 0.9,
    }.get(player_dict.get("position", "").upper(), 1.0)

    # Rating multiplier
    rating = player_dict.get("overall_rating")
    if rating is None:
        rating = 0.75
    rating_mult = 1.0 + (rating - 0.75) * 5

    # Social media bonus
    social = player_dict.get("social_media") or {}
    followers = (
        (social.get("instagram_followers") or 0) +
        (social.get("twitter_followers") or 0) +
        (social.get("tiktok_followers") or 0)
    )
    social_bonus = min(followers / 10, 500000)  # Cap at 500k bonus

    # School multiplier
    school = player_dict.get("school", "")
    school_mult = _get_school_multiplier(school)

    return (base_value * position_mult * rating_mult * school_mult) + social_bonus


def _get_school_multiplier(school: str) -> float:
    """Get NIL multiplier based on school brand."""
    blue_bloods = ["Alabama", "Ohio State", "Georgia", "Texas", "USC", "Michigan", "Notre Dame", "Oklahoma"]
    elite = ["LSU", "Florida", "Penn State", "Oregon", "Clemson", "Tennessee", "Texas A&M"]
    power_brand = ["Miami", "Florida State", "Auburn", "Wisconsin", "Iowa", "UCLA"]

    school_clean = school.strip()
    if school_clean in blue_bloods:
        return 2.5
    elif school_clean in elite:
        return 1.8
    elif school_clean in power_brand:
        return 1.4
    else:
        return 1.0


def _get_school_tier(school: str) -> str:
    """Get school tier classification."""
    blue_bloods = ["Alabama", "Ohio State", "Georgia", "Texas", "USC", "Michigan", "Notre Dame", "Oklahoma"]
    elite = ["LSU", "Florida", "Penn State", "Oregon", "Clemson", "Tennessee", "Texas A&M"]
    power_brand = ["Miami", "Florida State", "Auburn", "Wisconsin", "Iowa", "UCLA"]

    school_clean = school.strip()
    if school_clean in blue_bloods:
        return "blue_blood"
    elif school_clean in elite:
        return "elite"
    elif school_clean in power_brand:
        return "power_brand"
    else:
        return "p4_mid"


def _get_nil_tier(value: float) -> str:
    """Get NIL tier from value."""
    if value >= 1000000:
        return "mega"
    elif value >= 500000:
        return "premium"
    elif value >= 100000:
        return "solid"
    elif value >= 25000:
        return "moderate"
    else:
        return "entry"


# =============================================================================
# AI Search Endpoints
# =============================================================================

@router.post(
    "/search",
    response_model=APIResponse,
    tags=["AI Search"],
    summary="AI-powered natural language search",
    description="Search the player database using natural language queries powered by Claude.",
)
async def ai_search(
    request: Request,
    body: dict,
    api_key: str = Depends(require_api_key),
):
    """
    Search the player database using natural language.

    Example queries:
    - "Show me 4-star QBs in the portal"
    - "Top NIL prospects from SEC schools"
    - "Undervalued players outperforming their recruiting ranking"
    - "Portal WRs with 1000+ receiving yards"
    """
    from .ai_search import get_ai_search

    query = body.get("query", "")
    max_results = body.get("max_results", 25)

    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    ai = get_ai_search()

    if not ai.is_available():
        return APIResponse(
            status="error",
            message="AI search not available - ANTHROPIC_API_KEY not configured",
            data={"results": []}
        )

    result = await ai.search(query, max_results)

    if "error" in result:
        return APIResponse(
            status="error",
            message=result["error"],
            data=result
        )

    return APIResponse(
        status="success",
        data=result,
        message=f"Found {result.get('count', 0)} results"
    )


@router.get(
    "/search/status",
    response_model=APIResponse,
    tags=["AI Search"],
    summary="Check AI search availability",
)
async def ai_search_status(
    request: Request,
    api_key: str = Depends(require_api_key),
):
    """Check if AI search is available and what data is loaded."""
    from .ai_search import get_ai_search

    ai = get_ai_search()

    datasets = {}
    for name, df in ai.data.items():
        datasets[name] = {
            "records": len(df),
            "columns": list(df.columns)[:10]
        }

    return APIResponse(
        status="success",
        data={
            "available": ai.is_available(),
            "anthropic_configured": ai.client is not None,
            "datasets_loaded": len(ai.data),
            "datasets": datasets
        }
    )


# =============================================================================
# Player Search & Details Endpoints (Steps 2-5)
# =============================================================================

@router.get(
    "/players/search",
    response_model=APIResponse,
    tags=["Players"],
    summary="Search for players",
    description="Search for players by name across NIL and portal data.",
)
async def search_players(
    request: Request,
    query: str,
    data_type: str = "all",  # "nil", "portal", or "all"
    limit: int = 25,
    api_key: str = Depends(require_api_key),
):
    """Search for players by name.

    Args:
        query: Search query (player name)
        data_type: "nil" for NIL data only, "portal" for portal only, "all" for both
        limit: Maximum results to return
    """
    results = []

    query_lower = query.lower().strip()

    if data_type in ("nil", "all"):
        df = load_nil_data_enriched()
        if not df.empty:
            name_col = "name" if "name" in df.columns else "player_name"
            if name_col in df.columns:
                matches = df[df[name_col].str.lower().str.contains(query_lower, na=False)]
                for _, row in matches.head(limit).iterrows():
                    results.append({
                        "name": row.get(name_col, "Unknown"),
                        "position": row.get("position", "Unknown"),
                        "school": row.get("school", "Unknown"),
                        "nil_value": row.get("nil_value", row.get("nil_valuation", 0)),
                        "stars": row.get("stars", row.get("recruiting_stars")),
                        "headshot_url": row.get("headshot_url"),
                        "pff_overall": row.get("pff_overall"),
                        "data_source": "nil",
                    })

    if data_type in ("portal", "all"):
        df = load_portal_data_enriched()
        if not df.empty:
            name_col = "name" if "name" in df.columns else "player_name"
            if name_col in df.columns:
                matches = df[df[name_col].str.lower().str.contains(query_lower, na=False)]
                for _, row in matches.head(limit).iterrows():
                    # Skip if already in results (from NIL data)
                    name = row.get(name_col, "Unknown")
                    if any(r["name"] == name for r in results):
                        continue
                    results.append({
                        "name": name,
                        "position": row.get("position", "Unknown"),
                        "school": row.get("origin_school", row.get("school", "Unknown")),
                        "nil_value": row.get("nil_value", row.get("nil_valuation", 0)),
                        "stars": row.get("stars"),
                        "headshot_url": row.get("headshot_url"),
                        "pff_overall": row.get("pff_overall"),
                        "status": row.get("status"),
                        "destination_school": row.get("destination_school"),
                        "data_source": "portal",
                    })

    # Sort by NIL value descending
    results.sort(key=lambda x: x.get("nil_value") or 0, reverse=True)

    return APIResponse(
        status="success",
        data={
            "players": results[:limit],
            "total": len(results),
            "query": query,
        },
        message=f"Found {len(results)} players matching '{query}'"
    )


@router.get(
    "/players/{player_name}/stats",
    response_model=APIResponse,
    tags=["Players"],
    summary="Get player stats",
    description="Get comprehensive stats for a specific player including PFF grades.",
)
async def get_player_stats(
    request: Request,
    player_name: str,
    season: int = 2025,
    api_key: str = Depends(require_api_key),
):
    """Get all available stats for a player.

    Args:
        player_name: Player name (URL encoded)
        season: Season year (default: 2025)
    """
    player_name_lower = player_name.lower().strip()

    # Try NIL data first (has the most enrichment)
    df = load_nil_data_enriched()
    player_row = None

    if not df.empty:
        name_col = "name" if "name" in df.columns else "player_name"
        if name_col in df.columns:
            matches = df[df[name_col].str.lower() == player_name_lower]
            if matches.empty:
                # Try partial match
                matches = df[df[name_col].str.lower().str.contains(player_name_lower, na=False)]
            if not matches.empty:
                player_row = matches.iloc[0]

    # If not found in NIL data, try portal data
    if player_row is None:
        df = load_portal_data_enriched()
        if not df.empty:
            name_col = "name" if "name" in df.columns else "player_name"
            if name_col in df.columns:
                matches = df[df[name_col].str.lower() == player_name_lower]
                if matches.empty:
                    matches = df[df[name_col].str.lower().str.contains(player_name_lower, na=False)]
                if not matches.empty:
                    player_row = matches.iloc[0]

    if player_row is None:
        return APIResponse(
            status="error",
            message=f"Player '{player_name}' not found",
            data=None
        )

    # Build comprehensive player data
    name_col = "name" if "name" in player_row.index else "player_name"

    player_data = {
        "name": player_row.get(name_col, player_name),
        "position": player_row.get("position"),
        "school": player_row.get("school", player_row.get("origin_school")),
        "headshot_url": player_row.get("headshot_url"),
        "season": season,

        # Core info
        "nil_value": player_row.get("nil_value", player_row.get("nil_valuation")),
        "nil_tier": player_row.get("nil_tier"),
        "stars": player_row.get("stars", player_row.get("recruiting_stars")),
        "height": safe_float(player_row.get("height")),
        "weight": safe_float(player_row.get("weight")),

        # PFF Grades
        "pff": {
            "overall": player_row.get("pff_overall"),
            "offense": player_row.get("pff_offense"),
            "defense": player_row.get("pff_defense"),
            "passing": player_row.get("pff_passing"),
            "rushing": player_row.get("pff_rushing"),
            "receiving": player_row.get("pff_receiving"),
            "pass_block": player_row.get("pff_pass_block"),
            "run_block": player_row.get("pff_run_block"),
            "pass_rush": player_row.get("pff_pass_rush"),
            "run_defense": player_row.get("pff_run_defense"),
            "tackling": player_row.get("pff_tackling"),
            "coverage": player_row.get("pff_coverage"),
        },

        # QB Stats
        "passing": {
            "passer_rating": player_row.get("passer_rating"),
            "completion_pct": player_row.get("completion_pct", player_row.get("adjusted_completion_pct")),
            "big_time_throws": player_row.get("big_time_throws"),
            "big_time_throw_pct": player_row.get("big_time_throw_pct"),
            "turnover_worthy_plays": player_row.get("turnover_worthy_plays"),
            "pressure_completion_pct": player_row.get("pressure_completion_percent"),
            "pressure_qb_rating": player_row.get("pressure_qb_rating"),
            "yards": player_row.get("yards", player_row.get("passing_yards")),
            "touchdowns": player_row.get("touchdowns", player_row.get("passing_tds")),
        } if player_row.get("position", "").upper() == "QB" else None,

        # RB Stats
        "rushing": {
            "elusive_rating": player_row.get("elusive_rating"),
            "yards_after_contact": player_row.get("yards_after_contact"),
            "yaco_per_attempt": player_row.get("yaco_per_attempt"),
            "breakaway_pct": player_row.get("breakaway_pct"),
            "missed_tackles_forced": player_row.get("missed_tackles_forced"),
            "yards": player_row.get("rushing_yards"),
            "touchdowns": player_row.get("rushing_tds"),
            "yards_per_carry": player_row.get("yards_per_carry", player_row.get("ypa")),
        } if player_row.get("position", "").upper() == "RB" else None,

        # WR/TE Stats
        "receiving": {
            "yards_per_route_run": player_row.get("yards_per_route_run"),
            "drop_rate": player_row.get("drop_rate"),
            "contested_catch_rate": player_row.get("contested_catch_rate"),
            "yards_after_catch": player_row.get("yards_after_catch"),
            "targets": player_row.get("targets"),
            "receptions": player_row.get("receptions"),
            "yards": player_row.get("receiving_yards", player_row.get("rec_yards")),
            "touchdowns": player_row.get("receiving_tds"),
        } if player_row.get("position", "").upper() in ("WR", "TE") else None,

        # Pass Rush Stats (EDGE/DL)
        "pass_rush": {
            "pass_rushing_productivity": player_row.get("pass_rushing_productivity"),
            "pass_rush_win_rate": player_row.get("pass_rush_win_rate"),
            "pressures": player_row.get("pressures"),
            "sacks": player_row.get("sacks"),
            "hurries": player_row.get("hurries"),
            "hits": player_row.get("hits"),
        } if player_row.get("position", "").upper() in ("EDGE", "DL", "DT", "DE") else None,

        # Coverage Stats (DB/LB)
        "coverage": {
            "passer_rating_allowed": player_row.get("passer_rating_allowed"),
            "yards_per_coverage_snap": player_row.get("yards_per_coverage_snap"),
            "forced_incompletes": player_row.get("forced_incompletes"),
            "interceptions": player_row.get("ints", player_row.get("interceptions_def")),
            "pass_breakups": player_row.get("pbus"),
            "missed_tackle_rate": player_row.get("missed_tackle_rate"),
        } if player_row.get("position", "").upper() in ("CB", "S", "DB", "LB") else None,

        # O-Line Stats
        "blocking": {
            "pass_blocking_efficiency": player_row.get("pass_blocking_efficiency"),
            "pressures_allowed": player_row.get("pressures_allowed"),
            "sacks_allowed": player_row.get("sacks_allowed"),
            "run_block_percent": player_row.get("run_block_percent"),
        } if player_row.get("position", "").upper() in ("OT", "OG", "C", "OL", "IOL") else None,
    }

    # Remove None position-specific stats
    player_data = {k: v for k, v in player_data.items() if v is not None}

    return APIResponse(
        status="success",
        data=player_data,
        message=f"Stats for {player_data.get('name', player_name)}"
    )


@router.get(
    "/pff/{category}",
    response_model=APIResponse,
    tags=["PFF Stats"],
    summary="Get PFF stats by category",
    description="Get PFF stats for a specific category (passing, rushing, receiving, defense, pass_rush, blocking, special).",
)
async def get_pff_category_stats(
    request: Request,
    category: str,
    season: int = 2025,
    limit: int = 100,
    api_key: str = Depends(require_api_key),
):
    """Get PFF stats for a category.

    Categories:
    - passing: QB passing stats
    - rushing: RB rushing stats
    - receiving: WR/TE receiving stats
    - defense: Overall defensive stats
    - pass_rush: Pass rush stats
    - blocking: O-line blocking stats
    - special: Special teams stats
    """
    # Map category to stat type
    category_map = {
        "passing": "passing_summary",
        "rushing": "rushing_summary",
        "receiving": "receiving_summary",
        "defense": "defense_summary",
        "pass_rush": "pass_rush_summary",
        "blocking": "offense_blocking",
        "special": "special_teams_summary",
    }

    stat_type = category_map.get(category.lower())
    if not stat_type:
        return APIResponse(
            status="error",
            message=f"Unknown category '{category}'. Valid: {list(category_map.keys())}",
            data=None
        )

    df = load_pff_stat(category.lower(), stat_type, season)

    if df.empty:
        return APIResponse(
            status="success",
            data={"players": [], "total": 0, "category": category, "season": season},
            message=f"No {category} stats available for {season}"
        )

    # Standardize name column
    name_col = "player" if "player" in df.columns else "name" if "name" in df.columns else None

    players = []
    for _, row in df.head(limit).iterrows():
        player = {"season": season}
        for col in df.columns:
            val = row[col]
            if pd.notna(val):
                if isinstance(val, (int, float)):
                    player[col] = float(val) if isinstance(val, float) else int(val)
                else:
                    player[col] = str(val)
        players.append(player)

    return APIResponse(
        status="success",
        data={
            "players": players,
            "total": len(df),
            "category": category,
            "season": season,
        },
        message=f"{len(players)} players with {category} stats"
    )


# =============================================================================
# Reference Data Endpoints (Step 5)
# =============================================================================

@router.get(
    "/reference/positions",
    response_model=APIResponse,
    tags=["Reference"],
    summary="Get position list",
)
async def get_positions(
    api_key: str = Depends(require_api_key),
):
    """Get list of all valid positions."""
    positions = [
        "QB", "RB", "WR", "TE", "OT", "OG", "C", "IOL",
        "EDGE", "DT", "DL", "LB", "CB", "S", "K", "P", "ATH"
    ]
    return APIResponse(
        status="success",
        data={"positions": positions},
        message=f"{len(positions)} positions"
    )


@router.get(
    "/reference/conferences",
    response_model=APIResponse,
    tags=["Reference"],
    summary="Get conference list",
)
async def get_conferences(
    api_key: str = Depends(require_api_key),
):
    """Get list of all conferences."""
    conferences = [
        "SEC", "Big Ten", "Big 12", "ACC", "Pac-12",
        "Mountain West", "AAC", "Sun Belt", "MAC", "C-USA"
    ]
    return APIResponse(
        status="success",
        data={"conferences": conferences},
        message=f"{len(conferences)} conferences"
    )


@router.get(
    "/reference/schools",
    response_model=APIResponse,
    tags=["Reference"],
    summary="Get school list",
)
async def get_schools(
    api_key: str = Depends(require_api_key),
):
    """Get list of all schools from data."""
    schools = set()

    # Get from NIL data
    df = load_nil_data()
    if not df.empty and "school" in df.columns:
        schools.update(df["school"].dropna().unique())

    # Get from portal data
    df = load_portal_data()
    if not df.empty:
        if "origin_school" in df.columns:
            schools.update(df["origin_school"].dropna().unique())
        if "destination_school" in df.columns:
            schools.update(df["destination_school"].dropna().unique())
        if "school" in df.columns:
            schools.update(df["school"].dropna().unique())

    # Clean and sort
    schools = sorted([s for s in schools if s and str(s) != 'nan' and len(str(s)) > 1])

    return APIResponse(
        status="success",
        data={"schools": schools},
        message=f"{len(schools)} schools"
    )


@router.get(
    "/reference/presets",
    response_model=APIResponse,
    tags=["Reference"],
    summary="Get position presets",
    description="Get height/weight presets for each position.",
)
async def get_position_presets(
    api_key: str = Depends(require_api_key),
):
    """Get height and weight presets by position."""
    height_presets = {
        "QB": {"min": 72, "ideal_min": 74, "label": "6'0\"+ (ideal 6'2\"+)"},
        "WR": {"min": 69, "tall": 75, "label": "5'9\"+ (tall: 6'3\"+)"},
        "RB": {"min": 66, "max": 74, "label": "5'6\" - 6'2\""},
        "TE": {"min": 75, "ideal_min": 77, "label": "6'3\"+ (ideal 6'5\"+)"},
        "OT": {"min": 76, "ideal_min": 78, "label": "6'4\"+ (ideal 6'6\"+)"},
        "OG": {"min": 74, "ideal_min": 76, "label": "6'2\"+ (ideal 6'4\"+)"},
        "C": {"min": 73, "ideal_min": 75, "label": "6'1\"+ (ideal 6'3\"+)"},
        "EDGE": {"min": 74, "ideal_min": 76, "label": "6'2\"+ (ideal 6'4\"+)"},
        "DT": {"min": 74, "ideal_min": 76, "label": "6'2\"+ (ideal 6'4\"+)"},
        "LB": {"min": 72, "ideal_min": 74, "label": "6'0\"+ (ideal 6'2\"+)"},
        "CB": {"min": 69, "max": 75, "label": "5'9\" - 6'3\""},
        "S": {"min": 70, "ideal_min": 73, "label": "5'10\"+ (ideal 6'1\"+)"},
    }

    weight_presets = {
        "QB": {"min": 200, "ideal_min": 215, "label": "200+ lbs (ideal 215+)"},
        "WR": {"min": 170, "max": 220, "label": "170-220 lbs"},
        "RB": {"min": 190, "max": 230, "label": "190-230 lbs"},
        "TE": {"min": 240, "ideal_min": 250, "label": "240+ lbs (ideal 250+)"},
        "OT": {"min": 300, "ideal_min": 315, "label": "300+ lbs (ideal 315+)"},
        "OG": {"min": 300, "ideal_min": 315, "label": "300+ lbs (ideal 315+)"},
        "C": {"min": 290, "ideal_min": 305, "label": "290+ lbs (ideal 305+)"},
        "EDGE": {"min": 240, "ideal_min": 260, "label": "240+ lbs (ideal 260+)"},
        "DT": {"min": 280, "ideal_min": 300, "label": "280+ lbs (ideal 300+)"},
        "LB": {"min": 220, "ideal_min": 235, "label": "220+ lbs (ideal 235+)"},
        "CB": {"min": 175, "max": 210, "label": "175-210 lbs"},
        "S": {"min": 190, "ideal_min": 205, "label": "190+ lbs (ideal 205+)"},
    }

    return APIResponse(
        status="success",
        data={
            "height": height_presets,
            "weight": weight_presets,
        },
        message="Position presets for height and weight"
    )
