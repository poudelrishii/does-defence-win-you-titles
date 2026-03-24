# ============================================================
# src/visualizers/league_plots.py
# ============================================================
# PURPOSE:
#   Per-league visualisations showing defensive profiles of the
#   top 4 teams each season. These are the "deep dive" charts
#   that complement the cross-league overview in eda_plots.py
# ============================================================

import logging
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from config import (
    LEAGUE_COLORS, FIGURES_DIR, PLOT_DPI,
    PLOT_STYLE, LOG_FORMAT, LOG_LEVEL
)

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
plt.style.use(PLOT_STYLE)


def _save(fig, filename):
    path = FIGURES_DIR / filename
    fig.savefig(path, dpi=PLOT_DPI, bbox_inches="tight")
    logger.info(f"💾 Saved: {path}")


# ============================================================
# CHART 5: Top 4 Defensive Profile — Grouped Bar per League
# ============================================================
def plot_top4_defensive_bars(df: pd.DataFrame) -> plt.Figure:
    """
    For each of the 5 leagues: a grouped bar chart showing
    goals conceded by the top 4 teams across all 5 seasons.

    Bar colour intensity encodes finishing position:
    darker = higher finishing position.

    WHY THIS CHART:
    We want to see if within the top 4 there is a consistent
    ordering — does rank 1 almost always concede the fewest?
    If yes, defence within the top 4 is also discriminatory.
    """
    leagues = list(LEAGUE_COLORS.keys())
    fig, axes = plt.subplots(5, 1, figsize=(16, 22))
    fig.suptitle(
        "Goals Conceded by Top 4 Teams — Per League, Per Season\n"
        "Darker shade = better finishing position",
        fontsize=15, fontweight="bold", y=1.01
    )

    # Position shades: rank 1 = darkest, rank 4 = lightest
    position_alphas = {1: 1.0, 2: 0.75, 3: 0.55, 4: 0.38}
    position_labels = {
        1: "Champion",
        2: "2nd Place",
        3: "3rd Place",
        4: "4th Place"
    }

    for ax, league_key in zip(axes, leagues):
        color  = LEAGUE_COLORS[league_key]
        subset = df[
            (df["league_key"] == league_key) &
            (df["position"] <= 4)
        ].copy()

        if subset.empty:
            ax.set_visible(False)
            continue

        season_labels = sorted(subset["season_label"].unique())
        n_seasons     = len(season_labels)
        bar_width     = 0.18
        group_width   = 4 * bar_width + 0.1
        x_centers     = np.arange(n_seasons) * group_width

        for pos_idx, position in enumerate([1, 2, 3, 4]):
            pos_data    = subset[subset["position"] == position]
            x_offsets   = []
            bar_heights = []
            bar_labels  = []

            for s_idx, sl in enumerate(season_labels):
                season_row = pos_data[pos_data["season_label"] == sl]
                if season_row.empty:
                    bar_heights.append(0)
                    bar_labels.append("")
                else:
                    bar_heights.append(
                        float(season_row["goals_against"].values[0])
                    )
                    bar_labels.append(
                        season_row["team_name"].values[0]
                    )
                x_offsets.append(
                    x_centers[s_idx] + pos_idx * bar_width
                )

            bars = ax.bar(
                x_offsets,
                bar_heights,
                width=bar_width * 0.9,
                color=color,
                alpha=position_alphas[position],
                label=position_labels[position],
                zorder=3,
            )

            # Annotate bar with team name (rotated)
            for bar, label in zip(bars, bar_labels):
                if label and bar.get_height() > 0:
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.5,
                        label[:12],
                        ha="center", va="bottom",
                        fontsize=5.5, rotation=90,
                        color="black", alpha=0.8
                    )

        tick_positions = [
            x_centers[i] + (4 * bar_width) / 2
            for i in range(n_seasons)
        ]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(season_labels, fontsize=9)
        ax.set_ylabel("Goals Conceded", fontsize=9)
        ax.set_title(
            f"{league_key.replace('_', ' ')} — "
            f"Top 4 Defensive Comparison",
            fontsize=11, color=color, fontweight="bold"
        )
        ax.legend(fontsize=8, loc="upper right", ncol=4)
        ax.grid(axis="y", alpha=0.4, zorder=0)
        ax.set_xlim(-0.2, x_centers[-1] + group_width)

    plt.tight_layout()
    _save(fig, "05_top4_defensive_bars.png")
    return fig


# ============================================================
# CHART 6: Time Series — Title Winner GA Over 5 Seasons
# ============================================================
def plot_champion_ga_trend(df: pd.DataFrame) -> plt.Figure:
    """
    Line chart: For each league, show how many goals the title
    winner conceded each season from 2019/20 to 2023/24.

    WHY THIS CHART:
    Reveals trajectories — did leagues move towards more defensive
    champions over time? Did one league consistently crown
    defensive champions while another rewarded attacking play?
    """
    fig, ax = plt.subplots(figsize=(13, 7))
    champions = df[df["position"] == 1].copy()

    for league_key, color in LEAGUE_COLORS.items():
        subset = champions[
            champions["league_key"] == league_key
        ].sort_values("season")

        if len(subset) < 2:
            continue

        ax.plot(
            subset["season_label"],
            subset["goals_against"],
            marker="o", markersize=9,
            color=color, linewidth=2.5,
            label=league_key, zorder=4,
        )

        # Annotate each point with winning team name
        for _, row in subset.iterrows():
            ax.annotate(
                text=row["team_name"].split()[-1],
                xy=(row["season_label"], row["goals_against"]),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center", fontsize=7,
                color=color, alpha=0.85,
                fontweight="bold"
            )

    ax.set_xlabel("Season", fontsize=12)
    ax.set_ylabel(
        "Goals Conceded by League Winner", fontsize=12
    )
    ax.set_title(
        "Title Winner's Goals Conceded — "
        "5 Seasons Across Top 5 Leagues\n"
        "Label = winning team | "
        "Lower line = more defensive champion",
        fontsize=13, fontweight="bold"
    )
    ax.legend(title="League", fontsize=10, title_fontsize=10)
    ax.grid(True, alpha=0.4)

    # Reference band for elite defence zone
    ax.axhspan(0, 30, alpha=0.07, color="green")
    ax.text(
        0.01, 28,
        "Elite defence zone (<30 GA)",
        fontsize=8, color="green", alpha=0.8
    )

    plt.tight_layout()
    _save(fig, "06_champion_ga_trend.png")
    return fig


# ============================================================
# CHART 7: Radar — Average Top 4 Defensive Profile per League
# ============================================================
def plot_defensive_radar(df: pd.DataFrame) -> plt.Figure:
    """
    Radar (spider) chart comparing average defensive metrics
    across leagues for their respective top 4 teams.

    Metrics on radar axes:
    - Avg Goals Conceded (inverted: lower = better)
    - Avg GA per game (inverted)
    - Avg Win Rate
    - Avg Defensive Rank (inverted)
    - Avg Points per Game

    WHY THIS CHART:
    A radar chart excels at showing multi-dimensional profiles
    at a glance. It lets you see if one league's top 4 is
    uniformly better on all axes or trades defence for attack.
    """
    top4 = df[df["position"] <= 4].copy()

    metrics = {
        "Goals Conceded\n(season avg)": (
            "goals_against", "lower_is_better"
        ),
        "GA per Game": (
            "goals_against_avg", "lower_is_better"
        ),
        "Win Rate": (
            "win_rate", "higher_is_better"
        ),
        "Points per Game": (
            "points_per_game", "higher_is_better"
        ),
        "Def. Rank\n(inverted)": (
            "defensive_rank", "lower_is_better"
        ),
    }

    metric_labels = list(metrics.keys())
    metric_cols   = [v[0] for v in metrics.values()]
    metric_dirs   = [v[1] for v in metrics.values()]

    league_avgs = top4.groupby("league_key")[metric_cols].mean()

    # Normalise all metrics to 0-1
    normalised = league_avgs.copy()
    for col, direction in zip(metric_cols, metric_dirs):
        col_min   = league_avgs[col].min()
        col_max   = league_avgs[col].max()
        col_range = col_max - col_min
        if col_range == 0:
            normalised[col] = 0.5
        else:
            normalised[col] = (
                (league_avgs[col] - col_min) / col_range
            )
            if direction == "lower_is_better":
                normalised[col] = 1 - normalised[col]

    # Radar geometry
    n_metrics = len(metric_labels)
    angles    = np.linspace(
        0, 2 * np.pi, n_metrics, endpoint=False
    ).tolist()
    angles   += angles[:1]  # Close the polygon

    fig, ax = plt.subplots(
        figsize=(9, 9), subplot_kw={"polar": True}
    )
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    for league_key in [
        k for k in LEAGUE_COLORS if k in normalised.index
    ]:
        color  = LEAGUE_COLORS[league_key]
        values = normalised.loc[league_key, metric_cols].tolist()
        values += values[:1]  # Close polygon

        ax.plot(
            angles, values,
            color=color, linewidth=2,
            label=league_key, zorder=3
        )
        ax.fill(angles, values, color=color, alpha=0.12)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_labels, fontsize=10)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(
        ["25%", "50%", "75%", "100%"],
        fontsize=8, color="grey"
    )
    ax.set_ylim(0, 1)
    ax.set_title(
        "Average Defensive Profile: Top 4 Teams per League\n"
        "(Normalised 0-1 | All metrics: outer = better)",
        fontsize=13, fontweight="bold", pad=20
    )
    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.3, 1.1),
        fontsize=10,
        title="League",
        title_fontsize=10
    )

    plt.tight_layout()
    _save(fig, "07_defensive_radar.png")
    return fig