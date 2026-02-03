"""
Pytest Configuration and Fixtures

Shared fixtures and configuration for Portal IQ tests.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.config import Config


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_player_data():
    """Create sample player data for testing."""
    return pd.DataFrame({
        "player_id": ["p1", "p2", "p3", "p4", "p5"],
        "player_name": ["John Smith", "Mike Johnson", "Chris Davis", "Tyler Brown", "Marcus Williams"],
        "position": ["QB", "WR", "RB", "CB", "EDGE"],
        "school": ["Alabama", "Ohio State", "Georgia", "Texas", "Michigan"],
        "class_year": ["JR", "SR", "SO", "JR", "SR"],
        "stars": [5, 4, 4, 3, 4],
        "nil_valuation": [1500000, 500000, 400000, 200000, 600000],
        "social_followers": [250000, 100000, 80000, 30000, 120000],
        "yards": [3500, 1200, 1100, 0, 0],
        "touchdowns": [35, 12, 10, 0, 0],
        "games": [12, 12, 11, 12, 12],
    })


@pytest.fixture
def sample_portal_data():
    """Create sample portal data for testing."""
    return pd.DataFrame({
        "player_id": ["t1", "t2", "t3", "t4", "t5"],
        "first_name": ["James", "Kevin", "Robert", "David", "Michael"],
        "last_name": ["Wilson", "Clark", "Thomas", "Anderson", "Taylor"],
        "position": ["WR", "QB", "RB", "CB", "LB"],
        "origin": ["USC", "Florida", "LSU", "Miami", "Clemson"],
        "destination": ["Oregon", None, "Texas", None, "Alabama"],
        "transfer_date": ["2025-01-10", "2025-01-12", "2025-01-08", "2025-01-15", "2025-01-05"],
        "stars": [4, 3, 4, 4, 3],
    })


@pytest.fixture
def sample_roster_data():
    """Create sample roster data for testing."""
    positions = ["QB", "QB", "RB", "RB", "RB", "WR", "WR", "WR", "WR",
                 "TE", "TE", "OT", "OT", "OG", "OG", "C",
                 "DE", "DE", "DT", "DT", "LB", "LB", "LB",
                 "CB", "CB", "CB", "S", "S"]

    return pd.DataFrame({
        "player_id": [f"r{i}" for i in range(len(positions))],
        "player_name": [f"Player {i}" for i in range(len(positions))],
        "position": positions,
        "team": ["Alabama"] * len(positions),
        "class_year": np.random.choice(["FR", "SO", "JR", "SR"], len(positions)),
        "recruiting_stars": np.random.choice([3, 4, 5], len(positions), p=[0.5, 0.35, 0.15]),
        "starter": [i % 3 == 0 for i in range(len(positions))],
        "player_rating": np.random.randint(60, 95, len(positions)),
        "scholarship": [True] * len(positions),
    })


@pytest.fixture
def sample_draft_data():
    """Create sample draft data for testing."""
    return pd.DataFrame({
        "player_id": ["d1", "d2", "d3", "d4", "d5"],
        "player_name": ["Draft Pick 1", "Draft Pick 2", "Draft Pick 3", "Draft Pick 4", "Draft Pick 5"],
        "position": ["QB", "EDGE", "CB", "WR", "OT"],
        "school": ["Alabama", "Georgia", "Ohio State", "LSU", "Michigan"],
        "height": [76, 77, 72, 73, 78],
        "weight": [220, 265, 195, 200, 315],
        "recruiting_stars": [5, 4, 4, 4, 4],
        "career_yards": [10000, 0, 0, 3500, 0],
        "career_games": [36, 38, 40, 35, 42],
        "forty": [4.65, 4.55, 4.38, 4.42, 5.05],
        "vertical": [32, 36, 38, 40, 28],
        "age_at_draft": [22, 21, 22, 21, 23],
    })


@pytest.fixture
def mock_api_response():
    """Create mock API response data."""
    return {
        "status": "success",
        "data": {
            "players": [
                {"id": 1, "name": "Test Player", "position": "QB"},
            ]
        }
    }


class MockModel:
    """Mock ML model for testing."""

    def __init__(self):
        self.is_fitted = False

    def fit(self, X, y):
        self.is_fitted = True
        return self

    def predict(self, X):
        return np.zeros(len(X))

    def predict_proba(self, X):
        return np.column_stack([np.ones(len(X)) * 0.5, np.ones(len(X)) * 0.5])


@pytest.fixture
def mock_model():
    """Create a mock model for testing."""
    return MockModel()


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
