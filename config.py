# ============================================================
# config.py — Central configuration for the entire project
# ============================================================
# All "magic numbers" and constants live here.
# Import this module anywhere you need league IDs, seasons, etc.
# Changing a value here propagates everywhere — no hunting through code.
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# --- Load environment variables from .env ---
# This is the ONLY place we touch the API key.
# All other modules import API_KEY from here.
load_dotenv()

# ============================================================
# PATHS
# ============================================================
ROOT_DIR        = Path(__file__).parent
DATA_RAW_DIR    = ROOT_DIR / "data" / "raw"
DATA_PROC_DIR   = ROOT_DIR / "data" / "processed"
FIGURES_DIR     = ROOT_DIR / "outputs" / "figures"
REPORTS_DIR     = ROOT_DIR / "outputs" / "reports"

# Auto-create directories if they don't exist
for _dir in [DATA_RAW_DIR, DATA_PROC_DIR, FIGURES_DIR, REPORTS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ============================================================
# API CREDENTIALS
# ============================================================
# Loaded from .env — never hardcoded here.
API_KEY          = os.getenv("API_FOOTBALL_KEY")
API_HOST         = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")
API_BASE_URL     = os.getenv("API_BASE_URL", "https://v3.football.api-sports.io")
FORCE_REFETCH    = os.getenv("FORCE_REFETCH", "false").lower() == "true"

# ============================================================
# LEAGUES — Top 5 European Leagues
# ============================================================
LEAGUES = {
    "EPL": {
        "id": 39,
        "name": "Premier League",
        "country": "England",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    },
    "LALIGA": {
        "id": 140,
        "name": "La Liga",
        "country": "Spain",
        "flag": "🇪🇸",
    },
    "BUNDESLIGA": {
        "id": 78,
        "name": "Bundesliga",
        "country": "Germany",
        "flag": "🇩🇪",
    },
    "SERIE_A": {
        "id": 135,
        "name": "Serie A",
        "country": "Italy",
        "flag": "🇮🇹",
    },
    "LIGUE_1": {
        "id": 61,
        "name": "Ligue 1",
        "country": "France",
        "flag": "🇫🇷",
    },
}

# ============================================================
# SEASONS
# ============================================================
# API-Football uses the start year of a season.
# e.g., "2023" means the 2023/24 season.
SEASONS = [2019, 2020, 2021, 2022, 2023]

# ============================================================
# ANALYSIS CONSTANTS
# ============================================================
TOP_N_TEAMS      = 4
TITLE_POSITION   = 1
TOP4_POSITIONS   = [1, 2, 3, 4]

DEFENSIVE_METRICS = [
    "goals_conceded",
    "clean_sheets",
    "goals_conceded_avg",
]

# ============================================================
# VISUALIZATION
# ============================================================
LEAGUE_COLORS = {
    "EPL":        "#3D195B",   # Premier League purple
    "LALIGA":     "#EE3224",   # La Liga red
    "BUNDESLIGA": "#D4001C",   # Bundesliga red
    "SERIE_A":    "#1A56A5",   # Serie A blue
    "LIGUE_1":    "#012168",   # Ligue 1 navy
}

FIG_SIZE_STANDARD  = (12, 7)
FIG_SIZE_WIDE      = (16, 8)
FIG_SIZE_SQUARE    = (10, 10)

PLOT_DPI           = 150
PLOT_STYLE         = "seaborn-v0_8-whitegrid"

# ============================================================
# RATE LIMITING
# ============================================================
REQUEST_DELAY_SECONDS = 1.2

# ============================================================
# LOGGING
# ============================================================
LOG_LEVEL  = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
