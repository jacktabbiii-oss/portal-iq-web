"""Player Comparison Engine for Portal IQ.

Uses cosine similarity on position-specific feature vectors to find:
1. Similar portal players (for coaches evaluating targets)
2. Historical successful transfers (for projecting outcomes)
3. NFL comparisons (for NIL valuation context)
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from utils.logging_config import get_logger, log_execution_time

logger = get_logger(__name__)


# =============================================================================
# Position-Specific Feature Sets
# =============================================================================

# Features weighted by importance for each position group
# Higher weight = more important for similarity calculation
POSITION_FEATURES = {
    "QB": {
        # Core passing metrics
        "pff_passing": 1.5,
        "adjusted_completion_pct": 1.3,
        "completion_pct": 1.0,
        "passer_rating": 1.2,
        # Playmaking
        "big_time_throw_pct": 1.4,
        "turnover_worthy_play_pct": 1.3,  # Lower is better
        "avg_depth_of_target": 1.0,
        # Under pressure
        "pressure_completion_percent": 1.2,
        "pressure_qb_rating": 1.1,
        # Mobility
        "scramble_yards": 0.8,
        "rushing_yards": 0.6,
    },
    "RB": {
        # Elusiveness
        "pff_rushing": 1.5,
        "elusive_rating": 1.5,
        "yards_after_contact": 1.3,
        "yaco_per_attempt": 1.2,
        "missed_tackles_forced": 1.2,
        # Explosiveness
        "breakaway_pct": 1.3,
        "ypa": 1.1,  # yards per attempt
        # Receiving ability
        "pff_receiving": 1.0,
        "catch_rate": 0.9,
        "receptions": 0.7,
    },
    "WR": {
        # Route running
        "pff_receiving": 1.5,
        "yards_per_route_run": 1.5,
        # Hands
        "catch_rate": 1.3,
        "drop_rate": 1.2,  # Lower is better
        "contested_catch_rate": 1.3,
        # YAC ability
        "yards_after_catch_per_reception": 1.2,
        # Production
        "receiving_yards": 1.0,
        "receiving_tds": 0.9,
        "receptions": 0.8,
    },
    "TE": {
        # Receiving
        "pff_receiving": 1.3,
        "yards_per_route_run": 1.3,
        "catch_rate": 1.2,
        "contested_catch_rate": 1.1,
        # Blocking
        "pff_run_block": 1.2,
        "pff_pass_block": 1.1,
        # Production
        "receiving_yards": 1.0,
        "receiving_tds": 0.9,
    },
    "OL": {
        # Pass protection
        "pff_pass_block": 1.5,
        "pass_blocking_efficiency": 1.5,
        "pressures_allowed": 1.3,  # Lower is better
        "sacks_allowed": 1.2,  # Lower is better
        # Run blocking
        "pff_run_block": 1.4,
        "run_block_percent": 1.2,
        # Discipline
        "penalties": 0.8,  # Lower is better
    },
    "EDGE": {
        # Pass rush
        "pff_pass_rush": 1.5,
        "pass_rushing_productivity": 1.5,
        "pass_rush_win_rate": 1.4,
        "pressures": 1.3,
        "sacks": 1.2,
        "hurries": 1.0,
        # Run defense
        "pff_run_defense": 1.1,
        "stop_percent": 1.0,
        "tackles_for_loss": 1.0,
    },
    "DL": {
        # Pass rush
        "pff_pass_rush": 1.4,
        "pass_rushing_productivity": 1.3,
        "pressures": 1.2,
        # Run stuffing
        "pff_run_defense": 1.5,
        "stop_percent": 1.4,
        "tackles_for_loss": 1.2,
        "tackles": 1.0,
    },
    "LB": {
        # Run defense
        "pff_run_defense": 1.4,
        "stop_percent": 1.3,
        "tackles": 1.2,
        "tackles_for_loss": 1.1,
        # Coverage
        "pff_coverage": 1.3,
        "passer_rating_allowed": 1.2,  # Lower is better
        # Tackling
        "pff_tackling": 1.2,
        "missed_tackle_rate": 1.0,  # Lower is better
    },
    "CB": {
        # Coverage
        "pff_coverage": 1.5,
        "passer_rating_allowed": 1.4,  # Lower is better
        "yards_per_coverage_snap": 1.3,  # Lower is better
        "forced_incompletion_rate": 1.3,
        # Man vs Zone
        "man_qb_rating_against": 1.2,  # Lower is better
        "zone_qb_rating_against": 1.1,  # Lower is better
        # Ball skills
        "ints": 1.0,
        "pbus": 0.9,
        # Tackling
        "missed_tackle_rate": 0.8,  # Lower is better
    },
    "S": {
        # Coverage
        "pff_coverage": 1.4,
        "passer_rating_allowed": 1.3,  # Lower is better
        "coverage_snaps_per_target": 1.2,
        # Run support
        "pff_run_defense": 1.2,
        "stop_percent": 1.1,
        "tackles": 1.0,
        # Ball skills
        "ints": 1.1,
        "pbus": 0.9,
        "forced_fumbles": 0.8,
    },
}

# Features where lower values are better (need to be inverted)
INVERSE_FEATURES = {
    "turnover_worthy_play_pct",
    "drop_rate",
    "pressures_allowed",
    "sacks_allowed",
    "penalties",
    "passer_rating_allowed",
    "yards_per_coverage_snap",
    "man_qb_rating_against",
    "zone_qb_rating_against",
    "missed_tackle_rate",
}

# Position group mappings
POSITION_GROUPS = {
    "QB": ["QB"],
    "RB": ["RB", "FB"],
    "WR": ["WR"],
    "TE": ["TE"],
    "OL": ["OT", "OG", "C", "IOL", "OL"],
    "EDGE": ["EDGE", "DE", "OLB"],
    "DL": ["DT", "DL", "NT"],
    "LB": ["LB", "ILB", "MLB"],
    "CB": ["CB"],
    "S": ["S", "FS", "SS", "DB"],
}


def get_position_group(position: str) -> str:
    """Map a specific position to its position group.

    Args:
        position: Specific position (e.g., "OT", "ILB")

    Returns:
        Position group (e.g., "OL", "LB")
    """
    if not position:
        return "QB"  # Default

    position = position.upper().strip()

    for group, positions in POSITION_GROUPS.items():
        if position in positions:
            return group

    # If exact match not found, try partial
    for group, positions in POSITION_GROUPS.items():
        if any(pos in position or position in pos for pos in positions):
            return group

    return "QB"  # Fallback


class PlayerComparison:
    """Engine for finding similar players based on position-specific metrics."""

    def __init__(
        self,
        pff_data: pd.DataFrame,
        portal_data: Optional[pd.DataFrame] = None,
        nil_data: Optional[pd.DataFrame] = None
    ):
        """Initialize the comparison engine.

        Args:
            pff_data: DataFrame with PFF grades (must have 'name' column)
            portal_data: Optional DataFrame with portal player data
            nil_data: Optional DataFrame with NIL valuations
        """
        self.pff = pff_data.copy() if pff_data is not None else pd.DataFrame()
        self.portal = portal_data.copy() if portal_data is not None else pd.DataFrame()
        self.nil = nil_data.copy() if nil_data is not None else pd.DataFrame()
        self.scaler = StandardScaler()

        # Pre-compute feature matrices per position group
        self._feature_cache: Dict[str, Tuple[pd.DataFrame, np.ndarray]] = {}

        logger.info(f"PlayerComparison initialized with {len(self.pff)} PFF records")

    def _get_feature_columns(self, position_group: str) -> List[str]:
        """Get available feature columns for a position group.

        Args:
            position_group: Position group (QB, RB, WR, etc.)

        Returns:
            List of column names available in the PFF data
        """
        if position_group not in POSITION_FEATURES:
            position_group = "QB"  # Fallback

        features = POSITION_FEATURES[position_group]
        available = [col for col in features.keys() if col in self.pff.columns]

        return available

    def _get_feature_weights(self, position_group: str, features: List[str]) -> np.ndarray:
        """Get weights for features.

        Args:
            position_group: Position group
            features: List of feature column names

        Returns:
            Array of weights
        """
        if position_group not in POSITION_FEATURES:
            return np.ones(len(features))

        weights = []
        for f in features:
            weights.append(POSITION_FEATURES[position_group].get(f, 1.0))

        return np.array(weights)

    def _prepare_feature_matrix(
        self,
        df: pd.DataFrame,
        position_group: str
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """Prepare normalized feature matrix for a position group.

        Args:
            df: DataFrame with player data
            position_group: Position group to filter/prepare for

        Returns:
            Tuple of (filtered DataFrame, normalized feature matrix)
        """
        # Filter to players in this position group
        positions = POSITION_GROUPS.get(position_group, [position_group])
        mask = df["position"].str.upper().isin(positions)
        filtered = df[mask].copy()

        if filtered.empty:
            return filtered, np.array([])

        # Get available features
        features = self._get_feature_columns(position_group)

        if not features:
            logger.warning(f"No features available for {position_group}")
            return filtered, np.array([])

        # Extract feature matrix
        matrix = filtered[features].copy()

        # Handle inverse features (lower is better)
        for col in features:
            if col in INVERSE_FEATURES and col in matrix.columns:
                # Invert so higher is always better
                max_val = matrix[col].max()
                if max_val > 0:
                    matrix[col] = max_val - matrix[col]

        # Fill NaN with column median (better than 0 for similarity)
        matrix = matrix.fillna(matrix.median())

        # Normalize
        if len(matrix) > 1:
            matrix_normalized = self.scaler.fit_transform(matrix)
        else:
            matrix_normalized = matrix.values

        # Apply weights
        weights = self._get_feature_weights(position_group, features)
        matrix_weighted = matrix_normalized * weights

        return filtered, matrix_weighted

    def _calculate_similarity(
        self,
        player_features: np.ndarray,
        comparison_matrix: np.ndarray,
        min_features: int = 3
    ) -> np.ndarray:
        """Calculate similarity scores.

        Args:
            player_features: Feature vector for target player
            comparison_matrix: Feature matrix for comparison players
            min_features: Minimum features needed for valid comparison

        Returns:
            Array of similarity scores (0-100)
        """
        if comparison_matrix.size == 0 or player_features.size == 0:
            return np.array([])

        # Count non-NaN features
        valid_features = ~np.isnan(player_features)
        if valid_features.sum() < min_features:
            logger.warning("Not enough valid features for comparison")
            return np.zeros(len(comparison_matrix))

        # Cosine similarity
        similarities = cosine_similarity([player_features], comparison_matrix)[0]

        # Scale to 0-100
        similarities = (similarities + 1) * 50  # Convert -1,1 to 0,100

        return similarities

    @log_execution_time()
    def find_similar_players(
        self,
        player_name: str,
        position: Optional[str] = None,
        top_n: int = 10,
        min_similarity: float = 50.0,
        exclude_same_team: bool = False,
        portal_only: bool = False
    ) -> pd.DataFrame:
        """Find players most similar to target based on position metrics.

        Args:
            player_name: Name of player to find comparisons for
            position: Player's position (auto-detected if not provided)
            top_n: Number of similar players to return
            min_similarity: Minimum similarity score (0-100)
            exclude_same_team: Exclude players from same team
            portal_only: Only return players currently in portal

        Returns:
            DataFrame with similar players and similarity scores
        """
        # Find target player
        name_lower = player_name.lower().strip()
        target_mask = self.pff["name"].str.lower() == name_lower

        if not target_mask.any():
            # Try partial match
            target_mask = self.pff["name"].str.lower().str.contains(name_lower, na=False)

        if not target_mask.any():
            logger.warning(f"Player not found: {player_name}")
            return pd.DataFrame()

        target = self.pff[target_mask].iloc[0]
        target_name = target["name"]

        # Get position group
        if position:
            pos_group = get_position_group(position)
        elif "position" in target:
            pos_group = get_position_group(target["position"])
        else:
            pos_group = "QB"

        # Prepare comparison pool
        comparison_df = self.pff.copy()

        # Filter to same position group
        positions = POSITION_GROUPS.get(pos_group, [pos_group])
        comparison_df = comparison_df[
            comparison_df["position"].str.upper().isin(positions)
        ]

        # Exclude target player
        comparison_df = comparison_df[comparison_df["name"] != target_name]

        # Optionally filter to portal only
        if portal_only and not self.portal.empty:
            portal_names = set(self.portal["name"].str.lower())
            comparison_df = comparison_df[
                comparison_df["name"].str.lower().isin(portal_names)
            ]

        # Optionally exclude same team
        if exclude_same_team and "team" in target and "team" in comparison_df.columns:
            comparison_df = comparison_df[comparison_df["team"] != target["team"]]

        if comparison_df.empty:
            logger.info("No comparison players found")
            return pd.DataFrame()

        # Prepare feature matrices
        _, target_features = self._prepare_feature_matrix(
            self.pff[target_mask], pos_group
        )
        filtered_df, comparison_matrix = self._prepare_feature_matrix(
            comparison_df, pos_group
        )

        if target_features.size == 0 or comparison_matrix.size == 0:
            return pd.DataFrame()

        # Calculate similarities
        similarities = self._calculate_similarity(
            target_features[0], comparison_matrix
        )

        # Add to DataFrame
        filtered_df = filtered_df.copy()
        filtered_df["similarity"] = similarities

        # Filter by minimum similarity
        filtered_df = filtered_df[filtered_df["similarity"] >= min_similarity]

        # Sort and limit
        result = filtered_df.nlargest(top_n, "similarity")

        # Add helpful columns
        result["position_group"] = pos_group
        result["comparison_to"] = target_name

        # Select output columns
        output_cols = [
            "name", "position", "team", "similarity",
            "pff_overall", "position_group", "comparison_to"
        ]

        # Add season if available
        if "season" in result.columns:
            output_cols.insert(4, "season")

        available_cols = [c for c in output_cols if c in result.columns]

        return result[available_cols].round({"similarity": 1})

    def find_similar_in_portal(
        self,
        player_name: str,
        position: Optional[str] = None,
        top_n: int = 5
    ) -> pd.DataFrame:
        """Find similar players currently in the transfer portal.

        Args:
            player_name: Name of player to find comparisons for
            position: Player's position
            top_n: Number of results

        Returns:
            DataFrame with similar portal players
        """
        return self.find_similar_players(
            player_name,
            position=position,
            top_n=top_n,
            portal_only=True
        )

    def get_player_profile(self, player_name: str) -> Dict[str, Any]:
        """Get a player's profile with key metrics.

        Args:
            player_name: Player name

        Returns:
            Dict with player info and metrics
        """
        name_lower = player_name.lower().strip()
        mask = self.pff["name"].str.lower() == name_lower

        if not mask.any():
            mask = self.pff["name"].str.lower().str.contains(name_lower, na=False)

        if not mask.any():
            return {}

        player = self.pff[mask].iloc[0]
        pos_group = get_position_group(player.get("position", "QB"))

        # Get position-specific key metrics
        features = POSITION_FEATURES.get(pos_group, {})
        key_metrics = {}

        for metric, weight in sorted(features.items(), key=lambda x: -x[1])[:5]:
            if metric in player and pd.notna(player[metric]):
                key_metrics[metric] = player[metric]

        return {
            "name": player.get("name"),
            "position": player.get("position"),
            "team": player.get("team"),
            "position_group": pos_group,
            "pff_overall": player.get("pff_overall"),
            "key_metrics": key_metrics
        }

    def compare_two_players(
        self,
        player1_name: str,
        player2_name: str
    ) -> Dict[str, Any]:
        """Compare two specific players head-to-head.

        Args:
            player1_name: First player name
            player2_name: Second player name

        Returns:
            Dict with comparison results
        """
        profile1 = self.get_player_profile(player1_name)
        profile2 = self.get_player_profile(player2_name)

        if not profile1 or not profile2:
            return {"error": "One or both players not found"}

        # Determine position group (use first player's)
        pos_group = profile1.get("position_group", "QB")

        # Get features for comparison
        features = self._get_feature_columns(pos_group)

        # Extract values
        p1 = self.pff[self.pff["name"].str.lower() == player1_name.lower()].iloc[0]
        p2 = self.pff[self.pff["name"].str.lower() == player2_name.lower()].iloc[0]

        comparison = {}
        for f in features[:10]:  # Top 10 metrics
            if f in p1 and f in p2:
                v1 = p1[f] if pd.notna(p1[f]) else None
                v2 = p2[f] if pd.notna(p2[f]) else None

                if v1 is not None and v2 is not None:
                    # Determine who's better
                    if f in INVERSE_FEATURES:
                        winner = player1_name if v1 < v2 else player2_name
                    else:
                        winner = player1_name if v1 > v2 else player2_name

                    comparison[f] = {
                        player1_name: round(v1, 2),
                        player2_name: round(v2, 2),
                        "advantage": winner
                    }

        return {
            "player1": profile1,
            "player2": profile2,
            "metrics": comparison,
            "position_group": pos_group
        }


# =============================================================================
# Convenience Functions
# =============================================================================

def find_similar_players(
    player_name: str,
    pff_data: pd.DataFrame,
    portal_data: Optional[pd.DataFrame] = None,
    position: Optional[str] = None,
    top_n: int = 10
) -> pd.DataFrame:
    """Convenience function to find similar players.

    Args:
        player_name: Name of player
        pff_data: DataFrame with PFF grades
        portal_data: Optional portal data
        position: Player's position
        top_n: Number of results

    Returns:
        DataFrame with similar players
    """
    engine = PlayerComparison(pff_data, portal_data)
    return engine.find_similar_players(player_name, position, top_n)


def get_player_comps_for_card(
    player_name: str,
    pff_data: pd.DataFrame,
    portal_data: Optional[pd.DataFrame] = None,
    num_comps: int = 3
) -> List[Dict[str, Any]]:
    """Get player comparisons formatted for UI cards.

    Args:
        player_name: Player name
        pff_data: PFF data
        portal_data: Portal data
        num_comps: Number of comparisons

    Returns:
        List of comp dicts with name, team, similarity
    """
    engine = PlayerComparison(pff_data, portal_data)
    similar = engine.find_similar_players(player_name, top_n=num_comps)

    if similar.empty:
        return []

    comps = []
    for _, row in similar.iterrows():
        comps.append({
            "name": row["name"],
            "team": row.get("team", "Unknown"),
            "similarity": row["similarity"],
            "pff_overall": row.get("pff_overall"),
        })

    return comps
