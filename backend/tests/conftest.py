"""
Shared pytest fixtures for the backend test suite.

Phase 2 will populate this file with:
- A TestClient fixture for FastAPI routes
- Mock fixtures for Gemini API responses
- Mock fixtures for Dev.to API responses
- A mock MongoDB fixture
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import responses
from fastapi.testclient import TestClient


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class FakePreferencesCollection:
    def __init__(self) -> None:
        self.update_one = AsyncMock()


class FakeDatabase:
    def __init__(self) -> None:
        self.preferences = FakePreferencesCollection()


class FakeMotorClient:
    def __init__(self, database: FakeDatabase) -> None:
        self.leetcodeai = database


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("DEVTO_API_KEY", "test-devto-key")
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "test-twilio-sid")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test-twilio-token")
    monkeypatch.setenv("TWILIO_PHONE_NUMBER", "+10000000000")
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017/test")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-elevenlabs-key")


@pytest.fixture
def app_module(monkeypatch: pytest.MonkeyPatch):
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))

    fake_db = FakeDatabase()

    monkeypatch.setattr(
        "apscheduler.schedulers.background.BackgroundScheduler.start",
        lambda self: None,
    )
    monkeypatch.setattr(
        "twilio.rest.Client",
        lambda *args, **kwargs: Mock(name="twilio_client"),
    )
    monkeypatch.setattr(
        "motor.motor_asyncio.AsyncIOMotorClient",
        lambda *args, **kwargs: FakeMotorClient(fake_db),
    )

    for module_name in [
        "main",
        "alerts.scheduler",
        "alerts.progress_checker",
        "alerts.elevenlabs_service",
        "services.reminder_scheduler",
    ]:
        sys.modules.pop(module_name, None)

    module = importlib.import_module("main")
    monkeypatch.setattr(module, "db", fake_db)
    monkeypatch.setattr(module, "start_scheduler", Mock(name="start_scheduler"))
    return module


@pytest.fixture
def client(app_module):
    with TestClient(app_module.app) as test_client:
        yield test_client


@pytest.fixture
def mock_generate_blog(app_module, mocker):
    return mocker.patch.object(
        app_module,
        "generate_blog",
        autospec=True,
        return_value="# Mock blog content",
    )


@pytest.fixture
def mock_post_to_platform(app_module, mocker):
    return mocker.patch.object(
        app_module,
        "publish_to_platforms",
        autospec=True,
        return_value=[{
            "platform": "devto",
            "status": "success",
            "url": "https://dev.to/mock-post",
            "response": {"id": 123, "url": "https://dev.to/mock-post"}
        }],
        )


@pytest.fixture
def mock_db(app_module):
    return app_module.db


@pytest.fixture
def mock_gemini_client(mocker):
    ai_module = importlib.import_module("ai")
    
    response = Mock(name="gemini_response")
    response.text = "# Mock blog content"
    
    mock_client = Mock(name="gemini_client")
    mock_client.models.generate_content.return_value = response
    
    client_factory = mocker.patch.object(
        ai_module.genai,
        "Client",
        autospec=False,
        return_value=mock_client,
    )
    return {
        "client_factory": client_factory,
        "client": mock_client,
        "model": mock_client.models,
    }


@pytest.fixture
def mock_devto_request(mocker):
    devto_module = importlib.import_module("devto")
    response = Mock(name="devto_response")
    response.status_code = 201
    response.json.return_value = {"id": 123, "url": "https://dev.to/mock-post"}
    request_mock = mocker.patch.object(
        devto_module.requests,
        "post",
        autospec=True,
        return_value=response,
    )
    return {"request": request_mock, "response": response}


@pytest.fixture
def responses_mock():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps
