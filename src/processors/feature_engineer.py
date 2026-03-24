# ============================================================
# src/processors/feature_engineer.py
# ============================================================
# PURPOSE:
#   Derives new analytical metrics from the cleaned standings data.
#   Raw data tells us "City conceded 32 goals."
#   This module tells us "City had the best defence in the league
#   (rank #1), a clean sheet rate of 57%, and was 18 goals better
#   than the league median."
#
# ANALOGY:
#   The cleaner gave us clean, raw timber.
#   This module is the carpenter — shaping it into the actual
#   structural components (features) that will hold up our analysis.
# ============================================================

import logging
import numpy as np
import pandas as pd

from config import LOG_FORMAT, LOG_LEVEL, TOP4_POSITIONS

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main feature engineering pipeline.

    Adds the following derived columns:
    1. defensive_rank       — Rank within league-season (1 = fewest GA)
    2. is_best_defence      — Boolean: did this team have rank #1 defence?
    3. ga_vs_median         — How much better/worse than league-season median
    4. ga_pct_rank          — Percentile rank (0-1) within league-season
    5. champion_def_rank    — What defensive rank the title winner had
    6. champion_had_best_def— Boolean: did champion have best defence?
    7. points_per_game      — Normalises across different season lengths
    8. win_rate             — Wins divided by games played
    9. def_efficiency       — Composite defensive efficiency score
    10. ga_change_yoy       — Year-over-year change in goals conceded

    Args:
        df: Cleaned standings DataFrame

    Returns:
        DataFrame with new feature columns added
    """
    df = df.copy()

    # --- Feature 1: Defensive rank within each league-season ---
    # Rank 1 = fewest goals conceded (best defence)
    # method='min' means ties both get the lower rank
    df["defensive_rank"] = df.groupby(
        ["league_key", "season"]
    )["goals_against"].rank(
        method="min", ascending=True
    ).astype(int)

    logger.info("  ✅ Defensive rank computed")

    # --- Feature 2: Is this the best defensive unit in the league? ---
    df["is_best_defence"] = (
        df["defensive_rank"] == 1
    ).astype(int)

    # --- Feature 3: Goals against vs league-season median ---
    # Positive = conceded MORE than median (worse defence)
    # Negative = conceded LESS than median (better defence)
    df["ga_vs_median"] = df.groupby(
        ["league_key", "season"]
    )["goals_against"].transform(
        lambda x: x - x.median()
    ).round(2)

    # --- Feature 4: Percentile rank (0.0 = best, 1.0 = worst) ---
    df["ga_pct_rank"] = df.groupby(
        ["league_key", "season"]
    )["goals_against"].rank(
        pct=True, ascending=True
    ).round(3)

    logger.info("  ✅ Relative defensive metrics computed")

    # --- Feature 5 & 6: Champion's defensive rank per league-season ---
    # First find the champion's defensive rank per league-season
    champion_def = (
        df[df["position"] == 1]
        .groupby(["league_key", "season"])["defensive_rank"]
        .first()
        .reset_index()
        .rename(columns={"defensive_rank": "champion_def_rank"})
    )

    df = df.merge(champion_def, on=["league_key", "season"], how="left")

    # Boolean: did the champion ALSO have the #1 defence?
    df["champion_had_best_def"] = (
        df["champion_def_rank"] == 1
    ).astype(int)

    logger.info("  ✅ Champion-defence relationship features computed")

    # --- Feature 7: Points per game ---
    # Normalises across leagues with different game counts
    df["points_per_game"] = (
        df["points"] / df["games_played"]
    ).round(3)

    # --- Feature 8: Win rate ---
    df["win_rate"] = (
        df["wins"] / df["games_played"]
    ).round(3)

    # --- Feature 9: Defensive efficiency score ---
    # Composite: 50% normalised GA + 50% win rate
    # Lower GA + Higher win rate = better defensive efficiency
    df["def_efficiency"] = (
        df.groupby(["league_key", "season"])
        .apply(_compute_defensive_efficiency)
        .reset_index(level=[0, 1], drop=True)
    )

    logger.info("  ✅ Defensive efficiency score computed")

    # --- Feature 10: Season-over-season GA change ---
    # Negative = improvement (fewer goals conceded vs last season)
    # Positive = regression (more goals conceded vs last season)
    df = df.sort_values(["league_key", "team_id", "season"])
    df["ga_change_yoy"] = df.groupby(
        ["league_key", "team_id"]
    )["goals_against"].diff()

    logger.info("  ✅ Year-over-year defensive change computed")

    total_new = [
        "defensive_rank", "is_best_defence", "ga_vs_median",
        "ga_pct_rank", "champion_def_rank", "champion_had_best_def",
        "points_per_game", "win_rate", "def_efficiency", "ga_change_yoy",
    ]
    logger.info(
        f"✅ Feature engineering complete. "
        f"Added {len(total_new)} features."
    )

    return df


def _compute_defensive_efficiency(
    group: pd.DataFrame
) -> pd.Series:
    """
    Compute a 0-1 normalised defensive efficiency score
    within a league-season group.

    Formula:
    - Normalise goals_against_avg to 0-1 then invert
      (lower GA = higher score)
    - Normalise win_rate to 0-1
    - Score = 0.5 * (1 - norm_GA) + 0.5 * norm_win_rate

    This gives equal weight to not conceding and winning.

    Args:
        group: Sub-DataFrame for one league-season

    Returns:
        Series of efficiency scores (same index as group)
    """
    ga = group["goals_against_avg"]
    wr = group["win_rate"]

    ga_range = ga.max() - ga.min()
    wr_range = wr.max() - wr.min()

    norm_ga = (
        (ga - ga.min()) / ga_range
        if ga_range > 0
        else pd.Series(0.5, index=ga.index)
    )
    norm_wr = (
        (wr - wr.min()) / wr_range
        if wr_range > 0
        else pd.Series(0.5, index=wr.index)
    )

    # Invert GA: lower GA should give higher score
    return (0.5 * (1 - norm_ga) + 0.5 * norm_wr).round(3)


def build_hypothesis_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a per-league-season summary table for hypothesis testing.

    Each row = one league-season with:
    - Champion name and points
    - Champion's goals against
    - Champion's defensive rank
    - Whether champion had the best defence
    - Average defensive rank of top 4 teams

    Args:
        df: Feature-engineered standings DataFrame

    Returns:
        Summary DataFrame (one row per league-season)
    """
    champions = df[df["position"] == 1].copy()

    summary = champions.groupby(
        ["league_key", "league_name", "season", "season_label"]
    ).agg(
        champion_name     = ("team_name",       "first"),
        champion_points   = ("points",          "first"),
        champion_ga       = ("goals_against",   "first"),
        champion_def_rank = ("defensive_rank",  "first"),
        had_best_defence  = ("is_best_defence", "first"),
    ).reset_index()

    # Add average defensive rank of top 4 per league-season
    top4_def = (
        df[df["position"] <= 4]
        .groupby(["league_key", "season"])["defensive_rank"]
        .mean()
        .reset_index()
        .rename(columns={"defensive_rank": "top4_avg_def_rank"})
    )

    summary = summary.merge(
        top4_def, on=["league_key", "season"], how="left"
    )
    summary["top4_avg_def_rank"] = (
        summary["top4_avg_def_rank"].round(2)
    )

    logger.info(
        f"✅ Hypothesis summary built: {len(summary)} league-season rows"
    )
    return summary