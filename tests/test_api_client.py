# ============================================================
# tests/test_api_client.py
# ============================================================
# PURPOSE:
#   Unit tests for the API client — specifically caching logic
#   and key validation.
#
# IMPORTANT:
#   These tests do NOT make real API calls.
#   We use mocking to simulate responses.
#   This means they work with zero API quota usage.
# ============================================================

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Set env vars before importing modules that read them
os.environ["API_FOOTBALL_KEY"] = "test_key_12345"
os.environ["FORCE_REFETCH"]    = "false"

from src.collectors.api_client import (
    APIFootballClient,
    _cache_path,
    _load_from_cache,
)


class TestCaching:
    """Test that caching prevents redundant API calls."""

    def test_cache_path_is_deterministic(self):
        """
        Same endpoint + params should always produce
        the same cache file path.
        If this fails, every run would re-fetch from the API
        instead of using the cached response.
        """
        path1 = _cache_path(
            "standings", {"league": 39, "season": 2023}
        )
        path2 = _cache_path(
            "standings", {"league": 39, "season": 2023}
        )
        assert path1 == path2

    def test_different_params_give_different_paths(self):
        """
        Different params must map to different cache files.
        Without this, EPL 2023 and La Liga 2023 would
        overwrite each other in the cache.
        """
        path_epl  = _cache_path(
            "standings", {"league": 39,  "season": 2023}
        )
        path_liga = _cache_path(
            "standings", {"league": 140, "season": 2023}
        )
        assert path_epl != path_liga

    def test_load_from_cache_returns_none_when_missing(
        self, tmp_path
    ):
        """
        Cache miss should return None not raise an exception.
        The client should then proceed to make a live API call.
        """
        fake_path = tmp_path / "nonexistent.json"
        result    = _load_from_cache(fake_path)
        assert result is None

    def test_load_from_cache_returns_data_when_file_exists(
        self, tmp_path
    ):
        """
        Cache hit should return the saved data without
        making any network calls.
        """
        cache_file = tmp_path / "test_cache.json"
        test_data  = {"response": [{"test": "data"}]}

        # Write test data to the cache file
        with open(cache_file, "w") as f:
            json.dump(test_data, f)

        result = _load_from_cache(cache_file)
        assert result == test_data


class TestKeyValidation:
    """Test API key validation logic."""

    def test_placeholder_key_raises_environment_error(self):
        """
        A placeholder API key should raise a clear error
        before any network call is attempted.
        This protects against accidentally running with
        an unconfigured .env file.
        """
        with patch.dict(
            os.environ,
            {"API_FOOTBALL_KEY": "your_api_key_here"}
        ):
            from importlib import reload
            import config
            reload(config)

            with pytest.raises(EnvironmentError):
                client = APIFootballClient()
                client.get(
                    "standings", {"league": 39, "season": 2023}
                )

    def test_empty_key_raises_environment_error(self):
        """
        An empty API key should also raise a clear error.
        """
        with patch.dict(os.environ, {"API_FOOTBALL_KEY": ""}):
            from importlib import reload
            import config
            reload(config)

            with pytest.raises(EnvironmentError):
                client = APIFootballClient()
                client.get(
                    "standings", {"league": 39, "season": 2023}
                )


class TestLiveRequestCount:
    """Test that the request counter tracks correctly."""

    def test_initial_count_is_zero(self):
        """
        A freshly created client should have made
        zero live requests.
        """
        with patch.dict(
            os.environ,
            {"API_FOOTBALL_KEY": "valid_test_key_abc"}
        ):
            from importlib import reload
            import config
            reload(config)

            client = APIFootballClient()
            assert client.live_request_count == 0

    @patch("src.collectors.api_client.requests.get")
    def test_count_increments_on_live_request(
        self, mock_get, tmp_path
    ):
        """
        Counter should increment by 1 for each live API call.
        Cached responses should NOT increment the counter.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": [{"league": {"standings": [[]]}}],
            "errors": {}
        }
        mock_response.headers = {
            "x-ratelimit-requests-remaining": "99"
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch("src.collectors.api_client.DATA_RAW_DIR", tmp_path):
            with patch.dict(
                os.environ,
                {"API_FOOTBALL_KEY": "valid_test_key_abc"}
            ):
                from importlib import reload
                import config
                reload(config)

                client = APIFootballClient()
                client.get(
                    "standings", {"league": 39, "season": 2023}
                )
                assert client.live_request_count == 1