"""
Unit tests for the Dev.to publishing service in devto.py.
Tests use mock_devto_request to avoid real HTTP calls.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class TestPostToPlatform:

    def test_successful_publish_returns_dict(
        self, mock_devto_request
    ):
        """Successful publish returns parsed JSON dict."""
        from devto import post_to_platform

        result = post_to_platform("Two Sum", "# Blog content")
        assert isinstance(result, dict)
        assert result["id"] == 123

    def test_post_sends_correct_title(
        self, mock_devto_request
    ):
        """The title is included in the request body."""
        from devto import post_to_platform

        post_to_platform("Two Sum", "# Blog content")
        call_kwargs = mock_devto_request["request"].call_args[1]
        assert call_kwargs["json"]["article"]["title"] == "LeetCode Solution: Two Sum"

    def test_post_sends_correct_content(
        self, mock_devto_request
    ):
        """The markdown content is included in the request body."""
        from devto import post_to_platform

        post_to_platform("Two Sum", "# Blog content here")
        call_kwargs = mock_devto_request["request"].call_args[1]
        assert "# Blog content here" in (
            call_kwargs["json"]["article"]["body_markdown"]
        )

    def test_devto_api_error_raises(
        self, mock_devto_request
    ):
        """Non-2xx response raises an exception."""
        from devto import post_to_platform

        mock_devto_request["response"].status_code = 500
        mock_devto_request["response"].text = "Internal Server Error"

        with pytest.raises(Exception):
            post_to_platform("Two Sum", "# Blog content")


class TestNormalizePlatforms:

    def test_defaults_to_devto(self):
        from devto import normalize_platforms
        assert normalize_platforms(None) == ["devto"]

    def test_deduplicates_platforms(self):
        from devto import normalize_platforms
        result = normalize_platforms(["dev.to", "devto"])
        assert result == ["devto"]

    def test_rejects_unknown_provider(self):
        from devto import normalize_platforms, PublisherError
        with pytest.raises(PublisherError):
            normalize_platforms(["wordpress"])
