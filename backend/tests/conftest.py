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
from unittest.mock import AsyncMock, Mock

import pytest
import responses
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class FakeCursor:
    def __init__(self, records=None) -> None:
        self.records = records or []

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    async def to_list(self, length=None):
        if length is None:
            return [dict(record) for record in self.records]
        return [dict(record) for record in self.records[:length]]

    def __aiter__(self):
        self._iter = iter(self.records)
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


class FakeCollection:
    def __init__(self) -> None:
        self.records: list[dict] = []
        self.update_one = AsyncMock(side_effect=self._update_one)
        self.insert_one = AsyncMock(side_effect=self._insert_one)
        self.find_one = AsyncMock(side_effect=self._find_one)
        self.count_documents = AsyncMock(return_value=0)

    async def _find_one(self, query, *args, **kwargs):
        for record in self.records:
            if self._matches(record, query):
                return dict(record)
        return None

    async def _insert_one(self, record, *args, **kwargs):
        self.records.append(dict(record))
        return Mock(inserted_id=record.get("id"))

    async def _update_one(self, query, update, upsert=False, *args, **kwargs):
        payload = update.get("$set", update)
        for record in self.records:
            if self._matches(record, query):
                record.update(payload)
                return Mock(matched_count=1, modified_count=1)
        if upsert:
            self.records.append({**query, **payload})
        return Mock(matched_count=0, modified_count=0)

    def find(self, *args, **kwargs):
        query = args[0] if args else {}
        return FakeCursor([record for record in self.records if self._matches(record, query)])

    def aggregate(self, *args, **kwargs):
        return FakeCursor([])

    @staticmethod
    def _matches(record, query):
        for key, value in query.items():
            record_value = record.get(key)
            if isinstance(value, dict):
                if "$in" in value and record_value not in value["$in"]:
                    return False
                if "$exists" in value and (key in record) is not value["$exists"]:
                    return False
                if "$gte" in value and record_value < value["$gte"]:
                    return False
                if "$lte" in value and record_value > value["$lte"]:
                    return False
                continue
            if record_value != value:
                return False
        return True



class FakeProblemInfoCollection:
    def __init__(self) -> None:
        self.find_one = AsyncMock(return_value=None)
        self.update_one = AsyncMock()
        self.count_documents = AsyncMock(return_value=0)


class FakeDatabase:
    def __init__(self) -> None:
        self.preferences = FakeCollection()
        self.problem_info = FakeProblemInfoCollection()
        self.users = FakeCollection()
        self.integration_settings = FakeCollection()
        self.reminder_jobs = FakeCollection()
        self.reminder_alerts = FakeCollection()


class FakeMotorClient:
    def __init__(self, database: FakeDatabase) -> None:
        self.leetcodeai = database


@pytest.fixture(autouse=True)
def test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("DEVTO_API_KEY", "test-devto-key")
    monkeypatch.setenv("HASHNODE_TOKEN", "test-hashnode-token")
    monkeypatch.setenv("HASHNODE_PUBLICATION_ID", "test-pub-id-123")
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
        return_value=[
            {
                "platform": "devto",
                "status": "success",
                "url": "https://dev.to/mock-post",
                "response": {"id": 123, "url": "https://dev.to/mock-post"},
            }
        ],
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
    response = Mock(name="devto_response")
    response.status_code = 201
    response.json.return_value = {"id": 123, "url": "https://dev.to/mock-post"}

    async def fake_post(*args, **kwargs):
        return response

    request_mock = mocker.patch(
        "httpx.AsyncClient.post",
        side_effect=fake_post,
    )
    return {"request": request_mock, "response": response}


@pytest.fixture
def mock_hashnode_request(mocker):
    """
    Mocks httpx.AsyncClient.post for HashnodePublisher tests.

    Default return value is a successful GraphQL response.
    Individual tests can override ``response.json.return_value`` to simulate
    GraphQL error payloads without making real network calls or needing API keys.
    """
    import httpx

    response = mocker.Mock(spec=httpx.Response)
    response.status_code = 200
    response.json.return_value = {
        "data": {
            "publishPost": {
                "post": {
                    "id": "hn-post-123",
                    "url": "https://username.hashnode.dev/leetcode-solution-two-sum",
                    "title": "LeetCode Solution: Two Sum",
                }
            }
        }
    }
    mock_post = mocker.AsyncMock(return_value=response)
    mocker.patch("httpx.AsyncClient.post", new=mock_post)
    return {"request": mock_post, "response": response}


@pytest.fixture
def responses_mock():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps
