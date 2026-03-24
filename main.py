#!/usr/bin/env python3
# ============================================================
# main.py — Entry point for the full analysis pipeline
# ============================================================
# PURPOSE:
#   Orchestrates all stages of the analysis in sequence:
#   Fetch → Clean → Engineer → Analyse → Visualise → Report
#
#   Each stage saves its output so the pipeline can be
#   resumed from any point without re-fetching from the API.
#
# USAGE:
#   python main.py --step all         # Run full pipeline
#   python main.py --step fetch       # Only fetch from API
#   python main.py --step process     # Clean + engineer
#   python main.py --step visualise   # All charts
#   python main.py --step report      # Statistical report
# ============================================================

import argparse
import logging
import sys

import pandas as pd

from config import DATA_PROC_DIR, LOG_FORMAT, LOG_LEVEL
from src.collectors.api_client import APIFootballClient
from src.collectors.data_fetcher import fetch_standings, extract_top4
from src.processors.cleaner import clean_standings
from src.processors.feature_engineer import (
    engineer_features,
    build_hypothesis_summary
)
from src.visualizers.eda_plots import (
    plot_ga_distribution,
    plot_correlation_heatmap,
    plot_ga_vs_points_scatter,
    plot_champion_def_rank_heatmap,
)
from src.visualizers.league_plots import (
    plot_top4_defensive_bars,
    plot_champion_ga_trend,
    plot_defensive_radar,
)
from src.visualizers.summary_plots import (
    plot_hypothesis_summary_bar,
    plot_spearman_results,
    plot_final_summary_dashboard,
)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# ============================================================
# FILE PATHS — where each stage saves its output
# ============================================================
RAW_STANDINGS_PATH   = DATA_PROC_DIR / "standings_raw.csv"
CLEAN_STANDINGS_PATH = DATA_PROC_DIR / "standings_clean.csv"
FEATURES_PATH        = DATA_PROC_DIR / "standings_features.csv"
SUMMARY_PATH         = DATA_PROC_DIR / "hypothesis_summary.csv"


# ============================================================
# PIPELINE STAGES
# ============================================================

def stage_fetch() -> pd.DataFrame:
    """
    Stage 1 — FETCH
    Pull standings data for all 5 leagues x 5 seasons.
    Saves raw CSV to data/processed/standings_raw.csv.
    Cached responses cost 0 API requests on reruns.
    """
    logger.info("=" * 60)
    logger.info("STAGE 1: Data Fetching")
    logger.info("=" * 60)

    client = APIFootballClient()
    df_raw = fetch_standings(client)

    df_raw.to_csv(RAW_STANDINGS_PATH, index=False)
    logger.info(f"✅ Raw standings saved → {RAW_STANDINGS_PATH}")
    logger.info(
        f"   Live API requests this session: "
        f"{client.live_request_count}"
    )

    return df_raw


def stage_process(df_raw: pd.DataFrame = None) -> tuple:
    """
    Stage 2 — CLEAN + FEATURE ENGINEER
    Cleans the raw data and derives analysis-ready features.
    Saves to standings_clean.csv and standings_features.csv.
    Can be run independently if raw CSV already exists.
    """
    logger.info("=" * 60)
    logger.info("STAGE 2: Cleaning & Feature Engineering")
    logger.info("=" * 60)

    # Load from disk if not passed in — allows resume
    if df_raw is None:
        if not RAW_STANDINGS_PATH.exists():
            raise FileNotFoundError(
                f"Raw data not found at {RAW_STANDINGS_PATH}. "
                "Run with --step fetch first."
            )
        df_raw = pd.read_csv(RAW_STANDINGS_PATH)
        logger.info(f"Loaded raw data from {RAW_STANDINGS_PATH}")

    # --- Cleaning ---
    df_clean, quality_report = clean_standings(df_raw)
    df_clean.to_csv(CLEAN_STANDINGS_PATH, index=False)
    logger.info(f"Quality report: {quality_report}")
    logger.info(f"✅ Clean standings saved → {CLEAN_STANDINGS_PATH}")

    # --- Feature Engineering ---
    df_features = engineer_features(df_clean)
    df_features.to_csv(FEATURES_PATH, index=False)
    logger.info(f"✅ Feature data saved → {FEATURES_PATH}")

    # --- Hypothesis Summary ---
    summary_df = build_hypothesis_summary(df_features)
    summary_df.to_csv(SUMMARY_PATH, index=False)
    logger.info(f"✅ Hypothesis summary saved → {SUMMARY_PATH}")

    return df_features, summary_df


def stage_visualise(
    df: pd.DataFrame = None,
    summary_df: pd.DataFrame = None
) -> None:
    """
    Stage 3 — VISUALISE
    Generates all 10 charts and saves to outputs/figures/.
    Can be run independently if feature CSV already exists.
    """
    logger.info("=" * 60)
    logger.info("STAGE 3: Visualisation")
    logger.info("=" * 60)

    if df is None:
        if not FEATURES_PATH.exists():
            raise FileNotFoundError(
                "Feature data not found. "
                "Run --step process first."
            )
        df = pd.read_csv(FEATURES_PATH)

    if summary_df is None:
        summary_df = pd.read_csv(SUMMARY_PATH)

    top4 = extract_top4(df)

    # ---- EDA Plots ----
    logger.info("  Generating EDA plots...")
    plot_ga_distribution(df)
    plot_correlation_heatmap(df)
    plot_ga_vs_points_scatter(df)
    plot_champion_def_rank_heatmap(summary_df)

    # ---- League Plots ----
    logger.info("  Generating league-level plots...")
    plot_top4_defensive_bars(df)
    plot_champion_ga_trend(df)
    plot_defensive_radar(top4)

    # ---- Summary / Hypothesis Plots ----
    logger.info("  Generating summary plots...")
    plot_hypothesis_summary_bar(summary_df)
    plot_spearman_results(df)
    plot_final_summary_dashboard(df, summary_df)

    logger.info("✅ All 10 figures saved to outputs/figures/")


def stage_report(
    df: pd.DataFrame = None,
    summary_df: pd.DataFrame = None
) -> None:
    """
    Stage 4 — REPORT
    Prints key statistical findings to console.
    See docs/PROJECT_DETAIL.md for full narrative report.
    """
    logger.info("=" * 60)
    logger.info("STAGE 4: Statistical Report")
    logger.info("=" * 60)

    if df is None:
        df = pd.read_csv(FEATURES_PATH)
    if summary_df is None:
        summary_df = pd.read_csv(SUMMARY_PATH)

    from scipy import stats

    print("\n" + "=" * 70)
    print("ANALYSIS REPORT: Does Best Defence Win the Title?")
    print("Top 5 European Leagues | 5 Seasons (2019/20 - 2023/24)")
    print("=" * 70)

    # --- Finding 1: Champion defensive rank ---
    pct_rank1 = (
        summary_df["champion_def_rank"] == 1
    ).mean() * 100
    pct_top3 = (
        summary_df["champion_def_rank"] <= 3
    ).mean() * 100

    print(
        f"\n📊 FINDING 1: Champion had rank-1 defence in "
        f"{pct_rank1:.1f}% of seasons"
    )
    print(
        f"   Champion had top-3 defence in "
        f"{pct_top3:.1f}% of seasons"
    )

    print("\n   Per-league breakdown:")
    per_league = summary_df.groupby("league_key").agg(
        rank1_pct=(
            "champion_def_rank", lambda x: (x == 1).mean() * 100
        ),
        avg_def_rank=("champion_def_rank", "mean"),
        avg_ga=("champion_ga", "mean"),
    ).round(2)
    print(per_league.to_string())

    # --- Finding 2: Spearman correlation ---
    print(
        f"\n📊 FINDING 2: Spearman Correlation "
        f"(Defensive Rank vs Final Position)"
    )
    for league_key in df["league_key"].unique():
        subset = df[
            df["league_key"] == league_key
        ].dropna(subset=["defensive_rank", "position"])
        if len(subset) < 10:
            continue
        rho, p_val = stats.spearmanr(
            subset["defensive_rank"].astype(float),
            subset["position"].astype(float)
        )
        sig = (
            "✅ significant" if p_val < 0.05
            else "❌ not significant"
        )
        print(
            f"   {league_key:12s}: ρ={rho:.3f}, "
            f"p={p_val:.4f} → {sig}"
        )

    # --- Finding 3: Overall GA vs Points ---
    clean = df.dropna(subset=["goals_against", "points"])
    r, p  = stats.pearsonr(
        clean["goals_against"].astype(float),
        clean["points"].astype(float)
    )
    print(
        f"\n📊 FINDING 3: Pearson r "
        f"(Goals Against vs Points, all leagues): "
        f"r={r:.3f}, p={p:.4e}"
    )

    print("\n" + "=" * 70)
    print("See outputs/figures/ for all 10 visualisations")
    print("See docs/PROJECT_DETAIL.md for full narrative")
    print("=" * 70 + "\n")


# ============================================================
# CLI ARGUMENT PARSING
# ============================================================
def parse_args():
    parser = argparse.ArgumentParser(
        description="Football Defence Analysis Pipeline",
    )
    parser.add_argument(
        "--step",
        choices=["all", "fetch", "process", "visualise", "report"],
        default="all",
        help="Which pipeline stage to run (default: all)"
    )
    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    args = parse_args()
    logger.info(f"🚀 Starting pipeline — step: {args.step}")

    df         = None
    summary_df = None

    try:
        if args.step in ("all", "fetch"):
            df_raw = stage_fetch()
        else:
            df_raw = None

        if args.step in ("all", "process"):
            df, summary_df = stage_process(df_raw)

        if args.step in ("all", "visualise"):
            stage_visualise(df, summary_df)

        if args.step in ("all", "report"):
            stage_report(df, summary_df)

        logger.info("🏁 Pipeline complete.")

    except EnvironmentError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\n❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.exception(f"💥 Unexpected error: {e}")
        sys.exit(1)