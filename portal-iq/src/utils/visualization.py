"""
Visualization Utilities

Charts and visualizations for Portal IQ data.
"""

import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .config import Config


class Visualizer:
    """Creates visualizations for Portal IQ data."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the visualizer.

        Args:
            config: Configuration object
        """
        self.config = config or Config()
        self.output_dir = Path(
            self.config.data_paths.get("figures", "outputs/figures")
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set style
        plt.style.use("seaborn-v0_8-whitegrid")
        self.colors = px.colors.qualitative.Set2

    def nil_distribution(
        self,
        df: pd.DataFrame,
        by: str = "position",
        save: bool = False,
    ) -> go.Figure:
        """
        Create NIL valuation distribution chart.

        Args:
            df: DataFrame with NIL valuations
            by: Column to group by
            save: Whether to save the figure

        Returns:
            Plotly figure
        """
        fig = px.box(
            df,
            x=by,
            y="nil_valuation",
            color=by,
            title=f"NIL Valuation Distribution by {by.title()}",
            labels={"nil_valuation": "NIL Valuation ($)"},
        )

        fig.update_layout(
            showlegend=False,
            yaxis_tickformat="$,.0f",
        )

        if save:
            fig.write_html(self.output_dir / "nil_distribution.html")

        return fig

    def nil_leaderboard(
        self,
        df: pd.DataFrame,
        top_n: int = 20,
        save: bool = False,
    ) -> go.Figure:
        """
        Create NIL leaderboard bar chart.

        Args:
            df: DataFrame with NIL valuations
            top_n: Number of top players to show
            save: Whether to save the figure

        Returns:
            Plotly figure
        """
        top_players = df.nlargest(top_n, "nil_valuation")

        fig = px.bar(
            top_players,
            x="nil_valuation",
            y="player_name",
            color="position",
            orientation="h",
            title=f"Top {top_n} NIL Valuations",
            labels={"nil_valuation": "NIL Valuation ($)", "player_name": ""},
        )

        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_tickformat="$,.0f",
        )

        if save:
            fig.write_html(self.output_dir / "nil_leaderboard.html")

        return fig

    def portal_flow_sankey(
        self,
        df: pd.DataFrame,
        save: bool = False,
    ) -> go.Figure:
        """
        Create Sankey diagram of portal transfers.

        Args:
            df: DataFrame with portal data (origin, destination columns)
            save: Whether to save the figure

        Returns:
            Plotly figure
        """
        # Get unique schools
        origins = df["origin"].unique().tolist()
        destinations = df["destination"].dropna().unique().tolist()
        all_schools = list(set(origins + destinations))

        # Create node indices
        node_map = {school: i for i, school in enumerate(all_schools)}

        # Create links
        links = df.groupby(["origin", "destination"]).size().reset_index(name="count")
        links = links[links["destination"].notna()]

        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_schools,
            ),
            link=dict(
                source=[node_map[o] for o in links["origin"]],
                target=[node_map[d] for d in links["destination"]],
                value=links["count"],
            )
        )])

        fig.update_layout(title="Transfer Portal Flow")

        if save:
            fig.write_html(self.output_dir / "portal_flow.html")

        return fig

    def draft_projection_scatter(
        self,
        df: pd.DataFrame,
        save: bool = False,
    ) -> go.Figure:
        """
        Create draft projection scatter plot.

        Args:
            df: DataFrame with draft projections
            save: Whether to save the figure

        Returns:
            Plotly figure
        """
        fig = px.scatter(
            df,
            x="draft_grade",
            y="projected_pick",
            color="position",
            size="draft_probability",
            hover_data=["player_name", "school"],
            title="Draft Projections",
            labels={
                "draft_grade": "Draft Grade",
                "projected_pick": "Projected Pick",
            },
        )

        fig.update_layout(
            yaxis={"autorange": "reversed"},
        )

        if save:
            fig.write_html(self.output_dir / "draft_projections.html")

        return fig

    def roster_composition(
        self,
        df: pd.DataFrame,
        team: str,
        save: bool = False,
    ) -> go.Figure:
        """
        Create roster composition treemap.

        Args:
            df: DataFrame with roster data
            team: Team name
            save: Whether to save the figure

        Returns:
            Plotly figure
        """
        roster = df[df["team"] == team] if "team" in df.columns else df

        fig = px.treemap(
            roster,
            path=["position_group", "position", "player_name"],
            values="player_value" if "player_value" in roster.columns else None,
            title=f"{team} Roster Composition",
        )

        if save:
            fig.write_html(self.output_dir / f"roster_{team.lower()}.html")

        return fig

    def win_projection_gauge(
        self,
        projected_wins: float,
        win_range: Tuple[float, float],
        team: str,
        save: bool = False,
    ) -> go.Figure:
        """
        Create win projection gauge chart.

        Args:
            projected_wins: Projected win total
            win_range: (low, high) win range
            team: Team name
            save: Whether to save the figure

        Returns:
            Plotly figure
        """
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=projected_wins,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"{team} Win Projection"},
            delta={"reference": 8},
            gauge={
                "axis": {"range": [0, 15]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 6], "color": "lightcoral"},
                    {"range": [6, 9], "color": "lightyellow"},
                    {"range": [9, 12], "color": "lightgreen"},
                    {"range": [12, 15], "color": "green"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": win_range[0],
                },
            },
        ))

        if save:
            fig.write_html(self.output_dir / f"wins_{team.lower()}.html")

        return fig

    def feature_importance_bar(
        self,
        importance_df: pd.DataFrame,
        title: str = "Feature Importance",
        top_n: int = 15,
        save: bool = False,
    ) -> go.Figure:
        """
        Create feature importance bar chart.

        Args:
            importance_df: DataFrame with feature and importance columns
            title: Chart title
            top_n: Number of top features to show
            save: Whether to save the figure

        Returns:
            Plotly figure
        """
        top_features = importance_df.nlargest(top_n, "importance")

        fig = px.bar(
            top_features,
            x="importance",
            y="feature",
            orientation="h",
            title=title,
        )

        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
        )

        if save:
            fig.write_html(self.output_dir / "feature_importance.html")

        return fig

    def correlation_heatmap(
        self,
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        save: bool = False,
    ) -> plt.Figure:
        """
        Create correlation heatmap.

        Args:
            df: DataFrame with numerical columns
            columns: Specific columns to include
            save: Whether to save the figure

        Returns:
            Matplotlib figure
        """
        if columns:
            df = df[columns]

        # Select only numeric columns
        numeric_df = df.select_dtypes(include=[np.number])
        corr = numeric_df.corr()

        fig, ax = plt.subplots(figsize=(12, 10))
        sns.heatmap(
            corr,
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            center=0,
            ax=ax,
        )
        ax.set_title("Feature Correlations")

        if save:
            fig.savefig(self.output_dir / "correlations.png", dpi=150, bbox_inches="tight")

        return fig

    def save_dashboard_data(
        self,
        figures: Dict[str, go.Figure],
        name: str,
    ) -> Path:
        """
        Save multiple figures as an interactive HTML dashboard.

        Args:
            figures: Dictionary of figure name to figure
            name: Dashboard name

        Returns:
            Path to saved dashboard
        """
        html_parts = ["<html><head><title>Portal IQ Dashboard</title></head><body>"]

        for fig_name, fig in figures.items():
            html_parts.append(f"<h2>{fig_name}</h2>")
            html_parts.append(fig.to_html(full_html=False, include_plotlyjs="cdn"))

        html_parts.append("</body></html>")

        output_path = self.output_dir / f"{name}_dashboard.html"
        with open(output_path, "w") as f:
            f.write("\n".join(html_parts))

        return output_path
