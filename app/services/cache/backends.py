"""Cache backend implementations."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import redis
from redis.exceptions import RedisError

from app.interfaces.cache import ICacheService


class ICacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache."""
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store a value in cache."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available."""
        ...


class RedisCacheBackend(ICacheBackend):
    """Redis-based cache backend."""

    def __init__(self, redis_url: str, default_ttl_seconds: int = 3600) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._redis: Optional[redis.Redis] = None

        try:
            client = redis.Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            self._redis = client
        except RedisError:
            self._redis = None

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis."""
        if not self._redis:
            return None
        try:
            payload = self._redis.get(key)
            if payload is None:
                return None
            return json.loads(payload)
        except RedisError:
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value in Redis."""
        if not self._redis:
            return
        ttl = ttl_seconds or self.default_ttl_seconds
        try:
            self._redis.setex(key, ttl, json.dumps(value))
        except RedisError:
            pass

    def is_available(self) -> bool:
        """Check if Redis is available."""
        if not self._redis:
            return False
        try:
            return bool(self._redis.ping())
        except RedisError:
            return False


class MemoryCacheBackend(ICacheBackend):
    """In-memory cache backend with expiration."""

    def __init__(self, default_ttl_seconds: int = 3600) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._store: dict[str, tuple[datetime, Any]] = {}

    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, (expires_at, _) in self._store.items() if expires_at < now
        ]
        for key in expired_keys:
            self._store.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from memory cache."""
        self._cleanup_expired()
        payload = self._store.get(key)
        if not payload:
            return None
        _, value = payload
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value in memory cache."""
        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        self._store[key] = (expires_at, value)

    def is_available(self) -> bool:
        """Memory cache is always available."""
        return True

