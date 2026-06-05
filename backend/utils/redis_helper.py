import os
import redis
import hashlib

class RedisHelper:
    """Thin wrapper around redis-py for idempotency storage."""
    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.client = redis.StrictRedis.from_url(self.url, decode_responses=True)
            # test connection
            self.client.ping()
        except Exception:
            # Fallback to in‑memory fakeredis for testing / when Redis is unavailable
            try:
                import fakeredis
                self.client = fakeredis.FakeRedis(decode_responses=True)
            except ImportError:
                raise RuntimeError("Redis server not reachable and fakeredis not installed")


    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.client.setex(key, ttl, value)

    def get(self, key: str) -> str | None:
        value = self.client.get(key)
        if isinstance(value, bytes):
            return value.decode()
        return value




def _make_idempotency_key(title, author, platforms, draft):
    """Generate deterministic idempotency key.
    Returns a string of the form "idemp:{digest}:{uuid_part}".
    """
    base = f"{title}|{author}|{sorted(platforms) or []}|{draft}"
    digest = hashlib.sha256(base.encode()).hexdigest()
    uuid_part = hashlib.sha256(base.encode()).hexdigest()[:32]
    return f"idemp:{digest}:{uuid_part}"
