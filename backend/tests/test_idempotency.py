import json
import pytest
import fakeredis
from backend.utils.redis_helper import RedisHelper
from backend.main import _make_idempotency_key

def test_redis_helper_set_and_exists(monkeypatch):
    """RedisHelper should store and retrieve values using fakeredis."""
    fake = fakeredis.FakeRedis()
    def _init(self, url=None):
        self.url = url or "redis://localhost:6379/0"
        self.client = fake
    monkeypatch.setattr("backend.utils.redis_helper.RedisHelper.__init__", _init)

    helper = RedisHelper()
    key = "test:key"
    assert not helper.exists(key)
    helper.setex(key, 10, "value")
    assert helper.exists(key)
    assert helper.get(key) == "value"

def test_idempotency_key_structure():
    """Verify the idempotency key format and deterministic digest part."""
    title = "Two Sum"
    author = "Alice"
    platforms = ["devto", "hashnode"]
    draft = False
    key = _make_idempotency_key(title, author, platforms, draft)
    parts = key.split(":")
    assert parts[0] == "idemp"
    # Digest part should be 64 hex chars (SHA256)
    assert len(parts[1]) == 64
    # UUID part should be 32 hex chars
    assert len(parts[2]) == 32
