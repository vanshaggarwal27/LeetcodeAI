"""
Unit tests for the Dev.to publishing service in devto.py.
Tests use mock_devto_request to avoid real HTTP calls.
"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class TestPostToPlatform:
    async def test_successful_publish_returns_dict(self, mock_devto_request):
        """Successful publish returns parsed JSON dict."""
        from devto import post_to_platform

        result = await post_to_platform("Two Sum", "# Blog content")
        assert isinstance(result, dict)
        assert result["id"] == 123

    async def test_post_sends_correct_title(self, mock_devto_request):
        """The title is included in the request body."""
        from devto import post_to_platform

        await post_to_platform("Two Sum", "# Blog content")
        call_kwargs = mock_devto_request["request"].call_args[1]
        assert call_kwargs["json"]["article"]["title"] == "LeetCode Solution: Two Sum"

    async def test_post_sends_correct_content(self, mock_devto_request):
        """The markdown content is included in the request body."""
        from devto import post_to_platform

        await post_to_platform("Two Sum", "# Blog content here")
        call_kwargs = mock_devto_request["request"].call_args[1]
        assert "# Blog content here" in (
            call_kwargs["json"]["article"]["body_markdown"]
        )

    async def test_devto_api_error_raises(self, mock_devto_request):
        """Non-2xx response raises an exception."""
        from devto import post_to_platform

        mock_devto_request["response"].status_code = 500
        mock_devto_request["response"].text = "Internal Server Error"

        with pytest.raises(Exception):
            await post_to_platform("Two Sum", "# Blog content")


class TestNormalizePlatforms:
    def test_defaults_to_devto(self):
        from devto import normalize_platforms

        assert normalize_platforms(None) == ["devto"]

    def test_deduplicates_platforms(self):
        from devto import normalize_platforms

        result = normalize_platforms(["dev.to", "devto"])
        assert result == ["devto"]

    def test_rejects_unknown_provider(self):
        from devto import PublisherError, normalize_platforms

        with pytest.raises(PublisherError):
            normalize_platforms(["wordpress"])


class TestHashnodePublisher:
    """Unit tests for HashnodePublisher using mocked HTTP calls."""

    @pytest.mark.asyncio
    async def test_missing_credentials_raises_before_http(self, monkeypatch):
        """HashnodePublisher raises PublisherError when env vars are absent."""
        from devto import HashnodePublisher, PublisherError

        monkeypatch.delenv("HASHNODE_TOKEN", raising=False)
        monkeypatch.delenv("HASHNODE_PUBLICATION_ID", raising=False)
        publisher = HashnodePublisher()
        with pytest.raises(PublisherError, match="HASHNODE_TOKEN"):
            await publisher.publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    @pytest.mark.asyncio
    async def test_successful_publish_returns_url(self, mock_hashnode_request):
        """Successful GraphQL response returns a PublishResult with the post URL."""
        from devto import HashnodePublisher

        publisher = HashnodePublisher()
        result = await publisher.publish(
            "Two Sum", "# content", tags=["leetcode"], published=True
        )
        assert result.url == "https://username.hashnode.dev/leetcode-solution-two-sum"
        assert result.status == "success"
        assert result.platform == "hashnode"

    @pytest.mark.asyncio
    async def test_graphql_error_raises_publisher_error(self, mock_hashnode_request):
        """A GraphQL errors list in the response raises PublisherError."""
        from devto import HashnodePublisher, PublisherError

        mock_hashnode_request["response"].json.return_value = {
            "errors": [{"message": "Publication not found"}]
        }
        publisher = HashnodePublisher()
        with pytest.raises(PublisherError):
            await publisher.publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    @pytest.mark.asyncio
    async def test_graphql_error_message_is_propagated(self, mock_hashnode_request):
        """The first GraphQL error message appears in the PublisherError."""
        from devto import HashnodePublisher, PublisherError

        error_msg = "Publication not found"
        mock_hashnode_request["response"].json.return_value = {
            "errors": [{"message": error_msg}]
        }
        publisher = HashnodePublisher()
        with pytest.raises(PublisherError, match=error_msg):
            await publisher.publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    @pytest.mark.asyncio
    async def test_graphql_multiple_errors_uses_first(self, mock_hashnode_request):
        """When multiple GraphQL errors are present, the first message is used."""
        from devto import HashnodePublisher, PublisherError

        mock_hashnode_request["response"].json.return_value = {
            "errors": [
                {"message": "First error"},
                {"message": "Second error"},
            ]
        }
        publisher = HashnodePublisher()
        with pytest.raises(PublisherError, match="First error"):
            await publisher.publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    @pytest.mark.asyncio
    async def test_graphql_error_without_message_uses_fallback(
        self, mock_hashnode_request
    ):
        """GraphQL error dict without 'message' key still raises PublisherError."""
        from devto import HashnodePublisher, PublisherError

        mock_hashnode_request["response"].json.return_value = {
            "errors": [{"extensions": {"code": "NOT_FOUND"}}]
        }
        publisher = HashnodePublisher()
        with pytest.raises(PublisherError):
            await publisher.publish(
                "Two Sum", "# content", tags=["leetcode"], published=True
            )

    @pytest.mark.asyncio
    async def test_empty_errors_list_does_not_raise(self, mock_hashnode_request):
        """An empty 'errors' list is not treated as a failure."""
        from devto import HashnodePublisher

        mock_hashnode_request["response"].json.return_value = {
            "errors": [],
            "data": {
                "publishPost": {
                    "post": {
                        "id": "hn-post-123",
                        "url": "https://username.hashnode.dev/leetcode-solution-two-sum",
                        "title": "LeetCode Solution: Two Sum",
                    }
                }
            },
        }
        publisher = HashnodePublisher()
        result = await publisher.publish(
            "Two Sum", "# content", tags=["leetcode"], published=True
        )
        assert result.status == "success"

