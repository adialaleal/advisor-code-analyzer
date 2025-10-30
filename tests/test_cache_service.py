from datetime import datetime, timedelta

import pytest
import redis
from redis.exceptions import RedisError

from app.services.cache_service import CacheService


def test_memory_cache_used_when_redis_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args, **kwargs):  # noqa: ANN001, D401
        raise RedisError("unavailable")

    monkeypatch.setattr(redis.Redis, "from_url", classmethod(_raise))

    cache = CacheService("redis://example:6379/0", default_ttl_seconds=60)

    cache.set("key", {"value": 1})
    assert cache.get("key") == {"value": 1}


def test_memory_cache_expiration(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*args, **kwargs):  # noqa: ANN001, D401
        raise RedisError("unavailable")

    monkeypatch.setattr(redis.Redis, "from_url", classmethod(_raise))

    cache = CacheService("redis://example:6379/0", default_ttl_seconds=1)
    cache.set("key", {"value": 1})

    # Force the entry to expire by manipulating the internal store
    _, value = cache._memory_cache["key"]  # type: ignore[attr-defined]
    cache._memory_cache["key"] = (datetime.utcnow() - timedelta(seconds=5), value)  # type: ignore[attr-defined]

    assert cache.get("key") is None

