"""
Roster Optimizer

Optimizes roster composition using linear programming and constraints.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from pulp import (
    LpProblem, LpMaximize, LpVariable, LpBinary,
    lpSum, LpStatus, value
)

from ..utils.config import Config
from .win_model import WinImpactModel
from .nil_valuator import NILValuator


class RosterOptimizer:
    """Optimizes roster construction within NIL and scholarship constraints."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the roster optimizer.

        Args:
            config: Configuration object with settings
        """
        self.config = config or Config()
        self.win_model = WinImpactModel(config)
        self.nil_valuator = NILValuator(config)

    def optimize_portal_targets(
        self,
        current_roster: pd.DataFrame,
        available_players: pd.DataFrame,
        budget: float,
        max_additions: int = 10,
        position_needs: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize portal target selection.

        Args:
            current_roster: Current roster DataFrame
            available_players: Available transfer targets
            budget: NIL budget constraint
            max_additions: Maximum number of additions
            position_needs: Dictionary of position needs

        Returns:
            Dictionary with optimization results
        """
        # Create optimization problem
        prob = LpProblem("Portal_Optimization", LpMaximize)

        # Decision variables: binary for each player
        players = available_players.index.tolist()
        x = LpVariable.dicts("select", players, cat=LpBinary)

        # Calculate player values (WAR)
        player_values = {}
        player_costs = {}
        player_positions = {}

        for idx, player in available_players.iterrows():
            # Calculate win impact
            war = self.win_model.calculate_player_war(
                player.to_dict(),
                {}
            )
            player_values[idx] = war

            # Get NIL cost
            nil_value = player.get("nil_valuation", 100000)
            player_costs[idx] = nil_value

            # Get position
            player_positions[idx] = player.get("position", "")

        # Objective: maximize total WAR
        prob += lpSum([player_values[p] * x[p] for p in players])

        # Constraint: budget
        prob += lpSum([player_costs[p] * x[p] for p in players]) <= budget

        # Constraint: max additions
        prob += lpSum([x[p] for p in players]) <= max_additions

        # Constraint: position needs
        if position_needs:
            for position, need in position_needs.items():
                position_players = [
                    p for p in players
                    if player_positions[p] == position
                ]
                if position_players:
                    prob += lpSum([x[p] for p in position_players]) >= min(
                        need, len(position_players)
                    )

        # Solve
        prob.solve()

        # Extract results
        selected_players = [
            p for p in players if value(x[p]) == 1
        ]

        selected_df = available_players.loc[selected_players].copy()
        selected_df["war"] = [player_values[p] for p in selected_players]
        selected_df["nil_cost"] = [player_costs[p] for p in selected_players]

        return {
            "status": LpStatus[prob.status],
            "selected_players": selected_df,
            "total_war": sum(player_values[p] for p in selected_players),
            "total_cost": sum(player_costs[p] for p in selected_players),
            "budget_remaining": budget - sum(player_costs[p] for p in selected_players),
        }

    def allocate_nil_budget(
        self,
        roster: pd.DataFrame,
        total_budget: float,
        strategy: str = "balanced",
    ) -> pd.DataFrame:
        """
        Allocate NIL budget across roster.

        Args:
            roster: Current roster DataFrame
            total_budget: Total NIL budget
            strategy: Allocation strategy (balanced, top_heavy, positional)

        Returns:
            DataFrame with NIL allocations
        """
        roster = roster.copy()

        if strategy == "balanced":
            # Allocate based on player value
            roster["player_value"] = roster.apply(
                lambda x: self.win_model.calculate_player_war(x.to_dict(), {}),
                axis=1
            )
            total_value = roster["player_value"].sum()

            if total_value > 0:
                roster["nil_allocation"] = (
                    roster["player_value"] / total_value * total_budget
                )
            else:
                roster["nil_allocation"] = total_budget / len(roster)

        elif strategy == "top_heavy":
            # Heavy allocation to top players
            roster["player_value"] = roster.apply(
                lambda x: self.win_model.calculate_player_war(x.to_dict(), {}),
                axis=1
            )
            roster = roster.sort_values("player_value", ascending=False)

            # Top 20% get 60% of budget
            n_top = max(1, len(roster) // 5)
            top_budget = total_budget * 0.6
            remaining_budget = total_budget * 0.4

            roster["nil_allocation"] = 0.0
            roster.iloc[:n_top, roster.columns.get_loc("nil_allocation")] = top_budget / n_top
            if len(roster) > n_top:
                roster.iloc[n_top:, roster.columns.get_loc("nil_allocation")] = (
                    remaining_budget / (len(roster) - n_top)
                )

        elif strategy == "positional":
            # Allocate by position priority
            position_shares = {
                "QB": 0.25, "WR": 0.15, "EDGE": 0.12, "OT": 0.10,
                "CB": 0.08, "RB": 0.06, "LB": 0.06, "DL": 0.06,
                "TE": 0.04, "S": 0.04, "OG": 0.02, "C": 0.02,
            }

            roster["nil_allocation"] = roster["position"].map(
                lambda p: position_shares.get(p, 0.02) * total_budget
            )

            # Normalize to budget
            current_total = roster["nil_allocation"].sum()
            if current_total > 0:
                roster["nil_allocation"] *= total_budget / current_total

        return roster

    def build_optimal_roster(
        self,
        available_players: pd.DataFrame,
        scholarship_limit: int = 85,
        budget: float = 10_000_000,
    ) -> Dict[str, Any]:
        """
        Build an optimal roster from scratch.

        Args:
            available_players: All available players
            scholarship_limit: Scholarship limit
            budget: NIL budget

        Returns:
            Dictionary with optimal roster
        """
        # Position requirements
        position_requirements = {
            "QB": (2, 3),
            "RB": (3, 5),
            "WR": (6, 10),
            "TE": (2, 4),
            "OT": (3, 5),
            "OG": (3, 5),
            "C": (1, 2),
            "DE": (3, 5),
            "DT": (3, 5),
            "LB": (5, 8),
            "CB": (4, 6),
            "S": (3, 5),
            "K": (1, 2),
            "P": (1, 2),
        }

        prob = LpProblem("Roster_Build", LpMaximize)

        players = available_players.index.tolist()
        x = LpVariable.dicts("select", players, cat=LpBinary)

        # Calculate player values
        player_values = {}
        player_costs = {}
        player_positions = {}

        for idx, player in available_players.iterrows():
            war = self.win_model.calculate_player_war(player.to_dict(), {})
            player_values[idx] = war
            player_costs[idx] = player.get("nil_valuation", 50000)
            player_positions[idx] = player.get("position", "")

        # Objective: maximize WAR
        prob += lpSum([player_values[p] * x[p] for p in players])

        # Constraint: scholarship limit
        prob += lpSum([x[p] for p in players]) <= scholarship_limit

        # Constraint: budget
        prob += lpSum([player_costs[p] * x[p] for p in players]) <= budget

        # Constraint: position requirements
        for position, (min_req, max_req) in position_requirements.items():
            position_players = [
                p for p in players
                if player_positions[p] == position
            ]
            if position_players:
                prob += lpSum([x[p] for p in position_players]) >= min_req
                prob += lpSum([x[p] for p in position_players]) <= max_req

        prob.solve()

        selected = [p for p in players if value(x[p]) == 1]
        selected_df = available_players.loc[selected].copy()

        return {
            "status": LpStatus[prob.status],
            "roster": selected_df,
            "total_war": sum(player_values[p] for p in selected),
            "total_cost": sum(player_costs[p] for p in selected),
            "roster_size": len(selected),
        }

    def evaluate_trade(
        self,
        team_roster: pd.DataFrame,
        outgoing: List[str],
        incoming: List[Dict[str, Any]],
        nil_adjustment: float = 0,
    ) -> Dict[str, Any]:
        """
        Evaluate a potential trade/swap.

        Args:
            team_roster: Current roster
            outgoing: List of player IDs leaving
            incoming: List of player dicts coming in
            nil_adjustment: NIL cost difference

        Returns:
            Dictionary with trade evaluation
        """
        # Calculate current WAR for outgoing
        outgoing_war = 0
        for player_id in outgoing:
            player = team_roster[team_roster["player_id"] == player_id]
            if not player.empty:
                outgoing_war += self.win_model.calculate_player_war(
                    player.iloc[0].to_dict(), {}
                )

        # Calculate incoming WAR
        incoming_war = sum(
            self.win_model.calculate_player_war(p, {})
            for p in incoming
        )

        war_delta = incoming_war - outgoing_war

        return {
            "outgoing_war": outgoing_war,
            "incoming_war": incoming_war,
            "war_delta": war_delta,
            "nil_adjustment": nil_adjustment,
            "recommendation": "accept" if war_delta > 0 else "reject",
            "war_per_dollar": war_delta / max(abs(nil_adjustment), 1),
        }
