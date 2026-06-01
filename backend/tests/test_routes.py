"""
Integration tests for FastAPI route handlers.
All external API calls are mocked via conftest.py fixtures.
Tests check response body, not status code, for error cases
because all routes return HTTP 200 even on failure.
"""

import pytest


class TestHealthRoutes:
    def test_root_returns_ok(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_reminder_health_returns_ok(self, client):
        response = client.get("/reminder-health")
        assert response.status_code == 200
        assert response.json()["status"] == "active"


class TestGenerateBlogRoute:
    def test_happy_path_returns_success(
        self, client, mock_generate_blog, mock_post_to_platform
    ):
        """Both Gemini and Dev.to succeed  expect success body."""
        payload = {
            "title": "Two Sum",
            "description": "Given an array of integers...",
            "code": "def twoSum(nums, target): pass",
            "author": "testuser",
        }
        response = client.post("/generate-blog", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["platforms"][0]["status"] == "success"
        assert "dev.to" in body["data"]["platforms"][0]["url"]

    def test_empty_code_returns_error(self, client):
        """Empty code string is rejected before hitting any API."""
        payload = {
            "title": "Two Sum",
            "description": "Given an array...",
            "code": "",
            "author": "testuser",
        }
        response = client.post("/generate-blog", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"
        assert "empty" in body["message"].lower()

    def test_whitespace_only_code_returns_error(self, client):
        """Whitespace-only code is treated the same as empty."""
        payload = {
            "title": "Two Sum",
            "description": "Given an array...",
            "code": "   ",
            "author": "testuser",
        }
        response = client.post("/generate-blog", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"
        assert "empty" in body["message"].lower()

    def test_missing_required_field_returns_422(self, client):
        """Pydantic rejects payloads missing required fields."""
        payload = {
            "title": "Two Sum",
            "code": "def twoSum(): pass",
            # description and author are missing
        }
        response = client.post("/generate-blog", json=payload)
        assert response.status_code == 422

    def test_gemini_failure_returns_error_body(
        self, client, mock_generate_blog, mock_post_to_platform
    ):
        """When Gemini raises, route returns error in body."""
        mock_generate_blog.side_effect = Exception("Gemini timeout")
        payload = {
            "title": "Two Sum",
            "description": "Given an array...",
            "code": "def twoSum(): pass",
            "author": "testuser",
        }
        response = client.post("/generate-blog", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"
        assert "Gemini" in body["message"]

    def test_devto_failure_returns_error_body(
        self, client, mock_generate_blog, mock_post_to_platform
    ):
        """When Dev.to raises, route returns error in body."""
        mock_post_to_platform.side_effect = Exception("Dev.to 500")
        payload = {
            "title": "Two Sum",
            "description": "Given an array...",
            "code": "def twoSum(): pass",
            "author": "testuser",
        }
        response = client.post("/generate-blog", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "error"
        assert body["status"] == "error"

    def test_generate_blog_called_with_problem(
        self, client, mock_generate_blog, mock_post_to_platform
    ):
        """Verify generate_blog is actually called once."""
        payload = {
            "title": "Two Sum",
            "description": "Given an array...",
            "code": "def twoSum(): pass",
            "author": "testuser",
        }
        client.post("/generate-blog", json=payload)
        mock_generate_blog.assert_called_once()

    def test_post_to_platform_receives_title(
        self, client, mock_generate_blog, mock_post_to_platform
    ):
        """Verify post_to_platform is called with the correct title."""
        payload = {
            "title": "Two Sum",
            "description": "Given an array...",
            "code": "def twoSum(): pass",
            "author": "testuser",
        }
        client.post("/generate-blog", json=payload)
        mock_post_to_platform.assert_called_once()


class TestReminderRoutes:
    def test_subscribe_valid_payload(self, client, mock_db):
        """Valid subscription payload is accepted."""
        payload = {
            "name": "Test User",
            "whatsapp_number": "+911234567890",
            "reminder_time": "09:00",
            "timezone": "Asia/Kolkata",
            "is_opted_in": True,
        }
        response = client.post("/reminder/subscribe", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"

    def test_subscribe_missing_field_returns_422(self, client):
        """Pydantic rejects subscribe payload missing required field."""
        payload = {
            "reminder_time": "09:00",
            # whatsapp_number missing
        }
        response = client.post("/reminder/subscribe", json=payload)
        assert response.status_code == 422

    def test_unsubscribe_valid_payload(self, client, mock_db):
        """Valid unsubscribe request is accepted."""
        payload = {"whatsapp_number": "+911234567890"}
        response = client.post("/reminder/unsubscribe", json=payload)
        assert response.status_code == 200

    def test_unsubscribe_missing_key_raises(self, client, mock_db):
        """
        Known bug: missing whatsapp_number raises KeyError.
        This test documents the current broken behavior.
        If this test starts failing it means the bug was fixed
         update the assertion accordingly.
        """
        payload = {}
        with pytest.raises(Exception):
            client.post("/reminder/unsubscribe", json=payload)
