# ============================================================
# src/visualizers/eda_plots.py
# ============================================================
# PURPOSE:
#   Exploratory Data Analysis visualisations.
#   These are the "listening to the data" charts — distributions,
#   correlations, and overview summaries that reveal patterns
#   BEFORE we do formal statistical testing.
#
# DESIGN PRINCIPLES:
#   - Every chart has a clear title, axis labels, and units
#   - Colour encodes league identity (consistent LEAGUE_COLORS)
#   - Each figure is saved to outputs/figures/ at high DPI
#   - Functions return the figure object for notebook use too
# ============================================================

import logging
import matplotlib
matplotlib.use("Agg")          # Non-interactive backend for script runs

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats

from config import (
    LEAGUE_COLORS, FIGURES_DIR,
    FIG_SIZE_STANDARD, FIG_SIZE_WIDE,
    FIG_SIZE_SQUARE, PLOT_DPI, PLOT_STYLE,
    LOG_FORMAT, LOG_LEVEL
)

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

plt.style.use(PLOT_STYLE)


# ============================================================
# HELPER: Save figure
# ============================================================
def _save(fig: plt.Figure, filename: str) -> None:
    """Save figure to the outputs/figures directory."""
    path = FIGURES_DIR / filename
    fig.savefig(path, dpi=PLOT_DPI, bbox_inches="tight")
    logger.info(f"💾 Saved: {path}")


# ============================================================
# CHART 1: Goals Conceded Distribution per League
# ============================================================
def plot_ga_distribution(df: pd.DataFrame) -> plt.Figure:
    """
    Box plots showing distribution of goals conceded across all
    teams in each league across all 5 seasons combined.

    WHY THIS CHART:
    Before testing if top teams defend better, we need to understand
    the landscape — how spread out are GA values? Are some leagues
    generally more defensive than others?

    Chart type: Box + jittered swarm overlay
    """
    fig, axes = plt.subplots(1, 5, figsize=FIG_SIZE_WIDE, sharey=True)
    fig.suptitle(
        "Goals Conceded Distribution by League (All Teams, 5 Seasons)",
        fontsize=14, fontweight="bold", y=1.02
    )

    league_order = list(LEAGUE_COLORS.keys())

    for ax, league_key in zip(axes, league_order):
        subset = df[df["league_key"] == league_key]
        color  = LEAGUE_COLORS[league_key]

        # Box plot: shows median, IQR, whiskers
        ax.boxplot(
            subset["goals_against"].dropna(),
            patch_artist=True,
            medianprops={"color": "white", "linewidth": 2},
            boxprops={"facecolor": color, "alpha": 0.7},
            whiskerprops={"color": color},
            capprops={"color": color},
            flierprops={
                "marker": "o",
                "markerfacecolor": color,
                "markersize": 4,
                "alpha": 0.5
            },
        )

        # Overlay: individual jittered data points
        x_jitter = np.random.normal(1, 0.04, size=len(subset))
        ax.scatter(
            x_jitter,
            subset["goals_against"].values,
            alpha=0.35, color=color, s=15, zorder=3,
        )

        # League name labels
        league_info = {
            "EPL":        "Premier\nLeague",
            "LALIGA":     "La Liga",
            "BUNDESLIGA": "Bundesliga",
            "SERIE_A":    "Serie A",
            "LIGUE_1":    "Ligue 1"
        }
        ax.set_title(
            league_info.get(league_key, league_key),
            fontsize=11, color=color, fontweight="bold"
        )
        ax.set_xticks([])

        # Median label
        median_val = subset["goals_against"].median()
        ax.text(
            1.25, median_val,
            f"Md: {median_val:.0f}",
            va="center", fontsize=8, color="grey"
        )

    axes[0].set_ylabel("Goals Conceded (Season Total)", fontsize=11)
    fig.text(
        0.5, -0.02,
        "Each dot = one team-season | Box = IQR | Line = median",
        ha="center", fontsize=9, color="grey", style="italic"
    )

    plt.tight_layout()
    _save(fig, "01_ga_distribution_by_league.png")
    return fig


# ============================================================
# CHART 2: Correlation Heatmap
# ============================================================
def plot_correlation_heatmap(df: pd.DataFrame) -> plt.Figure:
    """
    Pearson correlation heatmap between all key metrics.

    Key correlations to look for:
    - goals_against vs position (positive: more GA = worse position)
    - points vs goals_against (negative: more GA = fewer points)
    - defensive_rank vs position (positive)

    WHY THIS CHART:
    The heatmap is the big picture overview — it tells us at a
    glance which variables move together. It is the X-ray
    before the surgery.
    """
    cols = [
        "position", "points", "goals_against", "goals_for",
        "goals_against_avg", "goal_diff", "wins",
        "defensive_rank", "ga_vs_median", "win_rate",
    ]
    existing_cols = [c for c in cols if c in df.columns]
    corr_df = df[existing_cols].dropna().astype(float)

    rename_map = {
        "position":        "Final Position",
        "points":          "Points",
        "goals_against":   "Goals Conceded",
        "goals_for":       "Goals Scored",
        "goals_against_avg": "GA per Game",
        "goal_diff":       "Goal Difference",
        "wins":            "Wins",
        "defensive_rank":  "Defensive Rank",
        "ga_vs_median":    "GA vs Median",
        "win_rate":        "Win Rate",
    }
    corr_df       = corr_df.rename(columns=rename_map)
    corr_matrix   = corr_df.corr(method="pearson")

    fig, ax = plt.subplots(figsize=FIG_SIZE_SQUARE)

    # Hide upper triangle (redundant mirror of lower)
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

    sns.heatmap(
        corr_matrix,
        mask=mask,
        cmap="RdBu_r",
        center=0,
        vmin=-1, vmax=1,
        annot=True,
        fmt=".2f",
        annot_kws={"size": 9},
        linewidths=0.5,
        linecolor="white",
        ax=ax,
        cbar_kws={
            "label": "Pearson Correlation Coefficient",
            "shrink": 0.8
        },
    )

    ax.set_title(
        "Correlation Matrix: Defensive & Performance Metrics\n"
        "(All Leagues, 5 Seasons | Lower triangle shown)",
        fontsize=13, fontweight="bold", pad=15
    )
    ax.set_xticklabels(
        ax.get_xticklabels(), rotation=45, ha="right", fontsize=9
    )
    ax.set_yticklabels(
        ax.get_yticklabels(), rotation=0, fontsize=9
    )

    fig.text(
        0.5, -0.03,
        "Key: Look for 'Goals Conceded' row — "
        "strong correlations with Position and Points "
        "confirm the defensive hypothesis.",
        ha="center", fontsize=9, style="italic", color="grey"
    )

    plt.tight_layout()
    _save(fig, "02_correlation_heatmap.png")
    return fig


# ============================================================
# CHART 3: Scatter — Goals Conceded vs Points
# ============================================================
def plot_ga_vs_points_scatter(df: pd.DataFrame) -> plt.Figure:
    """
    Scatter plot: Goals Conceded (x) vs Points (y).
    Coloured by league with OLS regression line per league.

    WHY THIS CHART:
    If the hypothesis is true we should see a clear downward
    slope — teams that concede more goals earn fewer points.
    Outliers reveal teams that won titles despite leaky defence,
    or had great defence but still finished mid-table.
    """
    fig, ax = plt.subplots(figsize=FIG_SIZE_STANDARD)

    for league_key, color in LEAGUE_COLORS.items():
        subset = df[df["league_key"] == league_key].dropna(
            subset=["goals_against", "points"]
        )

        if len(subset) < 5:
            continue

        # Scatter points
        ax.scatter(
            subset["goals_against"],
            subset["points"],
            color=color, alpha=0.55, s=45,
            label=f"{league_key}", zorder=3,
        )

        # OLS regression line
        m, b, r_val, p_val, _ = stats.linregress(
            subset["goals_against"].astype(float),
            subset["points"].astype(float)
        )
        x_line = np.linspace(
            subset["goals_against"].min(),
            subset["goals_against"].max(),
            100
        )
        ax.plot(
            x_line, m * x_line + b,
            color=color, linewidth=2,
            alpha=0.9, linestyle="--",
        )

        # Annotate r² value
        mid_x = subset["goals_against"].median()
        ax.text(
            mid_x, m * mid_x + b + 1.5,
            f"r²={r_val**2:.2f}",
            color=color, fontsize=8, ha="center"
        )

    ax.set_xlabel("Goals Conceded (Season Total)", fontsize=12)
    ax.set_ylabel("Points (Season Total)", fontsize=12)
    ax.set_title(
        "Goals Conceded vs Points — Top 5 European Leagues (5 Seasons)\n"
        "Dashed lines = OLS regression per league | "
        "r² = variance explained",
        fontsize=13, fontweight="bold"
    )
    ax.legend(title="League", fontsize=10, title_fontsize=10)
    ax.grid(True, alpha=0.4)

    ax.text(
        0.98, 0.98,
        "← Better defence = fewer goals conceded\n"
        "↑ More points = higher final position",
        transform=ax.transAxes, ha="right", va="top",
        fontsize=9, color="grey", style="italic",
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor="lightyellow",
            alpha=0.6
        )
    )

    plt.tight_layout()
    _save(fig, "03_ga_vs_points_scatter.png")
    return fig


# ============================================================
# CHART 4: Champion Defensive Rank Heatmap
# ============================================================
def plot_champion_def_rank_heatmap(
    summary_df: pd.DataFrame
) -> plt.Figure:
    """
    Heatmap where rows = leagues, columns = seasons.
    Cell value = the champion's defensive rank that season.
    Dark green = rank 1 (best defence). Light = lower rank.

    WHY THIS CHART:
    This is the most direct test of our hypothesis.
    If every cell is dark green (rank 1 or 2), the hypothesis
    is strongly supported. Light cells reveal which leagues
    produce attacking champions.
    """
    pivot = summary_df.pivot(
        index="league_key",
        columns="season_label",
        values="champion_def_rank",
    )

    league_order = [k for k in LEAGUE_COLORS.keys() if k in pivot.index]
    pivot = pivot.loc[league_order]

    name_map = {
        "EPL":        "Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "LALIGA":     "La Liga 🇪🇸",
        "BUNDESLIGA": "Bundesliga 🇩🇪",
        "SERIE_A":    "Serie A 🇮🇹",
        "LIGUE_1":    "Ligue 1 🇫🇷",
    }
    pivot.index = [name_map.get(k, k) for k in pivot.index]

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.heatmap(
        pivot.astype(float),
        cmap=sns.color_palette("YlGn_r", as_cmap=True),
        annot=True,
        fmt=".0f",
        annot_kws={"size": 14, "weight": "bold"},
        linewidths=2,
        linecolor="white",
        vmin=1, vmax=8,
        cbar_kws={
            "label": "Champion's Defensive Rank "
                     "(1 = fewest goals conceded)",
            "shrink": 0.9
        },
        ax=ax,
    )

    ax.set_title(
        "Where Did the Title Winner Rank Defensively?\n"
        "Cell = Champion's defensive rank that season "
        "(1 = best defence in league)",
        fontsize=13, fontweight="bold", pad=15
    )
    ax.set_xlabel("Season", fontsize=11)
    ax.set_ylabel("")
    ax.set_yticklabels(
        ax.get_yticklabels(), rotation=0, fontsize=11
    )

    fig.text(
        0.5, -0.04,
        "Dark green (rank 1 or 2) supports the hypothesis. "
        "Light cells = champion won with a mid-table defence.",
        ha="center", fontsize=9, style="italic", color="grey"
    )

    plt.tight_layout()
    _save(fig, "04_champion_def_rank_heatmap.png")
    return fig