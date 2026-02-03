"""
Tests for CFB Portal Data Collector
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data_collection.cfb_portal import PortalDataCollector


class TestPortalDataCollector:
    """Tests for PortalDataCollector class."""

    @pytest.fixture
    def collector(self, config):
        """Create a PortalDataCollector instance."""
        return PortalDataCollector(config)

    def test_init(self, collector):
        """Test collector initialization."""
        assert collector is not None
        assert collector.config is not None

    def test_get_portal_entries_empty(self, collector):
        """Test getting portal entries returns DataFrame."""
        with patch.object(collector, 'get_portal_entries', return_value=pd.DataFrame()):
            result = collector.get_portal_entries(season=2025)
            assert isinstance(result, pd.DataFrame)

    def test_analyze_portal_trends(self, collector, sample_portal_data):
        """Test portal trend analysis."""
        with patch.object(collector, 'get_portal_entries', return_value=sample_portal_data):
            trends = collector.analyze_portal_trends(season=2025)

            assert "total_entries" in trends
            assert "committed" in trends
            assert "uncommitted" in trends
            assert "by_position" in trends

    def test_get_team_portal_activity(self, collector, sample_portal_data):
        """Test team portal activity."""
        with patch.object(collector, 'get_portal_entries', return_value=sample_portal_data):
            activity = collector.get_team_portal_activity("USC", 2025)

            assert "incoming" in activity
            assert "outgoing" in activity
            assert isinstance(activity["incoming"], pd.DataFrame)
            assert isinstance(activity["outgoing"], pd.DataFrame)

    def test_get_portal_commitments(self, collector, sample_portal_data):
        """Test filtering to committed players."""
        with patch.object(collector, 'get_portal_entries', return_value=sample_portal_data):
            commitments = collector.get_portal_commitments(2025)

            assert isinstance(commitments, pd.DataFrame)
            # All returned players should have a destination
            if not commitments.empty:
                assert commitments["destination"].notna().all()

    def test_get_active_portal_players(self, collector, sample_portal_data):
        """Test filtering to active portal players."""
        with patch.object(collector, 'get_portal_entries', return_value=sample_portal_data):
            active = collector.get_active_portal_players(2025)

            assert isinstance(active, pd.DataFrame)
            # All returned players should not have a destination
            if not active.empty:
                assert active["destination"].isna().all()
