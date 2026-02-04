"""
PocketBase Client for Portal IQ

Handles player stats, measurables, and custom data persistence.
CSV files serve as local backup when PocketBase is unavailable.

To connect:
1. Set POCKETBASE_URL environment variable (e.g., https://your-instance.pocketbase.io)
2. Set POCKETBASE_ADMIN_EMAIL and POCKETBASE_ADMIN_PASSWORD for admin operations
   OR use POCKETBASE_API_TOKEN for direct API access

Collections needed:
- player_stats: Production stats (passing_yards, rushing_yards, etc.)
- player_measurables: Height, weight, combine data
- player_pff_grades: PFF-specific grades (overall, pass_block, run_block, etc.)
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Local CSV backup paths
DATA_DIR = Path(__file__).parent.parent.parent / "ml-engine" / "data" / "processed"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MANUAL_STATS_FILE = DATA_DIR / "manual_player_stats.csv"
PLAYER_MEASURABLES_FILE = DATA_DIR / "player_measurables.csv"


class PocketBaseClient:
    """
    PocketBase client with CSV fallback for Portal IQ.

    When PocketBase is connected, data syncs to cloud.
    Always maintains local CSV backup for offline use.
    """

    def __init__(self):
        self.base_url = os.getenv("POCKETBASE_URL", "")
        self.admin_email = os.getenv("POCKETBASE_ADMIN_EMAIL", "")
        self.admin_password = os.getenv("POCKETBASE_ADMIN_PASSWORD", "")
        self.api_token = os.getenv("POCKETBASE_API_TOKEN", "")

        self._client = None
        self._connected = False

        if self.base_url:
            self._init_client()

    def _init_client(self):
        """Initialize PocketBase client if URL is configured."""
        try:
            # Import pocketbase only if configured
            from pocketbase import PocketBase

            self._client = PocketBase(self.base_url)

            # Authenticate if credentials provided
            if self.admin_email and self.admin_password:
                self._client.admins.auth_with_password(
                    self.admin_email,
                    self.admin_password
                )
                self._connected = True
                logger.info("PocketBase connected with admin auth")
            elif self.api_token:
                # Use API token auth
                self._client.auth_store.save(self.api_token, None)
                self._connected = True
                logger.info("PocketBase connected with API token")
            else:
                logger.warning("PocketBase URL set but no auth configured")

        except ImportError:
            logger.warning("pocketbase package not installed. Install with: pip install pocketbase")
        except Exception as e:
            logger.error(f"Failed to connect to PocketBase: {e}")

    @property
    def is_connected(self) -> bool:
        """Check if PocketBase is connected."""
        return self._connected

    # =========================================================================
    # PLAYER STATS OPERATIONS
    # =========================================================================

    def get_player_stats(self, player_name: str) -> Optional[Dict]:
        """
        Get stats for a player. Tries PocketBase first, falls back to CSV.

        Args:
            player_name: Player's full name

        Returns:
            Dict of player stats or None if not found
        """
        # Try PocketBase first
        if self._connected:
            try:
                result = self._client.collection("player_stats").get_list(
                    1, 1,
                    {"filter": f'player_name = "{player_name}"'}
                )
                if result.items:
                    return dict(result.items[0])
            except Exception as e:
                logger.warning(f"PocketBase query failed: {e}")

        # Fallback to CSV
        return self._get_from_csv(MANUAL_STATS_FILE, "player_name", player_name)

    def save_player_stats(self, player_name: str, team: str, position: str, stats: Dict) -> bool:
        """
        Save player stats. Syncs to PocketBase if connected, always saves to CSV.

        Args:
            player_name: Player's full name
            team: Player's team
            position: Player's position
            stats: Dict of stats to save

        Returns:
            True if saved successfully
        """
        record = {
            "player_name": player_name,
            "team": team,
            "position": position,
            "updated_at": datetime.utcnow().isoformat(),
            **stats
        }

        # Save to PocketBase if connected
        if self._connected:
            try:
                # Check if record exists
                existing = self._client.collection("player_stats").get_list(
                    1, 1,
                    {"filter": f'player_name = "{player_name}"'}
                )

                if existing.items:
                    # Update existing
                    self._client.collection("player_stats").update(
                        existing.items[0].id,
                        record
                    )
                else:
                    # Create new
                    self._client.collection("player_stats").create(record)

                logger.info(f"Saved stats to PocketBase for {player_name}")
            except Exception as e:
                logger.error(f"Failed to save to PocketBase: {e}")

        # Always save to CSV as backup
        return self._save_to_csv(MANUAL_STATS_FILE, "player_name", player_name, record)

    def get_all_player_stats(self) -> pd.DataFrame:
        """Get all player stats as DataFrame."""
        if self._connected:
            try:
                result = self._client.collection("player_stats").get_full_list()
                if result:
                    return pd.DataFrame([dict(item) for item in result])
            except Exception as e:
                logger.warning(f"PocketBase query failed: {e}")

        # Fallback to CSV
        if MANUAL_STATS_FILE.exists():
            return pd.read_csv(MANUAL_STATS_FILE)
        return pd.DataFrame()

    # =========================================================================
    # PLAYER MEASURABLES OPERATIONS
    # =========================================================================

    def get_player_measurables(self, player_name: str) -> Optional[Dict]:
        """Get measurables (height, weight, etc.) for a player."""
        if self._connected:
            try:
                result = self._client.collection("player_measurables").get_list(
                    1, 1,
                    {"filter": f'player_name = "{player_name}"'}
                )
                if result.items:
                    return dict(result.items[0])
            except Exception as e:
                logger.warning(f"PocketBase query failed: {e}")

        return self._get_from_csv(PLAYER_MEASURABLES_FILE, "player_name", player_name)

    def save_player_measurables(self, player_name: str, measurables: Dict) -> bool:
        """Save player measurables."""
        record = {
            "player_name": player_name,
            "updated_at": datetime.utcnow().isoformat(),
            **measurables
        }

        if self._connected:
            try:
                existing = self._client.collection("player_measurables").get_list(
                    1, 1,
                    {"filter": f'player_name = "{player_name}"'}
                )

                if existing.items:
                    self._client.collection("player_measurables").update(
                        existing.items[0].id,
                        record
                    )
                else:
                    self._client.collection("player_measurables").create(record)

                logger.info(f"Saved measurables to PocketBase for {player_name}")
            except Exception as e:
                logger.error(f"Failed to save to PocketBase: {e}")

        return self._save_to_csv(PLAYER_MEASURABLES_FILE, "player_name", player_name, record)

    # =========================================================================
    # CSV HELPERS (Local Backup)
    # =========================================================================

    def _get_from_csv(self, filepath: Path, key_col: str, key_val: str) -> Optional[Dict]:
        """Get a record from CSV by key."""
        if not filepath.exists():
            return None

        try:
            df = pd.read_csv(filepath)
            match = df[df[key_col] == key_val]
            if not match.empty:
                return match.iloc[0].to_dict()
        except Exception as e:
            logger.error(f"Failed to read CSV {filepath}: {e}")

        return None

    def _save_to_csv(self, filepath: Path, key_col: str, key_val: str, record: Dict) -> bool:
        """Save a record to CSV, updating if exists."""
        try:
            if filepath.exists():
                df = pd.read_csv(filepath)
            else:
                df = pd.DataFrame()

            if df.empty:
                df = pd.DataFrame([record])
            else:
                mask = df[key_col] == key_val
                if mask.any():
                    for key, value in record.items():
                        if key in df.columns:
                            df.loc[mask, key] = value
                        else:
                            df[key] = None
                            df.loc[mask, key] = value
                else:
                    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)

            df.to_csv(filepath, index=False)
            return True

        except Exception as e:
            logger.error(f"Failed to save to CSV {filepath}: {e}")
            return False

    # =========================================================================
    # SYNC OPERATIONS
    # =========================================================================

    def sync_csv_to_pocketbase(self) -> Dict[str, int]:
        """
        Sync all local CSV data to PocketBase.

        Returns:
            Dict with counts of synced records per collection
        """
        if not self._connected:
            return {"error": "PocketBase not connected"}

        synced = {"player_stats": 0, "player_measurables": 0}

        # Sync player stats
        if MANUAL_STATS_FILE.exists():
            df = pd.read_csv(MANUAL_STATS_FILE)
            for _, row in df.iterrows():
                record = row.to_dict()
                player_name = record.get("player_name")
                if player_name:
                    try:
                        existing = self._client.collection("player_stats").get_list(
                            1, 1,
                            {"filter": f'player_name = "{player_name}"'}
                        )
                        if existing.items:
                            self._client.collection("player_stats").update(
                                existing.items[0].id,
                                record
                            )
                        else:
                            self._client.collection("player_stats").create(record)
                        synced["player_stats"] += 1
                    except Exception as e:
                        logger.error(f"Failed to sync {player_name}: {e}")

        # Sync measurables
        if PLAYER_MEASURABLES_FILE.exists():
            df = pd.read_csv(PLAYER_MEASURABLES_FILE)
            for _, row in df.iterrows():
                record = row.to_dict()
                player_name = record.get("player_name")
                if player_name:
                    try:
                        existing = self._client.collection("player_measurables").get_list(
                            1, 1,
                            {"filter": f'player_name = "{player_name}"'}
                        )
                        if existing.items:
                            self._client.collection("player_measurables").update(
                                existing.items[0].id,
                                record
                            )
                        else:
                            self._client.collection("player_measurables").create(record)
                        synced["player_measurables"] += 1
                    except Exception as e:
                        logger.error(f"Failed to sync {player_name}: {e}")

        return synced


# Global client instance
_client: Optional[PocketBaseClient] = None


def get_pocketbase_client() -> PocketBaseClient:
    """Get or create the global PocketBase client."""
    global _client
    if _client is None:
        _client = PocketBaseClient()
    return _client


# Convenience functions
def get_player_stats(player_name: str) -> Optional[Dict]:
    """Get stats for a player."""
    return get_pocketbase_client().get_player_stats(player_name)


def save_player_stats(player_name: str, team: str, position: str, stats: Dict) -> bool:
    """Save player stats."""
    return get_pocketbase_client().save_player_stats(player_name, team, position, stats)


def get_player_measurables(player_name: str) -> Optional[Dict]:
    """Get measurables for a player."""
    return get_pocketbase_client().get_player_measurables(player_name)


def save_player_measurables(player_name: str, measurables: Dict) -> bool:
    """Save player measurables."""
    return get_pocketbase_client().save_player_measurables(player_name, measurables)


def is_pocketbase_connected() -> bool:
    """Check if PocketBase is connected."""
    return get_pocketbase_client().is_connected


# =============================================================================
# PFF GRADES OPERATIONS
# =============================================================================

def get_pff_grades(player_name: str, season: Optional[int] = None) -> Optional[Dict]:
    """
    Get PFF grades for a player.

    Args:
        player_name: Player's full name
        season: Optional season filter (e.g., 2024)

    Returns:
        Dict with core grades and stats_json, or None if not found
    """
    client = get_pocketbase_client()

    if client.is_connected:
        try:
            filter_str = f'name ~ "{player_name}"'
            if season:
                filter_str += f' && season = {season}'

            result = client._client.collection("pff_grades").get_list(
                1, 1,
                {"filter": filter_str, "sort": "-season"}  # Most recent first
            )

            if result.items:
                record = dict(result.items[0])
                # Merge stats_json into main dict for easy access
                stats_json = record.pop("stats_json", {})
                if isinstance(stats_json, str):
                    import json
                    stats_json = json.loads(stats_json)
                return {**record, **stats_json}

        except Exception as e:
            logger.warning(f"PocketBase PFF query failed: {e}")

    return None


def get_all_pff_grades(season: Optional[int] = None, position: Optional[str] = None) -> pd.DataFrame:
    """
    Get all PFF grades as DataFrame.

    Args:
        season: Optional season filter
        position: Optional position filter (e.g., "QB", "WR")

    Returns:
        DataFrame with all PFF data
    """
    client = get_pocketbase_client()

    if client.is_connected:
        try:
            filters = []
            if season:
                filters.append(f'season = {season}')
            if position:
                filters.append(f'position = "{position}"')

            filter_str = " && ".join(filters) if filters else ""

            result = client._client.collection("pff_grades").get_full_list(
                query_params={"filter": filter_str} if filter_str else {}
            )

            if result:
                records = []
                for item in result:
                    record = dict(item)
                    stats_json = record.pop("stats_json", {})
                    if isinstance(stats_json, str):
                        import json
                        stats_json = json.loads(stats_json)
                    records.append({**record, **stats_json})
                return pd.DataFrame(records)

        except Exception as e:
            logger.warning(f"PocketBase PFF query failed: {e}")

    # Fallback to CSV
    csv_path = DATA_DIR / "pff_player_grades.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if season:
            df = df[df["season"] == season]
        if position:
            df = df[df["position"] == position]
        return df

    return pd.DataFrame()


def search_pff_players(
    query: str,
    season: Optional[int] = None,
    position: Optional[str] = None,
    team: Optional[str] = None,
    min_overall: Optional[float] = None,
    limit: int = 50
) -> pd.DataFrame:
    """
    Search PFF players with filters.

    Args:
        query: Search term (player name)
        season: Optional season filter
        position: Optional position filter
        team: Optional team filter
        min_overall: Minimum PFF overall grade
        limit: Max results to return

    Returns:
        DataFrame of matching players
    """
    client = get_pocketbase_client()

    if client.is_connected:
        try:
            filters = []
            if query:
                filters.append(f'name ~ "{query}"')
            if season:
                filters.append(f'season = {season}')
            if position:
                filters.append(f'position = "{position}"')
            if team:
                filters.append(f'team ~ "{team}"')
            if min_overall:
                filters.append(f'pff_overall >= {min_overall}')

            filter_str = " && ".join(filters) if filters else ""

            result = client._client.collection("pff_grades").get_list(
                1, limit,
                {"filter": filter_str, "sort": "-pff_overall"}
            )

            if result.items:
                records = []
                for item in result.items:
                    record = dict(item)
                    stats_json = record.pop("stats_json", {})
                    if isinstance(stats_json, str):
                        import json
                        stats_json = json.loads(stats_json)
                    records.append({**record, **stats_json})
                return pd.DataFrame(records)

        except Exception as e:
            logger.warning(f"PocketBase search failed: {e}")

    return pd.DataFrame()
