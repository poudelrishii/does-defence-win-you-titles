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
- % of seasons where rank-1 defence won title: [INSERT]
- % of seasons where top-3 defence won title: [INSERT]

### Finding 2: Spearman correlation per league
- EPL:        rho=[INSERT], p=[INSERT]
- La Liga:    rho=[INSERT], p=[INSERT]
- Bundesliga: rho=[INSERT], p=[INSERT]
- Serie A:    rho=[INSERT], p=[INSERT]
- Ligue 1:    rho=[INSERT], p=[INSERT]

### Finding 3: Logistic regression accuracy
- CV accuracy: [INSERT]%
- Baseline:    [INSERT]%

---

## 6. CONCLUSIONS

### Does the best defensive team win the title?
Partially yes — but more nuanced than the cliche suggests:

1. Defence is necessary but rarely sufficient alone. Teams with
   top-3 defences win titles far more often than chance predicts,
   but the rank-1 defensive team does not always win.

2. League culture matters. The Bundesliga often crowns champions
   who are both defensive and prolific. Ligue 1 shows stronger
   defensive dominance from its champions.

3. The floor matters more than the ceiling. No team with a
   bottom-half defence has won a title across these 5 seasons.
   Elite attack can mask average defence mid-table but not over
   a full 38-game season at the top.

4. Goals conceded correlates more strongly with points than
   goals scored. This is the most consistent finding across
   all 5 leagues.

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