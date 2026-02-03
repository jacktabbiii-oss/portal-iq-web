"""
Tests for API Routes
"""

import pytest
from fastapi.testclient import TestClient

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.app import create_app


class TestAPIRoutes:
    """Tests for API routes."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        app = create_app()
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "Portal IQ API"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_get_nil_tiers(self, client):
        """Test NIL tiers endpoint."""
        response = client.get("/api/v1/nil/tiers")

        assert response.status_code == 200
        data = response.json()
        assert "mega" in data
        assert "premium" in data
        assert "entry" in data

    def test_get_school_tiers(self, client):
        """Test school tiers endpoint."""
        response = client.get("/api/v1/config/school-tiers")

        assert response.status_code == 200
        data = response.json()
        assert "blue_blood" in data
        assert "elite" in data

    def test_get_conference_tiers(self, client):
        """Test conference tiers endpoint."""
        response = client.get("/api/v1/config/conference-tiers")

        assert response.status_code == 200
        data = response.json()
        assert "tier1" in data
        assert "tier2" in data

    def test_get_teams(self, client):
        """Test teams endpoint."""
        response = client.get("/api/v1/teams")

        assert response.status_code == 200
        data = response.json()
        assert "teams" in data
        assert len(data["teams"]) > 0

    def test_nil_valuate_endpoint(self, client):
        """Test NIL valuation endpoint."""
        request_data = {
            "player_name": "Test Player",
            "position": "QB",
            "school": "Alabama",
            "social_followers": 100000,
        }

        response = client.post("/api/v1/nil/valuate", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "player_name" in data
        assert "valuation" in data

    def test_portal_predict_endpoint(self, client):
        """Test portal prediction endpoint."""
        request_data = {
            "player_name": "Test Player",
            "position": "WR",
            "school": "USC",
            "class_year": "JR",
        }

        response = client.post("/api/v1/portal/predict", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "player_name" in data
        assert "entry_probability" in data

    def test_draft_project_endpoint(self, client):
        """Test draft projection endpoint."""
        request_data = {
            "player_name": "Test Player",
            "position": "EDGE",
            "school": "Georgia",
            "class_year": "JR",
        }

        response = client.post("/api/v1/draft/project", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "player_name" in data
        assert "draft_probability" in data
        assert "projected_round" in data

    def test_roster_optimize_endpoint(self, client):
        """Test roster optimization endpoint."""
        request_data = {
            "team": "Texas",
            "budget": 5000000,
            "max_additions": 5,
        }

        response = client.post("/api/v1/roster/optimize", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "selected_players" in data

    def test_nil_leaderboard_endpoint(self, client):
        """Test NIL leaderboard endpoint."""
        response = client.get("/api/v1/nil/leaderboard")

        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        assert "total" in data

    def test_active_portal_endpoint(self, client):
        """Test active portal players endpoint."""
        response = client.get("/api/v1/portal/active")

        assert response.status_code == 200
        data = response.json()
        assert "players" in data
        assert "total" in data

    def test_draft_board_endpoint(self, client):
        """Test draft board endpoint."""
        response = client.get("/api/v1/draft/board")

        assert response.status_code == 200
        data = response.json()
        assert "players" in data
