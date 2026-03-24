# ⚽ Does Defence Win You Titles?

A rigorous data analysis project examining whether defensive performance
predicts league title success across Europe's Top 5 leagues over 5 seasons.

---

## 🎯 Research Question

> **"Do the best defensive teams consistently win their league titles?"**

### Sub-Hypotheses
1. Title winners consistently rank #1 or #2 in goals conceded
2. Goals conceded is negatively correlated with final league position
3. Defensive stats alone can predict Top 4 finishes

---

## 📁 Project Structure
```
does-defence-win-you-titles/
│
├── data/
│   ├── raw/                    # Cached JSON responses from API
│   └── processed/              # Cleaned CSVs ready for analysis
│
├── src/
│   ├── collectors/
│   │   ├── api_client.py       # API-Football HTTP client + caching
│   │   └── data_fetcher.py     # Fetches standings per league/season
│   │
│   ├── processors/
│   │   ├── cleaner.py          # Cleans and validates raw data
│   │   └── feature_engineer.py # Derives defensive metrics
│   │
│   └── visualizers/
│       ├── eda_plots.py        # Charts 1-4: EDA visualisations
│       ├── league_plots.py     # Charts 5-7: per-league profiles
│       └── summary_plots.py    # Charts 8-10: hypothesis validation
│
├── notebooks/
│   ├── 01_data_collection.ipynb
│   ├── 02_cleaning_eda.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_statistical_analysis.ipynb
│   └── 05_visualizations_conclusions.ipynb
│
├── outputs/
│   ├── figures/                # All 10 saved plots (PNG)
│   └── reports/                # Final summary report
│
├── tests/
│   ├── test_api_client.py
│   └── test_cleaner.py
│
├── docs/
│   ├── PROJECT_DETAIL.md       # Full analysis narrative
│   └── GIT_WORKFLOW.md         # Branch and commit strategy
│
├── .env.example                # API key template
├── .gitignore
├── requirements.txt
├── config.py                   # All constants and settings
└── main.py                     # Pipeline entry point
```

---

## 🚀 Quickstart

### 1. Clone and setup
```bash
git clone https://github.com/poudelrishii/does-defence-win-you-titles.git
cd does-defence-win-you-titles
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API key
```bash
copy .env.example .env
# Open .env and paste your API key from:
# https://dashboard.api-football.com/profile?access
```

### 3. Run full pipeline
```bash
python main.py --step all
```

### 4. Or run step by step
```bash
python main.py --step fetch       # Fetch data from API
python main.py --step process     # Clean and engineer features
python main.py --step visualise   # Generate all 10 charts
python main.py --step report      # Print statistical findings
```

### 5. Open notebooks interactively
```bash
jupyter lab
```

---

## 📊 Leagues Covered

| League | Country | API ID |
|---|---|---|
| Premier League | England | 39 |
| La Liga | Spain | 140 |
| Bundesliga | Germany | 78 |
| Serie A | Italy | 135 |
| Ligue 1 | France | 61 |

**Seasons:** 2019/20 · 2020/21 · 2021/22 · 2022/23 · 2023/24

---

## 📈 Charts Generated

| # | Chart | Type |
|---|---|---|
| 01 | GA distribution by league | Box + swarm |
| 02 | Correlation heatmap | Heatmap |
| 03 | GA vs Points | Scatter + regression |
| 04 | Champion defensive rank | Grid heatmap |
| 05 | Top 4 defensive bars | Grouped bar |
| 06 | Champion GA trend | Line chart |
| 07 | Defensive radar | Spider chart |
| 08 | Hypothesis summary | Stacked bar |
| 09 | Spearman correlation | Bar chart |
| 10 | Executive dashboard | 2x2 grid |

---

## 🔐 Security

- API key stored in `.env` — never committed to git
- `.env` is blocked by `.gitignore`
- Use `.env.example` as the safe template
- Raw JSON cache in `data/raw/` — excluded from git

---

## 📄 Full Report

See `docs/PROJECT_DETAIL.md` for the complete analysis narrative,
methodology, findings, conclusions and limitations.