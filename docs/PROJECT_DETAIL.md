# PROJECT DETAIL
## Does Defence Win You Titles?

---

## 1. WHAT WE DID

A structured data analysis project examining 5 seasons of standings
data (2019/20 to 2023/24) across Europe's Top 5 football leagues
to determine whether having the best defensive record is a reliable
predictor of winning the league title or finishing in the top 4.

**Leagues:** Premier League, La Liga, Bundesliga, Serie A, Ligue 1

**Data source:** API-Football (api-football.com) free plan

**Primary metric:** Goals conceded (goals against) per season

---

## 2. WHY WE DID IT

The popular belief in football is that defence wins titles.
While attack generates highlights, the hypothesis is that the most
consistent path to a league title runs through keeping clean sheets
and conceding few goals.

This project tests that claim with 5 years of real data across
five different footballing cultures and styles of play.

---

## 3. CORE QUESTION

> Do the best defensive teams consistently win their league titles?

### Three sub-hypotheses tested:
1. Title winners consistently rank in the top 2 for goals conceded
2. Goals conceded is negatively correlated with final position
3. Defensive stats alone can predict a Top 4 finish

---

## 4. METHODOLOGY

### Stage 1 — Problem Definition
- Objective: Test whether defensive performance predicts title success
- Success metric: Spearman correlation + % of titles won by best defence
- Hypothesis: Defensive rank is positively correlated with final position

### Stage 2 — Data Acquisition
- Endpoint: API-Football /standings
- Scope: 5 leagues x 5 seasons = 25 league-season combinations
- All responses cached to data/raw/ as JSON files
- Free plan limit (100 req/day) managed via caching

### Stage 3 — Data Cleaning
Key decisions made:
- Rows with null position or goals_against dropped (critical fields)
- goals_against_avg recomputed from raw counts where null
- Duplicates removed by natural key: (league_key, season, team_id)
- Outliers flagged by Z-score (threshold 3.0) but NOT removed
- Used Int64 nullable integers to safely handle NaN in integer cols

### Stage 4 — Exploratory Data Analysis
Charts produced:
- Goals conceded distribution per league (box + swarm)
- Correlation heatmap of all key metrics
- Goals against vs Points scatter with regression lines
- Champion defensive rank heatmap per league per season

### Stage 5 — Feature Engineering
New metrics derived:
- defensive_rank: within-league-season rank (1 = best defence)
- ga_vs_median: goals against vs league-season median
- champion_def_rank: defensive rank of title winner each season
- def_efficiency: composite score (50% GA + 50% win rate)
- ga_change_yoy: year-on-year improvement in goals conceded

### Stage 6 — Statistical Inference
Tests run:
- Spearman rank correlation: defensive_rank vs position per league
- Pearson correlation: goals_against vs points (continuous)
- Logistic regression: predict Top 4 from defensive stats
- Bootstrap confidence intervals for Spearman rho
- Significance threshold: alpha = 0.05

### Stage 7 — Interpretation
- 10 charts covering distribution, correlation, hypothesis testing
- Executive summary dashboard combining all key findings
- Full narrative conclusions with per-league breakdown

---

## 5. KEY FINDINGS

*(Fill these in after running python main.py --step all)*

### Finding 1: How often did the best defence win the title?
- 70% of seasons — the champion had the #1 ranked defence in their league
- 90% of seasons — the champion had a top-3 defence

### Finding 2.1 Per league breakdown

League         Best defence won                     Avg champion def rank
Bundesliga     100% — every single season           1.0
La Liga 🇪🇸     100% — every single season           1.0
Serie A 🇮🇹     100% — every single season           1.0
Premier League  50%                                1.5
Ligue 1 🇫🇷       0% — never the best defence        3.0

Ligue 1 is the outlier — PSG wins titles with goals not defence.

### Finding 2.2  Spearman Correlation
All 5 leagues are highly significant (p=0.0000):

Bundesliga: ρ=0.890 — strongest relationship
Serie A: ρ=0.872
Ligue 1: ρ=0.838 — even here, defence still correlates with position
La Liga: ρ=0.821
EPL: ρ=0.815

Every single league shows a strong, statistically significant relationship between defensive rank and final position.

### Finding 3: Pearson Correlation

r = -0.790 — strong negative correlation
p = 1.15e-42 — essentially impossible this is by chance

Teams that concede fewer goals earn significantly more points across all leagues.

---

## 6. CONCLUSIONS

### Does the best defensive team win the title?
Yes but not in every league.
3 out of 5 leagues it was perfect. The hypothesis is strongly supported by the data.
Premier leauge and League 1 are exceptions
---

## 7. LIMITATIONS

- Free API plan means standings only — no xGA, no shot data,
  no pressing metrics. All defensive measurement is outcomes-based.
- 5 seasons is reasonable but some leagues have consistent
  single-team dominance (Bayern, PSG) which reduces variability.
- The 2019/20 season was affected by COVID-19.

---

## 8. FUTURE WORK

- Add xGA and shots on target with a paid API tier
- Build logistic regression: P(Top 4) = f(GA, clean sheets, xGA)
- Include player-level data to identify which defenders drive results
- Extend to 10 seasons for stronger statistical power

---

## 9. SECURITY NOTES

- API key stored in .env file — excluded from git via .gitignore
- Loaded via python-dotenv — never hardcoded or printed in logs
- Raw data cached locally in data/raw/ — do not commit if your
  plan has strict redistribution limits

### Claude Code Specific Risks
- If using Claude Code on this project, never pass raw API
  response text directly into AI prompts — parse with json.loads()
  first to prevent prompt injection via malicious team name fields
- Use git-secrets or GitHub secret scanning to catch accidental
  key commits before they reach the remote
- Set FORCE_REFETCH=false when running in agentic loops to
  prevent burning your 100 req/day limit on repeated runs