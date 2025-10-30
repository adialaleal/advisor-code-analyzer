from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Optional

import redis
from redis.exceptions import RedisError


class CacheService:
    def __init__(self, redis_url: str, default_ttl_seconds: int = 3600) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._memory_cache: dict[str, tuple[datetime, Any]] = {}
        self._redis: Optional[redis.Redis] = None

        try:
            client = redis.Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            self._redis = client
        except RedisError:
            # fallback silencioso para cache in-memory
            self._redis = None

    def _cleanup_memory_cache(self) -> None:
        now = datetime.utcnow()
        expired_keys = [
            key
            for key, (expires_at, _) in self._memory_cache.items()
            if expires_at < now
        ]
        for key in expired_keys:
            self._memory_cache.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        if self._redis:
            try:
                payload = self._redis.get(key)
                if payload is None:
                    return None
                return json.loads(payload)
            except RedisError:
                pass

        self._cleanup_memory_cache()
        payload = self._memory_cache.get(key)
        if not payload:
            return None
        _, value = payload
        return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds or self.default_ttl_seconds
        if self._redis:
            try:
                self._redis.setex(key, ttl, json.dumps(value))
                return
            except RedisError:
                pass

        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        self._memory_cache[key] = (expires_at, value)

    def is_available(self) -> bool:
        if not self._redis:
            return False
        try:
            return bool(self._redis.ping())
        except RedisError:
            return False
