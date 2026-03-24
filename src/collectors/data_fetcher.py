# ============================================================
# src/collectors/data_fetcher.py
# ============================================================
# PURPOSE:
#   High-level data fetching logic that sits above the raw API client.
#   This module knows *what* to fetch (standings, team stats) and
#   how to loop across all leagues and seasons.
#
# ANALOGY:
#   If api_client.py is the librarian, this is the reading list —
#   it tells the librarian exactly which books to retrieve and
#   assembles them into a structured collection.
# ============================================================

import logging
from typing import List, Dict

import pandas as pd
from tqdm import tqdm

from config import LEAGUES, SEASONS, TOP_N_TEAMS, LOG_FORMAT, LOG_LEVEL
from src.collectors.api_client import APIFootballClient

# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


# ============================================================
# STANDINGS FETCHER
# ============================================================
def fetch_standings(client: APIFootballClient) -> pd.DataFrame:
    """
    Fetch league standings for all configured leagues and seasons.

    Standings give us:
    - Final position (rank) of each team
    - Points, wins, draws, losses
    - Goals For (GF) and Goals Against (GA = goals conceded)
    - Goal Difference

    This is the primary data source for our analysis since
    GA (goals against) is our key defensive metric.

    Args:
        client: Authenticated APIFootballClient instance

    Returns:
        DataFrame with one row per team-season-league combination.
    """
    all_rows: List[Dict] = []

    # Outer loop: each league
    for league_key, league_info in tqdm(LEAGUES.items(), desc="Leagues"):

        # Inner loop: each season
        for season in tqdm(
            SEASONS, desc=f"  {league_key} seasons", leave=False
        ):

            logger.info(
                f"Fetching standings: {league_key} | Season {season}"
            )

            try:
                response = client.get(
                    endpoint="standings",
                    params={
                        "league":  league_info["id"],
                        "season":  season,
                    }
                )
            except Exception as e:
                # Log the error but continue — don't let one bad season
                # kill the entire fetch pipeline
                logger.warning(
                    f"⚠️  Failed to fetch {league_key} {season}: {e}"
                )
                continue

            # --------------------------------------------------------
            # PARSE THE API RESPONSE
            # API-Football standings structure:
            # response[0] → league object
            #   → league.standings[0] → list of team objects
            # --------------------------------------------------------
            try:
                standings_data = (
                    response["response"][0]["league"]["standings"][0]
                )
            except (KeyError, IndexError) as e:
                logger.warning(
                    f"⚠️  Unexpected response structure "
                    f"for {league_key} {season}: {e}"
                )
                continue

            # Extract each team's row
            for team_entry in standings_data:
                row = _parse_standing_entry(
                    entry=team_entry,
                    league_key=league_key,
                    league_name=league_info["name"],
                    country=league_info["country"],
                    season=season,
                )
                all_rows.append(row)

    if not all_rows:
        raise RuntimeError(
            "No standings data was fetched. "
            "Check API key and league/season config."
        )

    df = pd.DataFrame(all_rows)
    logger.info(
        f"✅ Fetched {len(df)} team-season records "
        f"across {len(LEAGUES)} leagues"
    )
    return df


def _parse_standing_entry(
    entry: Dict,
    league_key: str,
    league_name: str,
    country: str,
    season: int,
) -> Dict:
    """
    Parse a single team's standing entry from the API response
    into a flat dict.

    API-Football standing entry structure:
    {
      "rank": 1,
      "team": {"id": 33, "name": "Manchester United"},
      "points": 86,
      "goalsDiff": 55,
      "all": {
        "played": 38, "win": 27, "draw": 5, "lose": 6,
        "goals": {"for": 83, "against": 28}
      },
      "home": { ... },
      "away": { ... }
    }

    Args:
        entry:       Raw team standing dict from API
        league_key:  Our short key, e.g. "EPL"
        league_name: Full name, e.g. "Premier League"
        country:     e.g. "England"
        season:      e.g. 2023

    Returns:
        Flat dict suitable for a DataFrame row
    """
    all_stats  = entry.get("all", {})
    goals      = all_stats.get("goals", {})
    home_stats = entry.get("home", {})
    away_stats = entry.get("away", {})

    games_played  = all_stats.get("played", 0)
    goals_against = goals.get("against", 0)
    goals_for     = goals.get("for", 0)

    return {
        # --- Identifiers ---
        "league_key":   league_key,
        "league_name":  league_name,
        "country":      country,
        "season":       season,
        "season_label": f"{season}/{str(season + 1)[-2:]}",

        # --- Team Info ---
        "team_id":   entry.get("team", {}).get("id"),
        "team_name": entry.get("team", {}).get("name"),

        # --- Final Standing ---
        "position":    entry.get("rank"),
        "points":      entry.get("points"),
        "is_champion": 1 if entry.get("rank") == 1 else 0,
        "is_top4":     1 if entry.get("rank", 99) <= 4 else 0,

        # --- Match Record ---
        "games_played": games_played,
        "wins":         all_stats.get("win", 0),
        "draws":        all_stats.get("draw", 0),
        "losses":       all_stats.get("lose", 0),

        # --- Attacking ---
        "goals_for":     goals_for,
        "goals_for_avg": round(
            goals_for / games_played, 3
        ) if games_played else None,

        # --- DEFENSIVE METRICS (core of our analysis) ---
        "goals_against":     goals_against,
        "goal_diff":         entry.get("goalsDiff", 0),
        "goals_against_avg": round(
            goals_against / games_played, 3
        ) if games_played else None,

        # Home vs Away defensive split
        "goals_against_home": home_stats.get("goals", {}).get("against", 0),
        "goals_against_away": away_stats.get("goals", {}).get("against", 0),
    }


# ============================================================
# TOP N TEAMS EXTRACTOR
# ============================================================
def extract_top4(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the full standings DataFrame to keep only the top N teams
    per league per season based on final position.

    Args:
        df: Full standings DataFrame from fetch_standings()

    Returns:
        Filtered DataFrame with only Top 4 teams per league-season
    """
    top4 = df[df["position"] <= TOP_N_TEAMS].copy()
    logger.info(
        f"Extracted top {TOP_N_TEAMS} teams: {len(top4)} rows "
        f"(from {len(df)} total)"
    )
    return top4.reset_index(drop=True)