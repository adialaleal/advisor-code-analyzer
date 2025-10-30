from __future__ import annotations

from typing import Any, Optional

from app.interfaces.cache import ICacheService
from app.services.cache.backends import ICacheBackend, MemoryCacheBackend, RedisCacheBackend


class CacheService:
    """Cache service with fallback support between backends."""

    def __init__(
        self, redis_url: str, default_ttl_seconds: int = 3600, *, primary_backend: Optional[ICacheBackend] = None, fallback_backend: Optional[ICacheBackend] = None
    ) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        
        # Initialize backends if not provided (for backward compatibility)
        self._primary: ICacheBackend = primary_backend or RedisCacheBackend(redis_url, default_ttl_seconds)
        self._fallback: ICacheBackend = fallback_backend or MemoryCacheBackend(default_ttl_seconds)

    def get(self, key: str) -> Optional[Any]:
        # Try primary backend first
        value = self._primary.get(key)
        if value is not None:
            return value
        
        # Fallback to memory cache
        return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        # Set in both backends for redundancy
        self._primary.set(key, value, ttl_seconds)
        self._fallback.set(key, value, ttl_seconds)

    def is_available(self) -> bool:
        """Returns True if at least one backend is available."""
        return self._primary.is_available() or self._fallback.is_available()
