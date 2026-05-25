from unittest.mock import MagicMock, patch

from social import share_to_platforms


def test_share_to_platforms_twitter_success(monkeypatch):
    monkeypatch.setenv("TWITTER_API_KEY", "key")
    monkeypatch.setenv("TWITTER_API_SECRET", "secret")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "token")
    monkeypatch.setenv("TWITTER_ACCESS_SECRET", "access_secret")

    with patch("tweepy.Client.create_tweet") as mock_tweet:
        mock_response = MagicMock()
        mock_response.data = {"id": "12345", "text": "Test tweet"}
        mock_tweet.return_value = mock_response

        # LinkedIn will fail due to missing keys, which is expected
        monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)

        results = share_to_platforms("Test Post", "http://example.com", ["tag1"])

        assert len(results) == 2

        twitter_result = next(r for r in results if r["platform"] == "twitter")
        assert twitter_result["status"] == "success"
        assert twitter_result["url"] == "https://twitter.com/user/status/12345"

        linkedin_result = next(r for r in results if r["platform"] == "linkedin")
        assert linkedin_result["status"] == "error"

def test_share_to_platforms_missing_keys(monkeypatch):
    monkeypatch.delenv("TWITTER_API_KEY", raising=False)
    monkeypatch.delenv("LINKEDIN_ACCESS_TOKEN", raising=False)

    results = share_to_platforms("Test Post", "http://example.com", ["tag1"])

    assert len(results) == 2
    for r in results:
        assert r["status"] == "error"
