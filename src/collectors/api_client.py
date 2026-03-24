# ============================================================
# src/collectors/api_client.py
# ============================================================
# PURPOSE:
#   Low-level HTTP client for API-Football.
#   Handles: authentication headers, caching to disk (JSON),
#   rate limiting, error handling, and request logging.
#
# ANALOGY:
#   Think of this as the "librarian" — you ask for a book,
#   it first checks the shelf (cache). Only if it's not there
#   does it go out to the warehouse (API) to fetch it.
#   This keeps us well within 100 requests/day on the free plan.
# ============================================================

import json
import time
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

import requests

from config import (
    API_KEY, API_HOST, API_BASE_URL,
    DATA_RAW_DIR, REQUEST_DELAY_SECONDS,
    FORCE_REFETCH, LOG_LEVEL, LOG_FORMAT
)

# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


# ============================================================
# SECURITY CHECK — fail fast if API key is missing
# ============================================================
def _validate_api_key() -> None:
    """
    Raise a clear error if the API key hasn't been configured.
    Better to crash here with a helpful message than silently
    send unauthenticated requests and get confusing 401 errors.
    """
    if not API_KEY or API_KEY == "your_api_key_here":
        raise EnvironmentError(
            "\n\n🔐 API key not found!\n"
            "Steps to fix:\n"
            "  1. cp .env.example .env\n"
            "  2. Open .env and replace 'your_api_key_here' with your real key\n"
            "  3. Get your key at: https://dashboard.api-football.com/profile?access\n"
        )


# ============================================================
# CACHE HELPERS
# ============================================================
def _cache_path(endpoint: str, params: Dict) -> Path:
    """
    Generate a deterministic file path for caching a specific API response.
    We hash the endpoint + params so each unique request maps to a unique file.

    Args:
        endpoint: API path, e.g. "standings"
        params:   Query parameters dict, e.g. {"league": 39, "season": 2023}

    Returns:
        Path object pointing to the cache file location
    """
    key_string = endpoint + json.dumps(params, sort_keys=True)
    file_hash  = hashlib.md5(key_string.encode()).hexdigest()
    return DATA_RAW_DIR / f"{file_hash}.json"


def _load_from_cache(cache_file: Path) -> Optional[Dict]:
    """
    Try to load a previously saved API response from disk.

    Returns:
        Parsed JSON dict if cache hit, None if cache miss or FORCE_REFETCH=true
    """
    if FORCE_REFETCH:
        logger.debug("FORCE_REFETCH=true — bypassing cache")
        return None

    if cache_file.exists():
        logger.info(f"📦 Cache hit: {cache_file.name}")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    return None


def _save_to_cache(cache_file: Path, data: Dict) -> None:
    """
    Persist an API response to disk as JSON.

    Args:
        cache_file: Where to write the file
        data:       The full API response dict to save
    """
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.debug(f"💾 Cached response → {cache_file.name}")


# ============================================================
# MAIN API CLIENT CLASS
# ============================================================
class APIFootballClient:
    """
    Thin wrapper around the API-Football REST API.

    Features:
    - Disk-based JSON caching (avoids re-fetching on reruns)
    - Rate limiting (sleep between requests)
    - Centralised auth headers (API key never hardcoded)
    - Structured error handling with clear messages

    Usage:
        client = APIFootballClient()
        data = client.get("standings", {"league": 39, "season": 2023})
    """

    def __init__(self):
        _validate_api_key()
        self.headers = {
            "x-rapidapi-key":  API_KEY,
            "x-rapidapi-host": API_HOST,
        }
        self._request_count = 0

    def get(self, endpoint: str, params: Dict[str, Any]) -> Dict:
        """
        Fetch data from API-Football, using cache when available.

        Flow:
          1. Check disk cache → return immediately if found
          2. Make HTTP GET request to API
          3. Validate response
          4. Save to cache
          5. Return data

        Args:
            endpoint: API endpoint name, e.g. "standings"
            params:   Query parameters, e.g. {"league": 39, "season": 2023}

        Returns:
            Parsed response dict from API-Football payload

        Raises:
            requests.HTTPError: On 4xx/5xx HTTP errors
            ValueError: If API returns error in payload
        """
        cache_file = _cache_path(endpoint, params)

        # --- Step 1: Try cache first ---
        cached = _load_from_cache(cache_file)
        if cached is not None:
            return cached

        # --- Step 2: Build URL and make request ---
        url = f"{API_BASE_URL}/{endpoint}"
        logger.info(f"🌐 API request #{self._request_count + 1}: "
                    f"{endpoint} | params={params}")

        time.sleep(REQUEST_DELAY_SECONDS)

        response = requests.get(
            url, headers=self.headers, params=params, timeout=30
        )

        # --- Step 3: HTTP-level error check ---
        response.raise_for_status()

        data = response.json()
        self._request_count += 1

        # --- Step 4: API-level error check ---
        if "errors" in data and data["errors"]:
            raise ValueError(
                f"API-Football error for {endpoint}:\n{data['errors']}"
            )

        remaining = response.headers.get(
            "x-ratelimit-requests-remaining", "unknown"
        )
        logger.info(f"   ✅ Success | Remaining today: {remaining} requests")

        # --- Step 5: Save to cache and return ---
        _save_to_cache(cache_file, data)
        return data

    @property
    def live_request_count(self) -> int:
        """Return number of actual (non-cached) API calls made this session."""
        return self._request_count
    