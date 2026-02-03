"""API client for Portal IQ backend.

Handles all communication with the FastAPI backend.
"""

import os
from typing import Any, Dict, List, Optional
from datetime import datetime

import requests
import streamlit as st


class PortalIQClient:
    """Client for Portal IQ API."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the API client.

        Args:
            base_url: API base URL (defaults to env var or localhost)
            api_key: API key for authentication
        """
        self.base_url = base_url or os.getenv("PORTAL_IQ_API_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("PORTAL_IQ_API_KEY", "dev-key-123")
        self.timeout = 30

    def _headers(self) -> Dict[str, str]:
        """Get request headers with API key."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make an API request.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            data: Request body data (for POST)

        Returns:
            Response data dict
        """
        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = requests.get(
                    url,
                    headers=self._headers(),
                    timeout=self.timeout,
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=self._headers(),
                    json=data,
                    timeout=self.timeout,
                )
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": "Could not connect to API server",
                "data": None,
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timed out",
                "data": None,
            }
        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "message": str(e),
                "data": None,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "data": None,
            }

    # =========================================================================
    # Health Check
    # =========================================================================

    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        return self._request("GET", "/")

    # =========================================================================
    # NIL Endpoints
    # =========================================================================

    def predict_nil(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get NIL valuation prediction for a player.

        Args:
            player_data: Player profile data

        Returns:
            NIL prediction with value breakdown
        """
        return self._request("POST", "/api/nil/predict", {"player": player_data})

    def transfer_impact(
        self,
        player_data: Dict[str, Any],
        target_school: str,
    ) -> Dict[str, Any]:
        """Analyze transfer impact on NIL value.

        Args:
            player_data: Player profile data
            target_school: Potential transfer destination

        Returns:
            Transfer impact analysis
        """
        return self._request("POST", "/api/nil/transfer-impact", {
            "player": player_data,
            "target_school": target_school,
        })

    def market_report(
        self,
        position: Optional[str] = None,
        conference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get NIL market report.

        Args:
            position: Filter by position
            conference: Filter by conference

        Returns:
            Market report data
        """
        return self._request("POST", "/api/nil/market-report", {
            "position": position,
            "conference": conference,
        })

    # =========================================================================
    # Portal Endpoints
    # =========================================================================

    def predict_flight_risk(
        self,
        player_data: Dict[str, Any],
        team_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Predict flight risk for a player.

        Args:
            player_data: Player profile data
            team_context: Additional team context

        Returns:
            Flight risk prediction
        """
        return self._request("POST", "/api/portal/flight-risk", {
            "player": player_data,
            "team_context": team_context,
        })

    def team_flight_report(self, school: str) -> Dict[str, Any]:
        """Get team-wide flight risk report.

        Args:
            school: School name

        Returns:
            Team flight risk report
        """
        return self._request("POST", "/api/portal/team-report", {"school": school})

    def portal_fit_score(
        self,
        player_data: Dict[str, Any],
        target_school: str,
    ) -> Dict[str, Any]:
        """Calculate portal fit score.

        Args:
            player_data: Portal player data
            target_school: Target school

        Returns:
            Fit score analysis
        """
        return self._request("POST", "/api/portal/fit-score", {
            "player": player_data,
            "target_school": target_school,
        })

    def portal_recommendations(
        self,
        school: str,
        budget: float,
        positions_of_need: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get portal recommendations for a school.

        Args:
            school: School seeking players
            budget: Available NIL budget
            positions_of_need: Priority positions

        Returns:
            Ranked portal recommendations
        """
        return self._request("POST", "/api/portal/recommendations", {
            "school": school,
            "budget": budget,
            "positions_of_need": positions_of_need,
        })

    # =========================================================================
    # Draft Endpoints
    # =========================================================================

    def project_draft(self, player_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get draft projection for a player.

        Args:
            player_data: Player profile data

        Returns:
            Draft projection with earnings estimates
        """
        return self._request("POST", "/api/draft/project", {"player": player_data})

    def mock_draft(
        self,
        season_year: int,
        num_rounds: int = 3,
    ) -> Dict[str, Any]:
        """Generate mock draft board.

        Args:
            season_year: Draft year
            num_rounds: Number of rounds

        Returns:
            Mock draft board
        """
        return self._request("POST", "/api/draft/mock", {
            "season_year": season_year,
            "num_rounds": num_rounds,
        })

    # =========================================================================
    # Roster Endpoints
    # =========================================================================

    def optimize_roster(
        self,
        school: str,
        total_budget: float,
        win_target: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Optimize NIL budget allocation.

        Args:
            school: School name
            total_budget: Total NIL budget
            win_target: Optional win target

        Returns:
            Optimized budget allocation
        """
        return self._request("POST", "/api/roster/optimize", {
            "school": school,
            "total_budget": total_budget,
            "win_target": win_target,
        })

    def scenario_analysis(
        self,
        school: str,
        changes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze roster change scenarios.

        Args:
            school: School name
            changes: List of player changes

        Returns:
            Scenario analysis results
        """
        return self._request("POST", "/api/roster/scenario", {
            "school": school,
            "changes": changes,
        })

    def roster_report(self, school: str) -> Dict[str, Any]:
        """Get comprehensive roster report.

        Args:
            school: School name

        Returns:
            Full roster report
        """
        return self._request("GET", f"/api/roster/{school}/report")


@st.cache_resource
def get_api_client() -> PortalIQClient:
    """Get cached API client instance."""
    return PortalIQClient()
