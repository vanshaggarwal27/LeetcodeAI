import os
import redis

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
        return self.client.get(key)
