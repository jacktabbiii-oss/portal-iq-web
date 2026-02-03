"""
Configuration Management

Loads and manages configuration from config.yaml and environment variables.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager for Portal IQ."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Optional path to config.yaml
        """
        # Load environment variables
        load_dotenv()

        # Find config file
        if config_path is None:
            # Look in current directory and parent directories
            for path in [Path.cwd(), Path.cwd().parent, Path(__file__).parent.parent.parent]:
                candidate = path / "config.yaml"
                if candidate.exists():
                    config_path = str(candidate)
                    break

        self._config = self._load_config(config_path)
        self._load_api_keys()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path and Path(config_path).exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "data_paths": {
                "raw": "data/raw",
                "processed": "data/processed",
                "cache": "data/cache",
                "models": "models",
            },
            "current_season": 2025,
            "seasons_range": [2020, 2025],
            "school_tiers": {
                "blue_blood": ["Alabama", "Ohio State", "USC", "Michigan", "Texas", "Oklahoma", "Notre Dame"],
                "elite": ["Georgia", "Clemson", "Oregon", "Penn State", "LSU", "Florida", "Florida State", "Tennessee", "Auburn", "Wisconsin", "Miami"],
                "power_brand": [],
                "p4_mid": [],
                "g5_strong": ["Boise State", "Memphis", "SMU", "UNLV", "Tulane", "Liberty", "James Madison", "Jacksonville State", "Sam Houston"],
                "g5": [],
            },
            "conference_tiers": {
                "tier1": ["SEC", "Big Ten"],
                "tier2": ["Big 12", "ACC"],
                "tier3": ["American", "Mountain West", "Sun Belt", "MAC", "CUSA"],
            },
            "nil_tiers": {
                "mega": 1000000,
                "premium": 500000,
                "solid": 100000,
                "moderate": 25000,
                "entry": 0,
            },
            "model_params": {
                "nil_valuator": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1},
                "portal_predictor": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1},
                "draft_projector": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1},
                "win_model": {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.1},
            },
        }

    def _load_api_keys(self) -> None:
        """Load API keys from environment variables."""
        self.cfbd_api_key = os.getenv("CFBD_API_KEY", "")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///data/portal_iq.db")

    @property
    def data_paths(self) -> Dict[str, str]:
        """Get data paths configuration."""
        return self._config.get("data_paths", {})

    @property
    def current_season(self) -> int:
        """Get current season."""
        return self._config.get("current_season", 2025)

    @property
    def seasons_range(self) -> List[int]:
        """Get seasons range."""
        return self._config.get("seasons_range", [2020, 2025])

    @property
    def school_tiers(self) -> Dict[str, List[str]]:
        """Get school tier classifications."""
        return self._config.get("school_tiers", {})

    @property
    def conference_tiers(self) -> Dict[str, List[str]]:
        """Get conference tier classifications."""
        return self._config.get("conference_tiers", {})

    @property
    def nil_tiers(self) -> Dict[str, int]:
        """Get NIL tier thresholds."""
        return self._config.get("nil_tiers", {})

    @property
    def model_params(self) -> Dict[str, Dict[str, Any]]:
        """Get model hyperparameters."""
        return self._config.get("model_params", {})

    def get_school_tier(self, school: str) -> str:
        """
        Get tier classification for a school.

        Args:
            school: School name

        Returns:
            Tier name
        """
        for tier, schools in self.school_tiers.items():
            if school in schools:
                return tier
        return "g5"

    def get_conference_tier(self, conference: str) -> int:
        """
        Get tier classification for a conference.

        Args:
            conference: Conference name

        Returns:
            Tier number (1-3)
        """
        for tier, conferences in self.conference_tiers.items():
            if conference in conferences:
                return int(tier.replace("tier", ""))
        return 3

    def get_nil_tier(self, value: float) -> str:
        """
        Get NIL tier for a valuation.

        Args:
            value: NIL valuation

        Returns:
            Tier name
        """
        sorted_tiers = sorted(
            self.nil_tiers.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for tier_name, threshold in sorted_tiers:
            if value >= threshold:
                return tier_name
        return "entry"

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return self._config.copy()
