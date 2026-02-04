"""
Penalty Data Extractor from CFBD Play-by-Play

Extracts individual player penalties from CFBD play-by-play data.
Penalty types: Holding, False Start, Offsides, Pass Interference, etc.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

import pandas as pd
from dotenv import load_dotenv

try:
    import cfbd
    from cfbd.rest import ApiException
    CFBD_AVAILABLE = True
except ImportError:
    CFBD_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Penalty patterns to extract from play descriptions
PENALTY_PATTERNS = {
    # Offensive penalties
    "holding": r"(?:Offensive )?[Hh]olding(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "false_start": r"[Ff]alse [Ss]tart(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "illegal_formation": r"[Ii]llegal [Ff]ormation(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "illegal_shift": r"[Ii]llegal [Ss]hift(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "illegal_motion": r"[Ii]llegal [Mm]otion(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "delay_of_game": r"[Dd]elay of [Gg]ame(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "intentional_grounding": r"[Ii]ntentional [Gg]rounding(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",

    # Defensive penalties
    "offsides": r"[Oo]ffsides(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "encroachment": r"[Ee]ncroachment(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "neutral_zone": r"[Nn]eutral [Zz]one(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "roughing_passer": r"[Rr]oughing the [Pp]asser(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "roughing_kicker": r"[Rr]oughing the [Kk]icker(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "pass_interference_def": r"[Dd]efensive [Pp]ass [Ii]nterference(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "defensive_holding": r"[Dd]efensive [Hh]olding(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",

    # Special teams penalties
    "illegal_block": r"[Ii]llegal [Bb]lock(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "kick_catch_interference": r"[Kk]ick [Cc]atch [Ii]nterference(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",

    # Personal fouls
    "unsportsmanlike": r"[Uu]nsportsmanlike [Cc]onduct(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "personal_foul": r"[Pp]ersonal [Ff]oul(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "targeting": r"[Tt]argeting(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "facemask": r"[Ff]acemask(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
    "late_hit": r"[Ll]ate [Hh]it(?:,| on| -) ([A-Z][a-z]+ [A-Z][A-Za-z'-]+)",
}


class PenaltyExtractor:
    """Extract penalty data from CFBD play-by-play."""

    def __init__(self):
        load_dotenv()

        if not CFBD_AVAILABLE:
            raise ImportError("cfbd package required: pip install cfbd")

        self.api_key = os.getenv("CFBD_API_KEY")
        if not self.api_key:
            raise ValueError("CFBD_API_KEY environment variable required")

        self.configuration = cfbd.Configuration(access_token=self.api_key)

    def get_plays_for_team(self, team: str, year: int = 2024) -> List[Dict]:
        """Get all plays for a team in a season."""
        api = cfbd.PlaysApi(cfbd.ApiClient(self.configuration))

        all_plays = []
        for week in range(1, 16):  # Regular season weeks
            try:
                plays = api.get_plays(year=year, week=week, team=team)
                for play in plays:
                    all_plays.append({
                        "week": week,
                        "game_id": play.game_id,
                        "play_type": play.play_type,
                        "play_text": play.play_text or "",
                        "offense": play.offense,
                        "defense": play.defense,
                        "down": play.down,
                        "distance": play.distance,
                    })
            except ApiException as e:
                logger.warning(f"Error fetching week {week} for {team}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error week {week}: {e}")

        return all_plays

    def extract_penalties_from_plays(self, plays: List[Dict], team: str) -> Dict[str, Dict]:
        """Extract individual player penalties from play descriptions."""
        player_penalties = defaultdict(lambda: defaultdict(int))

        for play in plays:
            play_text = play.get("play_text", "")
            if not play_text:
                continue

            # Only count penalties against our team
            is_offense = play.get("offense") == team
            is_defense = play.get("defense") == team

            for penalty_type, pattern in PENALTY_PATTERNS.items():
                matches = re.findall(pattern, play_text)
                for player_name in matches:
                    # Determine if this penalty is against our team
                    offensive_penalties = ["holding", "false_start", "illegal_formation",
                                          "illegal_shift", "illegal_motion", "delay_of_game",
                                          "intentional_grounding"]
                    defensive_penalties = ["offsides", "encroachment", "neutral_zone",
                                          "roughing_passer", "roughing_kicker",
                                          "pass_interference_def", "defensive_holding"]

                    if penalty_type in offensive_penalties and is_offense:
                        player_penalties[player_name][penalty_type] += 1
                        player_penalties[player_name]["total"] += 1
                    elif penalty_type in defensive_penalties and is_defense:
                        player_penalties[player_name][penalty_type] += 1
                        player_penalties[player_name]["total"] += 1
                    elif penalty_type not in offensive_penalties + defensive_penalties:
                        # Personal fouls, unsportsmanlike, etc.
                        player_penalties[player_name][penalty_type] += 1
                        player_penalties[player_name]["total"] += 1

        return dict(player_penalties)

    def collect_team_penalties(self, team: str, year: int = 2024) -> pd.DataFrame:
        """Collect all penalty data for a team."""
        logger.info(f"Collecting penalties for {team} ({year})...")

        plays = self.get_plays_for_team(team, year)
        logger.info(f"Found {len(plays)} plays for {team}")

        penalties = self.extract_penalties_from_plays(plays, team)

        # Convert to DataFrame
        records = []
        for player, penalty_counts in penalties.items():
            record = {
                "player_name": player,
                "team": team,
                "season": year,
                **penalty_counts
            }
            records.append(record)

        df = pd.DataFrame(records)

        if not df.empty:
            # Sort by total penalties
            df = df.sort_values("total", ascending=False)
            logger.info(f"Found {len(df)} players with penalties")

        return df

    def collect_all_teams(self, year: int = 2024, teams: List[str] = None) -> pd.DataFrame:
        """Collect penalty data for all FBS teams."""
        if teams is None:
            # Get FBS teams
            api = cfbd.TeamsApi(cfbd.ApiClient(self.configuration))
            fbs_teams = api.get_fbs_teams(year=year)
            teams = [t.school for t in fbs_teams]

        all_dfs = []
        for i, team in enumerate(teams):
            logger.info(f"Processing {team} ({i+1}/{len(teams)})")
            try:
                df = self.collect_team_penalties(team, year)
                if not df.empty:
                    all_dfs.append(df)
            except Exception as e:
                logger.error(f"Error processing {team}: {e}")

            # Rate limiting
            import time
            time.sleep(0.5)

        if all_dfs:
            combined = pd.concat(all_dfs, ignore_index=True)
            return combined

        return pd.DataFrame()


def main():
    """Run penalty extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract penalty data from CFBD")
    parser.add_argument("--year", type=int, default=2024, help="Season year")
    parser.add_argument("--team", type=str, help="Single team to process (optional)")
    parser.add_argument("--output", type=str, default="penalties.csv", help="Output file")
    args = parser.parse_args()

    extractor = PenaltyExtractor()

    if args.team:
        df = extractor.collect_team_penalties(args.team, args.year)
    else:
        # Process a few teams for testing
        test_teams = ["Alabama", "Ohio State", "Georgia", "Texas", "Michigan"]
        df = extractor.collect_all_teams(args.year, test_teams)

    if not df.empty:
        output_path = Path(__file__).parent.parent.parent.parent / "data" / "processed" / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved to {output_path}")
        print(df.head(20))
    else:
        logger.warning("No penalty data extracted")


if __name__ == "__main__":
    main()
