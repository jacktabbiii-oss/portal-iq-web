"""
Tests for NIL Valuator Model
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models.nil_valuator import NILValuator


class TestNILValuator:
    """Tests for NILValuator class."""

    @pytest.fixture
    def valuator(self, config):
        """Create a NILValuator instance."""
        return NILValuator(config)

    def test_init(self, valuator):
        """Test valuator initialization."""
        assert valuator is not None
        assert valuator.model is None
        assert valuator.feature_columns == []

    def test_build_model_xgboost(self, valuator):
        """Test building XGBoost model."""
        valuator.build_model(model_type="xgboost")
        assert valuator.model is not None
        assert valuator.model_type == "xgboost"

    def test_build_model_lightgbm(self, valuator):
        """Test building LightGBM model."""
        valuator.build_model(model_type="lightgbm")
        assert valuator.model is not None
        assert valuator.model_type == "lightgbm"

    def test_build_model_gbm(self, valuator):
        """Test building GBM model."""
        valuator.build_model(model_type="gbm")
        assert valuator.model is not None
        assert valuator.model_type == "gbm"

    def test_train(self, valuator, sample_player_data):
        """Test model training."""
        # Prepare features
        X = sample_player_data[["social_followers", "yards", "touchdowns", "games"]].fillna(0)
        y = sample_player_data["nil_valuation"]

        metrics = valuator.train(X, y, validate=False)

        assert "trained" in metrics
        assert metrics["trained"] is True
        assert valuator.model is not None
        assert len(valuator.feature_columns) == 4

    def test_predict_untrained_raises(self, valuator, sample_player_data):
        """Test predict raises error when model not trained."""
        X = sample_player_data[["social_followers", "yards"]].fillna(0)

        with pytest.raises(ValueError, match="Model not trained"):
            valuator.predict(X)

    def test_predict(self, valuator, sample_player_data):
        """Test prediction after training."""
        X = sample_player_data[["social_followers", "yards", "touchdowns", "games"]].fillna(0)
        y = sample_player_data["nil_valuation"]

        valuator.train(X, y, validate=False)
        predictions = valuator.predict(X)

        assert len(predictions) == len(X)
        assert isinstance(predictions, np.ndarray)

    def test_predict_with_confidence(self, valuator, sample_player_data):
        """Test prediction with confidence intervals."""
        X = sample_player_data[["social_followers", "yards", "touchdowns", "games"]].fillna(0)
        y = sample_player_data["nil_valuation"]

        valuator.train(X, y, validate=False)
        predictions, lower, upper = valuator.predict_with_confidence(X)

        assert len(predictions) == len(X)
        assert len(lower) == len(X)
        assert len(upper) == len(X)
        assert all(lower <= predictions)
        assert all(predictions <= upper)

    def test_get_feature_importance(self, valuator, sample_player_data):
        """Test getting feature importance."""
        X = sample_player_data[["social_followers", "yards", "touchdowns", "games"]].fillna(0)
        y = sample_player_data["nil_valuation"]

        valuator.train(X, y, validate=False)
        importance = valuator.get_feature_importance()

        assert isinstance(importance, pd.DataFrame)
        assert "feature" in importance.columns
        assert "importance" in importance.columns
        assert len(importance) == 4

    def test_value_player(self, valuator, sample_player_data):
        """Test valuing a single player."""
        # First train the model
        X = sample_player_data[["social_followers", "yards", "touchdowns", "games"]].fillna(0)
        y = sample_player_data["nil_valuation"]
        valuator.train(X, y, validate=False)

        player_data = {
            "player_name": "Test Player",
            "position": "QB",
            "school": "Alabama",
            "social_followers": 100000,
            "yards": 2000,
            "touchdowns": 20,
            "games": 10,
        }

        result = valuator.value_player(player_data)

        assert "player_name" in result
        assert "valuation" in result
        assert "valuation_low" in result
        assert "valuation_high" in result
        assert "nil_tier" in result
