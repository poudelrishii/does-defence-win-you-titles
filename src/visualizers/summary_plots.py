# ============================================================
# src/visualizers/summary_plots.py
# ============================================================
# PURPOSE:
#   Final hypothesis-validation and summary visualisations.
#   These charts tell the "answer" story — the ones that go
#   into the final report and presentation.
# ============================================================

import logging
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
import pandas as pd
from scipy import stats

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
# CHART 8: Did Best Defence Win the Title? — Summary Bar
# ============================================================
def plot_hypothesis_summary_bar(
    summary_df: pd.DataFrame
) -> plt.Figure:
    """
    Stacked bar chart showing per league how many out of 5
    seasons the title was won by:
      - Rank 1 defence (best in league)
      - Rank 2-3 defence
      - Rank 4+ defence (won with non-elite defence)

    WHY THIS CHART:
    This is the direct answer to our core question.
    It translates the statistical analysis into a clear
    boardroom-ready visual.
    """
    summary_df = summary_df.copy()

    # Classify each championship into a defensive tier
    summary_df["defence_tier"] = pd.cut(
        summary_df["champion_def_rank"],
        bins=[0, 1, 3, 100],
        labels=["Rank 1 (Best)", "Rank 2-3", "Rank 4+"],
        right=True,
    )

    counts = (
        summary_df
        .groupby(["league_key", "defence_tier"], observed=True)
        .size()
        .unstack(fill_value=0)
    )

    # Ensure all tiers are present as columns
    for tier in ["Rank 1 (Best)", "Rank 2-3", "Rank 4+"]:
        if tier not in counts.columns:
            counts[tier] = 0

    counts = counts[["Rank 1 (Best)", "Rank 2-3", "Rank 4+"]]

    league_order = [k for k in LEAGUE_COLORS if k in counts.index]
    counts = counts.loc[league_order]

    full_names = {
        "EPL":        "Premier League\n🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "LALIGA":     "La Liga\n🇪🇸",
        "BUNDESLIGA": "Bundesliga\n🇩🇪",
        "SERIE_A":    "Serie A\n🇮🇹",
        "LIGUE_1":    "Ligue 1\n🇫🇷",
    }
    counts.index = [full_names.get(k, k) for k in counts.index]

    fig, ax = plt.subplots(figsize=(12, 6))

    # Green = best defence won, Orange = mid, Red = poor defence won
    bar_colors = ["#2ecc71", "#f39c12", "#e74c3c"]
    bottom     = np.zeros(len(counts))

    for tier, color in zip(counts.columns, bar_colors):
        values = counts[tier].values
        bars   = ax.bar(
            counts.index, values,
            bottom=bottom,
            color=color,
            label=tier,
            alpha=0.88,
            width=0.55,
            zorder=3,
        )

        # Annotate each bar segment with count
        for bar, val, bot in zip(bars, values, bottom):
            if val > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bot + val / 2,
                    str(int(val)),
                    ha="center", va="center",
                    fontsize=13, fontweight="bold",
                    color="white"
                )
        bottom += values

    # Total seasons label at top of each bar
    for i, total in enumerate(counts.sum(axis=1)):
        ax.text(
            i, total + 0.05,
            f"/{int(total)} seasons",
            ha="center", va="bottom",
            fontsize=9, color="grey"
        )

    ax.set_ylabel("Number of Title Winners", fontsize=12)
    ax.set_title(
        "Did the Best Defensive Team Win the Title?\n"
        "Breakdown by defensive rank tier across 5 seasons",
        fontsize=13, fontweight="bold"
    )
    ax.set_ylim(0, 6.5)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(1))
    ax.legend(
        title="Champion's Defensive Rank",
        fontsize=10, title_fontsize=10,
        loc="upper right"
    )
    ax.grid(axis="y", alpha=0.4, zorder=0)

    fig.text(
        0.5, -0.03,
        "Green = best defence in league won the title | "
        "Red = title won by team with 4th or lower defensive rank",
        ha="center", fontsize=9, style="italic", color="grey"
    )

    plt.tight_layout()
    _save(fig, "08_hypothesis_summary_bar.png")
    return fig


# ============================================================
# CHART 9: Spearman Correlation Bar Chart
# ============================================================
def plot_spearman_results(df: pd.DataFrame) -> plt.Figure:
    """
    Bar chart showing Spearman rank correlation coefficients
    between defensive rank and final position per league.
    Displays p-value significance markers on each bar.

    WHY SPEARMAN not Pearson:
    Both variables are ordinal ranks (1st, 2nd, 3rd).
    Spearman is rank-based and does not assume a linear
    or normal relationship. Think of it as asking:
    when defensive rank goes up does final position
    tend to go up proportionally?
    """
    results = []

    for league_key in LEAGUE_COLORS:
        subset = df[df["league_key"] == league_key].dropna(
            subset=["defensive_rank", "position"]
        )
        if len(subset) < 10:
            continue

        rho, p_val = stats.spearmanr(
            subset["defensive_rank"].astype(float),
            subset["position"].astype(float)
        )
        results.append({
            "league_key":   league_key,
            "spearman_rho": round(rho, 3),
            "p_value":      round(p_val, 4),
            "significant":  p_val < 0.05,
            "n":            len(subset),
        })

    if not results:
        logger.warning("No Spearman results computed")
        return plt.figure()

    results_df  = pd.DataFrame(results)
    bar_colors  = [
        LEAGUE_COLORS.get(k, "#aaa")
        for k in results_df["league_key"]
    ]

    fig, ax = plt.subplots(figsize=(10, 5))

    bars = ax.bar(
        results_df["league_key"],
        results_df["spearman_rho"],
        color=bar_colors,
        alpha=0.85,
        width=0.5,
        zorder=3,
    )

    # Annotate bars with rho value and significance stars
    for bar, row in zip(bars, results_df.itertuples()):
        sig_star = (
            "**" if row.p_value < 0.01
            else ("*" if row.p_value < 0.05 else "ns")
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"ρ={row.spearman_rho}\n{sig_star}",
            ha="center", va="bottom",
            fontsize=10, fontweight="bold"
        )

    ax.axhline(
        0, color="black", linewidth=0.8,
        linestyle="--", alpha=0.4
    )
    ax.set_ylim(-0.1, 1.1)
    ax.set_ylabel(
        "Spearman ρ (Defensive Rank vs Final Position)",
        fontsize=11
    )
    ax.set_title(
        "Spearman Rank Correlation: "
        "Defensive Rank ↔ Final League Position\n"
        "** p<0.01 | * p<0.05 | ns = not significant",
        fontsize=13, fontweight="bold"
    )
    ax.set_xticklabels(results_df["league_key"], fontsize=11)
    ax.grid(axis="y", alpha=0.4, zorder=0)

    fig.text(
        0.5, -0.04,
        "ρ close to +1.0 = teams with better defences consistently "
        "finish higher | ρ near 0 = no relationship",
        ha="center", fontsize=9, style="italic", color="grey"
    )

    plt.tight_layout()
    _save(fig, "09_spearman_correlation.png")
    return fig


# ============================================================
# CHART 10: Final Dashboard — 2x2 Summary Grid
# ============================================================
def plot_final_summary_dashboard(
    df: pd.DataFrame,
    summary_df: pd.DataFrame
) -> plt.Figure:
    """
    A 2x2 summary grid combining key findings into one figure.

    Top-left:     Violin — champion defensive rank distribution
    Top-right:    GA vs Points cross-league scatter + OLS line
    Bottom-left:  % titles won by top-3 defence per league
    Bottom-right: Avg champion GA per league (horizontal bar)

    WHY THIS CHART:
    One-page executive summary. If someone only sees one chart
    this is the one that tells the complete story.
    """
    fig = plt.figure(figsize=(16, 12))
    fig.suptitle(
        "Does Best Defence Win the Title? — Executive Summary\n"
        "Top 5 European Leagues | 5 Seasons (2019/20–2023/24)",
        fontsize=15, fontweight="bold", y=1.01
    )

    gs  = fig.add_gridspec(2, 2, hspace=0.4, wspace=0.35)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    # ---- Top-left: Violin — champion defensive rank ----
    champions     = df[df["position"] == 1].copy()
    champion_ranks = champions["champion_def_rank"].dropna().astype(float)

    ax1.violinplot(
        champion_ranks, positions=[1],
        showmedians=True, showextrema=True
    )
    ax1.scatter(
        [1] * len(champion_ranks), champion_ranks,
        alpha=0.6, color="#3498db", s=50, zorder=3
    )
    ax1.axhline(
        1, color="green", linestyle="--",
        alpha=0.5, label="Best defence = rank 1"
    )
    ax1.set_xlim(0, 2)
    ax1.set_xticks([])
    ax1.set_ylabel("Defensive Rank")
    ax1.set_title(
        "Champions' Defensive Rank\n(All Leagues & Seasons)",
        fontsize=11, fontweight="bold"
    )
    ax1.legend(fontsize=8)

    # ---- Top-right: GA vs Points scatter ----
    for league_key, color in LEAGUE_COLORS.items():
        s = df[df["league_key"] == league_key].dropna(
            subset=["goals_against", "points"]
        )
        ax2.scatter(
            s["goals_against"], s["points"],
            color=color, alpha=0.4, s=25, label=league_key
        )

    clean   = df.dropna(subset=["goals_against", "points"])
    m, b, r, p, _ = stats.linregress(
        clean["goals_against"].astype(float),
        clean["points"].astype(float)
    )
    x_r = np.linspace(
        clean["goals_against"].min(),
        clean["goals_against"].max(),
        100
    )
    ax2.plot(
        x_r, m * x_r + b,
        color="black", linewidth=2,
        linestyle="--", label=f"Overall r²={r**2:.2f}"
    )
    ax2.set_xlabel("Goals Conceded")
    ax2.set_ylabel("Points")
    ax2.set_title(
        "Goals Conceded vs Points\n(All Leagues)",
        fontsize=11, fontweight="bold"
    )
    ax2.legend(fontsize=7, ncol=2)

    # ---- Bottom-left: % titles won by top-3 defence ----
    pct_data = (
        summary_df
        .groupby("league_key")
        .apply(
            lambda x: (x["champion_def_rank"] <= 3).mean() * 100
        )
        .reset_index()
    )
    pct_data.columns   = ["league_key", "pct_top3_def"]
    league_order       = [
        k for k in LEAGUE_COLORS
        if k in pct_data["league_key"].values
    ]
    pct_data           = (
        pct_data.set_index("league_key")
        .loc[league_order]
        .reset_index()
    )
    bar_colors_pct     = [
        LEAGUE_COLORS[k] for k in pct_data["league_key"]
    ]

    bars = ax3.bar(
        pct_data["league_key"],
        pct_data["pct_top3_def"],
        color=bar_colors_pct, alpha=0.85
    )
    ax3.axhline(
        50, color="orange", linestyle="--",
        linewidth=1.2, label="50% line"
    )
    ax3.axhline(
        80, color="green", linestyle="--",
        linewidth=1.2, label="80% line"
    )
    for bar in bars:
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{bar.get_height():.0f}%",
            ha="center", fontsize=10, fontweight="bold"
        )
    ax3.set_ylim(0, 115)
    ax3.set_ylabel("% Titles Won by Top-3 Defence")
    ax3.set_title(
        "Titles Won by Top-3 Defensive Team\n"
        "(% out of 5 seasons)",
        fontsize=11, fontweight="bold"
    )
    ax3.legend(fontsize=8)

    # ---- Bottom-right: Avg champion GA per league ----
    avg_ga = (
        summary_df
        .groupby("league_key")["champion_ga"]
        .mean()
        .reset_index()
        .sort_values("champion_ga")
    )
    h_colors = [
        LEAGUE_COLORS.get(k, "#aaa") for k in avg_ga["league_key"]
    ]
    ax4.barh(
        avg_ga["league_key"], avg_ga["champion_ga"],
        color=h_colors, alpha=0.85
    )
    ax4.set_xlabel("Avg Goals Conceded by Champion")
    ax4.set_title(
        "Average Champion's Goals Conceded\n"
        "(Lower = More Defensive Title Winner)",
        fontsize=11, fontweight="bold"
    )
    for i, (_, row) in enumerate(avg_ga.iterrows()):
        ax4.text(
            row["champion_ga"] + 0.3, i,
            f"{row['champion_ga']:.1f}",
            va="center", fontsize=10
        )

    plt.tight_layout()
    _save(fig, "10_final_summary_dashboard.png")
    return fig