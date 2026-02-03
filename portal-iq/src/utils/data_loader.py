"""
Data Loader

Utilities for loading and caching data from various sources.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import hashlib
import pickle
from datetime import datetime, timedelta

from .config import Config


class DataLoader:
    """Loads and caches data from various sources."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the data loader.

        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.cache_dir = Path(self.config.data_paths.get("cache", "data/cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a key."""
        hash_key = hashlib.md5(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{hash_key}.pkl"

    def _is_cache_valid(
        self,
        cache_path: Path,
        max_age_hours: int = 24,
    ) -> bool:
        """Check if cache file is still valid."""
        if not cache_path.exists():
            return False

        modified_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - modified_time
        return age < timedelta(hours=max_age_hours)

    def cache_get(
        self,
        key: str,
        max_age_hours: int = 24,
    ) -> Optional[Any]:
        """
        Get data from cache.

        Args:
            key: Cache key
            max_age_hours: Maximum cache age in hours

        Returns:
            Cached data or None
        """
        cache_path = self._get_cache_path(key)

        if self._is_cache_valid(cache_path, max_age_hours):
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        return None

    def cache_set(self, key: str, data: Any) -> None:
        """
        Set data in cache.

        Args:
            key: Cache key
            data: Data to cache
        """
        cache_path = self._get_cache_path(key)
        with open(cache_path, "wb") as f:
            pickle.dump(data, f)

    def load_csv(
        self,
        path: Union[str, Path],
        cache: bool = True,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Load CSV file with optional caching.

        Args:
            path: Path to CSV file
            cache: Whether to use caching
            **kwargs: Additional pandas read_csv arguments

        Returns:
            DataFrame
        """
        path = Path(path)

        if cache:
            cache_key = f"csv_{path}_{path.stat().st_mtime}"
            cached = self.cache_get(cache_key)
            if cached is not None:
                return cached

        df = pd.read_csv(path, **kwargs)

        if cache:
            self.cache_set(cache_key, df)

        return df

    def load_excel(
        self,
        path: Union[str, Path],
        sheet_name: Union[str, int] = 0,
        cache: bool = True,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Load Excel file with optional caching.

        Args:
            path: Path to Excel file
            sheet_name: Sheet name or index
            cache: Whether to use caching
            **kwargs: Additional pandas read_excel arguments

        Returns:
            DataFrame
        """
        path = Path(path)

        if cache:
            cache_key = f"excel_{path}_{sheet_name}_{path.stat().st_mtime}"
            cached = self.cache_get(cache_key)
            if cached is not None:
                return cached

        df = pd.read_excel(path, sheet_name=sheet_name, **kwargs)

        if cache:
            self.cache_set(cache_key, df)

        return df

    def load_json(
        self,
        path: Union[str, Path],
        cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Load JSON file with optional caching.

        Args:
            path: Path to JSON file
            cache: Whether to use caching

        Returns:
            Dictionary
        """
        import json

        path = Path(path)

        if cache:
            cache_key = f"json_{path}_{path.stat().st_mtime}"
            cached = self.cache_get(cache_key)
            if cached is not None:
                return cached

        with open(path, "r") as f:
            data = json.load(f)

        if cache:
            self.cache_set(cache_key, data)

        return data

    def save_csv(
        self,
        df: pd.DataFrame,
        path: Union[str, Path],
        **kwargs,
    ) -> None:
        """
        Save DataFrame to CSV.

        Args:
            df: DataFrame to save
            path: Output path
            **kwargs: Additional pandas to_csv arguments
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, **kwargs)

    def save_excel(
        self,
        df: pd.DataFrame,
        path: Union[str, Path],
        sheet_name: str = "Sheet1",
        **kwargs,
    ) -> None:
        """
        Save DataFrame to Excel.

        Args:
            df: DataFrame to save
            path: Output path
            sheet_name: Sheet name
            **kwargs: Additional pandas to_excel arguments
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(path, sheet_name=sheet_name, index=False, **kwargs)

    def load_processed_data(
        self,
        name: str,
        version: Optional[str] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Load processed data by name.

        Args:
            name: Data name
            version: Optional version string

        Returns:
            DataFrame or None
        """
        processed_dir = Path(self.config.data_paths.get("processed", "data/processed"))

        if version:
            path = processed_dir / f"{name}_{version}.csv"
        else:
            # Find latest version
            matches = list(processed_dir.glob(f"{name}*.csv"))
            if not matches:
                return None
            path = max(matches, key=lambda p: p.stat().st_mtime)

        if path.exists():
            return self.load_csv(path)
        return None

    def save_processed_data(
        self,
        df: pd.DataFrame,
        name: str,
        version: Optional[str] = None,
    ) -> Path:
        """
        Save processed data.

        Args:
            df: DataFrame to save
            name: Data name
            version: Optional version string

        Returns:
            Path where data was saved
        """
        processed_dir = Path(self.config.data_paths.get("processed", "data/processed"))
        processed_dir.mkdir(parents=True, exist_ok=True)

        if version is None:
            version = datetime.now().strftime("%Y%m%d_%H%M%S")

        path = processed_dir / f"{name}_{version}.csv"
        self.save_csv(df, path)

        return path

    def clear_cache(self, older_than_days: Optional[int] = None) -> int:
        """
        Clear cache files.

        Args:
            older_than_days: Only clear files older than this many days

        Returns:
            Number of files cleared
        """
        count = 0
        now = datetime.now()

        for cache_file in self.cache_dir.glob("*.pkl"):
            if older_than_days is not None:
                modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                age = now - modified_time
                if age.days < older_than_days:
                    continue

            cache_file.unlink()
            count += 1

        return count
