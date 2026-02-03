"""
Player Matching Utilities

Fuzzy matching and entity resolution for player names across data sources.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from difflib import SequenceMatcher
import re

from .config import Config


class PlayerMatcher:
    """Matches player names across different data sources."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the player matcher.

        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self._name_cache: Dict[str, str] = {}

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalize a player name for matching.

        Args:
            name: Raw player name

        Returns:
            Normalized name
        """
        if not name:
            return ""

        # Lowercase
        name = name.lower()

        # Remove common suffixes
        suffixes = [" jr", " jr.", " sr", " sr.", " ii", " iii", " iv"]
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        # Remove punctuation
        name = re.sub(r"[^\w\s]", "", name)

        # Normalize whitespace
        name = " ".join(name.split())

        return name

    @staticmethod
    def similarity_score(name1: str, name2: str) -> float:
        """
        Calculate similarity score between two names.

        Args:
            name1: First name
            name2: Second name

        Returns:
            Similarity score (0-1)
        """
        norm1 = PlayerMatcher.normalize_name(name1)
        norm2 = PlayerMatcher.normalize_name(name2)

        if norm1 == norm2:
            return 1.0

        return SequenceMatcher(None, norm1, norm2).ratio()

    def find_best_match(
        self,
        name: str,
        candidates: List[str],
        threshold: float = 0.8,
    ) -> Optional[Tuple[str, float]]:
        """
        Find the best matching name from a list of candidates.

        Args:
            name: Name to match
            candidates: List of candidate names
            threshold: Minimum similarity threshold

        Returns:
            Tuple of (matched_name, score) or None
        """
        norm_name = self.normalize_name(name)

        # Check cache first
        if norm_name in self._name_cache:
            cached = self._name_cache[norm_name]
            if cached in candidates:
                return (cached, 1.0)

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            score = self.similarity_score(name, candidate)
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_score >= threshold:
            # Cache the match
            self._name_cache[norm_name] = best_match
            return (best_match, best_score)

        return None

    def match_dataframes(
        self,
        df1: pd.DataFrame,
        df2: pd.DataFrame,
        name_col1: str = "player_name",
        name_col2: str = "player_name",
        additional_keys: Optional[List[str]] = None,
        threshold: float = 0.8,
    ) -> pd.DataFrame:
        """
        Match players between two DataFrames.

        Args:
            df1: First DataFrame
            df2: Second DataFrame
            name_col1: Name column in df1
            name_col2: Name column in df2
            additional_keys: Additional columns to use for matching
            threshold: Minimum similarity threshold

        Returns:
            DataFrame with matched players
        """
        matches = []

        for idx1, row1 in df1.iterrows():
            name1 = row1[name_col1]

            # Filter candidates by additional keys if provided
            candidates_df = df2.copy()
            if additional_keys:
                for key in additional_keys:
                    if key in row1 and key in df2.columns:
                        candidates_df = candidates_df[
                            candidates_df[key] == row1[key]
                        ]

            candidates = candidates_df[name_col2].tolist()

            result = self.find_best_match(name1, candidates, threshold)

            if result:
                matched_name, score = result
                matched_row = df2[df2[name_col2] == matched_name].iloc[0]

                matches.append({
                    "df1_index": idx1,
                    "df1_name": name1,
                    "df2_index": matched_row.name,
                    "df2_name": matched_name,
                    "match_score": score,
                })

        return pd.DataFrame(matches)

    def deduplicate_players(
        self,
        df: pd.DataFrame,
        name_col: str = "player_name",
        group_cols: Optional[List[str]] = None,
        threshold: float = 0.9,
    ) -> pd.DataFrame:
        """
        Remove duplicate player entries.

        Args:
            df: DataFrame with potential duplicates
            name_col: Name column
            group_cols: Columns to group by before deduplication
            threshold: Similarity threshold for duplicates

        Returns:
            Deduplicated DataFrame
        """
        if group_cols:
            groups = df.groupby(group_cols)
        else:
            groups = [(None, df)]

        deduplicated_dfs = []

        for group_key, group_df in groups:
            keep_indices = []
            processed_names = []

            for idx, row in group_df.iterrows():
                name = row[name_col]
                is_duplicate = False

                for processed in processed_names:
                    if self.similarity_score(name, processed) >= threshold:
                        is_duplicate = True
                        break

                if not is_duplicate:
                    keep_indices.append(idx)
                    processed_names.append(name)

            deduplicated_dfs.append(group_df.loc[keep_indices])

        return pd.concat(deduplicated_dfs, ignore_index=True)

    def create_player_id(
        self,
        name: str,
        school: Optional[str] = None,
        position: Optional[str] = None,
    ) -> str:
        """
        Create a unique player ID from name and attributes.

        Args:
            name: Player name
            school: School name
            position: Position

        Returns:
            Unique player ID
        """
        parts = [self.normalize_name(name).replace(" ", "_")]

        if school:
            parts.append(self.normalize_name(school).replace(" ", "_")[:10])

        if position:
            parts.append(position.lower())

        return "_".join(parts)

    def parse_name(self, full_name: str) -> Dict[str, str]:
        """
        Parse a full name into components.

        Args:
            full_name: Full player name

        Returns:
            Dictionary with first_name, last_name, suffix
        """
        parts = full_name.split()

        if not parts:
            return {"first_name": "", "last_name": "", "suffix": ""}

        suffix = ""
        suffixes = ["Jr", "Jr.", "Sr", "Sr.", "II", "III", "IV"]
        if parts[-1] in suffixes:
            suffix = parts[-1]
            parts = parts[:-1]

        if len(parts) == 1:
            return {
                "first_name": parts[0],
                "last_name": "",
                "suffix": suffix,
            }

        return {
            "first_name": parts[0],
            "last_name": " ".join(parts[1:]),
            "suffix": suffix,
        }

    def combine_names(
        self,
        first_name: str,
        last_name: str,
        suffix: Optional[str] = None,
    ) -> str:
        """
        Combine name components into full name.

        Args:
            first_name: First name
            last_name: Last name
            suffix: Optional suffix

        Returns:
            Full name
        """
        parts = [first_name, last_name]
        if suffix:
            parts.append(suffix)
        return " ".join(parts)
