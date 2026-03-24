# ============================================================
# tests/test_cleaner.py
# ============================================================
# PURPOSE:
#   Unit tests for the data cleaning pipeline.
#   Uses synthetic DataFrames — no API access needed.
#   Each test validates one specific cleaning behaviour.
# ============================================================

import pytest
import pandas as pd
import numpy as np

from src.processors.cleaner import (
    clean_standings,
    _enforce_types,
    _remove_duplicates,
    _handle_missing_values,
    _validate_business_rules,
    _flag_outliers,
)


# ============================================================
# TEST DATA FACTORY
# ============================================================
def _make_sample_df(n=20) -> pd.DataFrame:
    """
    Create a minimal valid standings DataFrame for testing.
    All values are valid by default — individual tests
    then corrupt specific fields to test cleaning logic.
    """
    return pd.DataFrame({
        "league_key":         ["EPL"] * n,
        "league_name":        ["Premier League"] * n,
        "country":            ["England"] * n,
        "season":             [2023] * n,
        "season_label":       ["2023/24"] * n,
        "team_id":            list(range(1, n + 1)),
        "team_name":          [f"Team {i}" for i in range(1, n + 1)],
        "position":           list(range(1, n + 1)),
        "points":             list(range(n * 2, n, -2)),
        "games_played":       [38] * n,
        "wins":               list(range(n, 0, -1)),
        "draws":              [5] * n,
        "losses":             list(range(0, n)),
        "goals_for":          [60 - i * 2 for i in range(n)],
        "goals_against":      [20 + i * 2 for i in range(n)],
        "goals_against_avg":  [
            round((20 + i * 2) / 38, 3) for i in range(n)
        ],
        "goals_against_home": [10 + i for i in range(n)],
        "goals_against_away": [10 + i for i in range(n)],
        "goal_diff":          [40 - i * 4 for i in range(n)],
        "goals_for_avg":      [
            round((60 - i * 2) / 38, 3) for i in range(n)
        ],
        "is_champion":        [1] + [0] * (n - 1),
        "is_top4":            [1] * 4 + [0] * (n - 4),
    })


# ============================================================
# TYPE ENFORCEMENT TESTS
# ============================================================
class TestEnforceTypes:

    def test_position_float_becomes_int64(self):
        """
        position column stored as float (common with NaNs)
        should be converted to Int64.
        """
        df = _make_sample_df()
        df["position"] = df["position"].astype(float)
        result = _enforce_types(df)
        assert str(result["position"].dtype) == "Int64"

    def test_team_name_whitespace_stripped(self):
        """
        Team names with leading/trailing spaces should
        be stripped to avoid mismatches in groupby operations.
        """
        df = _make_sample_df()
        df.loc[0, "team_name"] = "  Manchester City  "
        result = _enforce_types(df)
        assert result.loc[0, "team_name"] == "Manchester City"

    def test_goals_against_avg_stays_float(self):
        """
        Float columns should remain float after type enforcement.
        """
        df     = _make_sample_df()
        result = _enforce_types(df)
        assert result["goals_against_avg"].dtype == float


# ============================================================
# DUPLICATE REMOVAL TESTS
# ============================================================
class TestRemoveDuplicates:

    def test_exact_duplicate_removed(self):
        """
        An exact duplicate row (same team, season, league)
        should be removed keeping only the first occurrence.
        """
        df = _make_sample_df(10)
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        assert len(df) == 11

        cleaned, count = _remove_duplicates(df)
        assert count == 1
        assert len(cleaned) == 10

    def test_no_duplicates_unchanged(self):
        """
        Clean data with no duplicates should pass through
        with zero rows removed.
        """
        df             = _make_sample_df(10)
        cleaned, count = _remove_duplicates(df)
        assert count == 0
        assert len(cleaned) == len(df)


# ============================================================
# MISSING VALUE TESTS
# ============================================================
class TestHandleMissingValues:

    def test_null_position_row_dropped(self):
        """
        Rows with null position are critical failures —
        we cannot rank a team with no position.
        These rows must be dropped entirely.
        """
        df          = _make_sample_df(10)
        df.loc[0, "position"] = None
        cleaned, report = _handle_missing_values(df)
        assert len(cleaned) == 9
        assert "position_dropped" in report

    def test_ga_avg_recomputed_when_null(self):
        """
        If goals_against_avg is null but goals_against and
        games_played are present, the avg should be recomputed
        rather than leaving a gap in the data.
        """
        df = _make_sample_df(5)
        df.loc[0, "goals_against_avg"] = None
        df.loc[0, "goals_against"]     = 30
        df.loc[0, "games_played"]      = 38
        cleaned, report = _handle_missing_values(df)

        expected = round(30 / 38, 3)
        assert abs(
            float(cleaned.loc[0, "goals_against_avg"]) - expected
        ) < 0.001

    def test_clean_data_unchanged(self):
        """
        Data with no missing values should pass through
        with all rows intact.
        """
        df             = _make_sample_df(10)
        cleaned, report = _handle_missing_values(df)
        assert len(cleaned) == 10


# ============================================================
# BUSINESS RULE VALIDATION TESTS
# ============================================================
class TestValidateBusinessRules:

    def test_negative_goals_flagged(self):
        """
        Negative goals against is physically impossible —
        should be caught as a data quality issue.
        """
        df = _make_sample_df(5)
        df.loc[0, "goals_against"] = -1
        issues = _validate_business_rules(df)
        assert any("negative" in i for i in issues)

    def test_zero_games_played_flagged(self):
        """
        Zero games played makes averages undefined —
        should be flagged as a validation issue.
        """
        df = _make_sample_df(5)
        df.loc[2, "games_played"] = 0
        issues = _validate_business_rules(df)
        assert any("games_played" in i for i in issues)

    def test_clean_data_passes_validation(self):
        """
        Perfectly valid data should produce zero issues.
        """
        df     = _make_sample_df(10)
        issues = _validate_business_rules(df)
        assert len(issues) == 0


# ============================================================
# OUTLIER FLAGGING TESTS
# ============================================================
class TestFlagOutliers:

    def test_extreme_value_flagged(self):
        """
        A team with an absurdly high GA should be flagged
        as a statistical outlier (Z > 3.0).
        """
        df = _make_sample_df(18)
        df.loc[0, "goals_against"] = 999
        result = _flag_outliers(
            df, column="goals_against", threshold=3.0
        )
        assert "goals_against_is_outlier" in result.columns
        assert result.loc[0, "goals_against_is_outlier"] == True

    def test_normal_data_has_no_outliers(self):
        """
        Normally distributed data should produce
        zero outlier flags.
        """
        df     = _make_sample_df(18)
        result = _flag_outliers(
            df, column="goals_against", threshold=3.0
        )
        assert result["goals_against_is_outlier"].sum() == 0


# ============================================================
# FULL PIPELINE TESTS
# ============================================================
class TestFullPipeline:

    def test_returns_dataframe_and_report(self):
        """
        clean_standings should always return a tuple of
        (DataFrame, dict) regardless of input quality.
        """
        df             = _make_sample_df(20)
        result, report = clean_standings(df)
        assert isinstance(result, pd.DataFrame)
        assert isinstance(report, dict)

    def test_report_has_required_keys(self):
        """
        Quality report must always contain initial_rows
        and final_rows so we can audit what was changed.
        """
        df             = _make_sample_df(10)
        result, report = clean_standings(df)
        assert "initial_rows" in report
        assert "final_rows" in report

    def test_completeness_score_between_0_and_1(self):
        """
        Completeness score must be a valid proportion (0-1).
        Any value outside this range indicates a bug in
        the scoring logic.
        """
        df             = _make_sample_df(10)
        result, _      = clean_standings(df)
        assert "completeness_score" in result.columns
        assert result["completeness_score"].between(0, 1).all()