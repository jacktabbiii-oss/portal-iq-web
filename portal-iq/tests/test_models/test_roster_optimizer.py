"""
Tests for Roster Optimizer
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models.roster_optimizer import RosterOptimizer


class TestRosterOptimizer:
    """Tests for RosterOptimizer class."""

    @pytest.fixture
    def optimizer(self, config):
        """Create a RosterOptimizer instance."""
        return RosterOptimizer(config)

    def test_init(self, optimizer):
        """Test optimizer initialization."""
        assert optimizer is not None
        assert optimizer.win_model is not None
        assert optimizer.nil_valuator is not None

    def test_optimize_portal_targets(self, optimizer):
        """Test portal target optimization."""
        current_roster = pd.DataFrame({
            "player_id": ["r1", "r2"],
            "player_name": ["Player 1", "Player 2"],
            "position": ["QB", "WR"],
        })

        available_players = pd.DataFrame({
            "player_id": ["a1", "a2", "a3"],
            "player_name": ["Target 1", "Target 2", "Target 3"],
            "position": ["CB", "WR", "EDGE"],
            "nil_valuation": [500000, 300000, 400000],
        })

        result = optimizer.optimize_portal_targets(
            current_roster=current_roster,
            available_players=available_players,
            budget=1000000,
            max_additions=2,
        )

        assert "status" in result
        assert "selected_players" in result
        assert "total_cost" in result
        assert "budget_remaining" in result

    def test_allocate_nil_budget_balanced(self, optimizer, sample_roster_data):
        """Test balanced NIL budget allocation."""
        result = optimizer.allocate_nil_budget(
            roster=sample_roster_data,
            total_budget=5000000,
            strategy="balanced",
        )

        assert "nil_allocation" in result.columns
        assert result["nil_allocation"].sum() <= 5000000

    def test_allocate_nil_budget_top_heavy(self, optimizer, sample_roster_data):
        """Test top-heavy NIL budget allocation."""
        result = optimizer.allocate_nil_budget(
            roster=sample_roster_data,
            total_budget=5000000,
            strategy="top_heavy",
        )

        assert "nil_allocation" in result.columns
        # Top players should have higher allocation
        top_allocation = result.nlargest(5, "nil_allocation")["nil_allocation"].mean()
        bottom_allocation = result.nsmallest(5, "nil_allocation")["nil_allocation"].mean()
        assert top_allocation > bottom_allocation

    def test_allocate_nil_budget_positional(self, optimizer, sample_roster_data):
        """Test positional NIL budget allocation."""
        result = optimizer.allocate_nil_budget(
            roster=sample_roster_data,
            total_budget=5000000,
            strategy="positional",
        )

        assert "nil_allocation" in result.columns

    def test_evaluate_trade(self, optimizer, sample_roster_data):
        """Test trade evaluation."""
        incoming = [
            {"player_name": "New Player", "position": "QB", "player_rating": 85}
        ]

        result = optimizer.evaluate_trade(
            team_roster=sample_roster_data,
            outgoing=["r1"],
            incoming=incoming,
            nil_adjustment=100000,
        )

        assert "outgoing_war" in result
        assert "incoming_war" in result
        assert "war_delta" in result
        assert "recommendation" in result
        assert result["recommendation"] in ["accept", "reject"]


class TestRosterOptimizerIntegration:
    """Integration tests for RosterOptimizer."""

    @pytest.fixture
    def optimizer(self, config):
        """Create a RosterOptimizer instance."""
        return RosterOptimizer(config)

    @pytest.mark.slow
    def test_full_optimization_workflow(self, optimizer, sample_roster_data):
        """Test full optimization workflow."""
        # Create available players
        available = pd.DataFrame({
            "player_id": [f"t{i}" for i in range(10)],
            "player_name": [f"Target {i}" for i in range(10)],
            "position": ["CB", "CB", "WR", "WR", "EDGE", "LB", "S", "OT", "RB", "TE"],
            "nil_valuation": [500000, 400000, 350000, 300000, 450000, 280000, 250000, 320000, 200000, 180000],
            "player_rating": [82, 78, 80, 75, 84, 76, 74, 79, 72, 70],
        })

        # Run optimization
        result = optimizer.optimize_portal_targets(
            current_roster=sample_roster_data,
            available_players=available,
            budget=2000000,
            max_additions=5,
            position_needs={"CB": 2, "WR": 1},
        )

        assert result["status"] in ["Optimal", "Not Solved"]
        assert result["total_cost"] <= 2000000
        assert len(result["selected_players"]) <= 5
