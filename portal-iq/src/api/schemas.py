"""
API Schemas

Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Base Models
class PlayerBase(BaseModel):
    """Base player information."""
    player_id: Optional[str] = None
    player_name: str
    position: str
    school: Optional[str] = None
    class_year: Optional[str] = None


class PlayerStats(BaseModel):
    """Player statistics."""
    games: int = 0
    starts: int = 0
    yards: float = 0
    touchdowns: int = 0
    snaps: int = 0


# NIL Schemas
class NILValuationRequest(BaseModel):
    """Request for NIL valuation."""
    player_name: str
    position: str
    school: str
    class_year: Optional[str] = None
    stats: Optional[PlayerStats] = None
    social_followers: Optional[int] = 0
    engagement_rate: Optional[float] = 0.0
    recruiting_stars: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "player_name": "John Smith",
                "position": "QB",
                "school": "Alabama",
                "class_year": "JR",
                "social_followers": 150000,
                "engagement_rate": 3.5,
                "recruiting_stars": 4,
            }
        }


class NILValuationResponse(BaseModel):
    """Response for NIL valuation."""
    player_name: str
    valuation: float
    valuation_low: float
    valuation_high: float
    nil_tier: str
    breakdown: Optional[Dict[str, float]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "player_name": "John Smith",
                "valuation": 750000,
                "valuation_low": 500000,
                "valuation_high": 1000000,
                "nil_tier": "premium",
            }
        }


# Portal Schemas
class PortalPredictionRequest(BaseModel):
    """Request for portal prediction."""
    player_name: str
    player_id: Optional[str] = None
    position: str
    school: str
    class_year: str
    is_starter: bool = False
    snap_trend: Optional[float] = None
    coaching_change: bool = False
    current_nil: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "player_name": "Mike Johnson",
                "position": "WR",
                "school": "USC",
                "class_year": "SO",
                "is_starter": False,
                "coaching_change": True,
            }
        }


class DestinationPrediction(BaseModel):
    """Predicted destination."""
    school: str
    probability: float
    fit_score: float
    nil_potential: Optional[float] = None


class PortalPredictionResponse(BaseModel):
    """Response for portal prediction."""
    player_name: str
    entry_probability: float
    likely_destinations: List[DestinationPrediction] = []
    risk_factors: List[str] = []


# Draft Schemas
class DraftProjectionRequest(BaseModel):
    """Request for draft projection."""
    player_name: str
    position: str
    school: str
    class_year: str
    height: Optional[int] = None  # inches
    weight: Optional[int] = None  # pounds
    career_stats: Optional[Dict[str, Any]] = None
    combine_data: Optional[Dict[str, float]] = None
    recruiting_stars: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "player_name": "David Williams",
                "position": "EDGE",
                "school": "Georgia",
                "class_year": "JR",
                "height": 77,
                "weight": 265,
                "recruiting_stars": 5,
            }
        }


class ComparablePlayer(BaseModel):
    """Historical comparable player."""
    name: str
    draft_year: int
    draft_pick: int
    nfl_team: str
    similarity_score: float


class DraftProjectionResponse(BaseModel):
    """Response for draft projection."""
    player_name: str
    draft_probability: float
    projected_round: int
    projected_pick: int
    draft_grade: float
    comparable_players: List[ComparablePlayer] = []
    career_value_projection: Optional[Dict[str, float]] = None


# Roster Optimization Schemas
class RosterOptimizationRequest(BaseModel):
    """Request for roster optimization."""
    team: str
    budget: float
    max_additions: int = 10
    position_needs: Optional[Dict[str, int]] = None
    available_players: Optional[List[PlayerBase]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "team": "Texas",
                "budget": 5000000,
                "max_additions": 5,
                "position_needs": {"QB": 1, "WR": 2, "CB": 1},
            }
        }


class SelectedPlayer(BaseModel):
    """Player selected in optimization."""
    player_name: str
    position: str
    origin_school: str
    war: float
    nil_cost: float


class RosterOptimizationResponse(BaseModel):
    """Response for roster optimization."""
    status: str
    selected_players: List[SelectedPlayer]
    total_war: float
    total_cost: float
    budget_remaining: float


# Team Schemas
class TeamResponse(BaseModel):
    """Team information response."""
    name: str
    tier: str
    conference: str
    nil_ranking: Optional[int] = None
    projected_wins: Optional[float] = None
    portal_activity: Optional[Dict[str, Any]] = None


class PlayerResponse(BaseModel):
    """Player information response."""
    player_id: str
    player_name: str
    position: str
    school: str
    class_year: str
    nil_valuation: Optional[float] = None
    draft_grade: Optional[float] = None
    portal_risk: Optional[float] = None


# List Response Schemas
class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: List[Any]
    total: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
    status_code: int = 500
