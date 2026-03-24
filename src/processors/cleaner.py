# ============================================================
# src/processors/cleaner.py
# ============================================================
# PURPOSE:
#   Validates and cleans the raw standings DataFrame.
#   Handles: type enforcement, missing values, duplicate detection,
#   outlier flagging, and data quality reporting.
#
# ANALOGY:
#   Think of raw data as unprocessed ingredients.
#   This module is the "prep cook" — it checks everything is
#   fresh, removes bad pieces, and cuts it to a consistent size
#   before it goes to the main chef (feature engineer).
# ============================================================

import logging
from typing import Tuple

import numpy as np
import pandas as pd

from config import LOG_FORMAT, LOG_LEVEL, SEASONS

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


# ============================================================
# MAIN CLEANING PIPELINE
# ============================================================
def clean_standings(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Full cleaning pipeline for the standings DataFrame.

    Runs all cleaning steps in sequence and returns both the
    cleaned DataFrame and a quality report dict for logging.

    Args:
        df: Raw standings DataFrame from data_fetcher.py

    Returns:
        Tuple of:
        - cleaned DataFrame
        - quality_report dict (records dropped, issues found, etc.)
    """
    quality_report = {
        "initial_rows": len(df),
        "issues": [],
    }

    logger.info(f"🧹 Starting cleaning pipeline on {len(df)} rows")

    # --- Step 1: Enforce correct data types ---
    df = _enforce_types(df)
    logger.info("  ✅ Types enforced")

    # --- Step 2: Check for duplicates ---
    df, dupe_count = _remove_duplicates(df)
    if dupe_count > 0:
        quality_report["issues"].append(
            f"Removed {dupe_count} duplicate rows"
        )
        logger.warning(f"  ⚠️  Removed {dupe_count} duplicate rows")
    else:
        logger.info("  ✅ No duplicates found")

    # --- Step 3: Handle missing values ---
    df, missing_report = _handle_missing_values(df)
    quality_report["missing_values"] = missing_report
    logger.info(f"  ✅ Missing values handled: {missing_report}")

    # --- Step 4: Validate business logic ---
    issues = _validate_business_rules(df)
    quality_report["validation_issues"] = issues
    if issues:
        logger.warning(f"  ⚠️  Business rule violations: {issues}")
    else:
        logger.info("  ✅ Business rule validation passed")

    # --- Step 5: Flag statistical outliers ---
    # We flag but do NOT remove — extreme values are real signals
    df = _flag_outliers(df, column="goals_against", threshold=3.0)
    logger.info("  ✅ Outliers flagged")

    # --- Step 6: Add data quality score per row ---
    df = _add_completeness_score(df)

    quality_report["final_rows"]   = len(df)
    quality_report["rows_dropped"] = (
        quality_report["initial_rows"] - len(df)
    )

    logger.info(
        f"✅ Cleaning complete: {quality_report['final_rows']} rows "
        f"({quality_report['rows_dropped']} dropped)"
    )

    return df, quality_report


# ============================================================
# INDIVIDUAL CLEANING STEPS
# ============================================================

def _enforce_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce correct data types for every column.

    Without this, pandas might store 'position' as float64 due
    to NaNs, causing bugs in comparisons like df['position'] == 1.
    We use Int64 (nullable integer) to safely handle NaN values.
    """
    df = df.copy()

    int_cols = [
        "position", "points", "games_played",
        "wins", "draws", "losses",
        "goals_for", "goals_against",
        "goals_against_home", "goals_against_away",
        "goal_diff", "is_champion", "is_top4",
        "season", "team_id",
    ]
    for col in int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            ).astype("Int64")

    float_cols = ["goals_against_avg", "goals_for_avg"]
    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    str_cols = [
        "team_name", "league_key", "league_name",
        "country", "season_label"
    ]
    for col in str_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


def _remove_duplicates(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, int]:
    """
    Remove duplicate team-season-league records.

    Natural key: (league_key, season, team_id)
    A duplicate means the same team appeared twice in the same
    league standings for the same season.
    """
    natural_key = ["league_key", "season", "team_id"]

    if all(col in df.columns for col in natural_key):
        before = len(df)
        df = df.drop_duplicates(subset=natural_key, keep="first")
        return df, before - len(df)

    return df, 0


def _handle_missing_values(
    df: pd.DataFrame
) -> Tuple[pd.DataFrame, dict]:
    """
    Audit and handle missing values.

    Strategy:
    - Critical identifiers: drop the row
    - Derived averages: recompute from raw counts if possible
    """
    df     = df.copy()
    report = {}

    # --- Critical columns: drop rows with missing values ---
    critical_cols = [
        "team_name", "position", "goals_against", "games_played"
    ]
    for col in critical_cols:
        if col in df.columns:
            n_missing = df[col].isna().sum()
            if n_missing > 0:
                report[f"{col}_dropped"] = int(n_missing)
                df = df.dropna(subset=[col])

    # --- Averages: recompute from raw counts if missing ---
    mask = (
        df["goals_against_avg"].isna()
        & df["games_played"].notna()
        & (df["games_played"] > 0)
    )
    if mask.any():
        df.loc[mask, "goals_against_avg"] = (
            df.loc[mask, "goals_against"]
            / df.loc[mask, "games_played"]
        ).round(3)
        report["goals_against_avg_recomputed"] = int(mask.sum())

    return df, report


def _validate_business_rules(df: pd.DataFrame) -> list:
    """
    Check domain-specific logic to catch data quality issues.

    Rules that must always be true in football:
    - Position must be >= 1
    - Goals against must be >= 0
    - games_played must be > 0
    - Season should be in our expected list
    """
    issues = []

    bad_positions = df[(df["position"] < 1) | (df["position"] > 30)]
    if len(bad_positions) > 0:
        issues.append(
            f"{len(bad_positions)} rows with invalid position"
        )

    negative_ga = df[df["goals_against"] < 0]
    if len(negative_ga) > 0:
        issues.append(
            f"{len(negative_ga)} rows with negative goals_against"
        )

    zero_games = df[df["games_played"] <= 0]
    if len(zero_games) > 0:
        issues.append(
            f"{len(zero_games)} rows with games_played <= 0"
        )

    unexpected_seasons = df[~df["season"].isin(SEASONS)]
    if len(unexpected_seasons) > 0:
        issues.append(
            f"{len(unexpected_seasons)} rows with unexpected season"
        )

    return issues


def _flag_outliers(
    df: pd.DataFrame,
    column: str,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """
    Flag statistical outliers using Z-score within
    league-season groups.

    We do NOT remove outliers — a team that conceded 80 goals
    is genuinely terrible, not a data error. We flag them so
    we can investigate and note them in the report.

    Args:
        df:        Input DataFrame
        column:    Column to check for outliers
        threshold: Z-score threshold (standard: 3.0)

    Returns:
        DataFrame with added boolean column: {column}_is_outlier
    """
    df = df.copy()
    df[f"{column}_zscore"] = df.groupby(
        ["league_key", "season"]
    )[column].transform(
        lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
    )
    df[f"{column}_is_outlier"] = (
        df[f"{column}_zscore"].abs() > threshold
    )

    n_outliers = df[f"{column}_is_outlier"].sum()
    if n_outliers > 0:
        logger.info(
            f"  🔍 Flagged {n_outliers} outliers in "
            f"'{column}' (Z > {threshold})"
        )

    return df


def _add_completeness_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a row-level data completeness score (0.0 to 1.0).

    A score of 1.0 means all expected columns are populated.
    Useful for weighting or filtering in the analysis phase.
    """
    df       = df.copy()
    key_cols = [
        "position", "points", "games_played",
        "goals_for", "goals_against", "goals_against_avg",
    ]
    existing = [c for c in key_cols if c in df.columns]
    df["completeness_score"] = (
        df[existing].notna().mean(axis=1).round(2)
    )
    return df