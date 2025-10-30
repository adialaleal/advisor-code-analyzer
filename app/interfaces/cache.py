"""Interface for cache services."""

from typing import Any, Optional
from typing_extensions import Protocol


class ICacheService(Protocol):
    """Protocol defining the contract for cache services."""

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from cache by key.

        Args:
            key: The cache key to retrieve

        Returns:
            The cached value if found, None otherwise
        """
        ...

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Store a value in cache.

        Args:
            key: The cache key
            value: The value to cache
            ttl_seconds: Optional time-to-live in seconds
        """
        ...

    def is_available(self) -> bool:
        """
        Check if the cache service is available.

        Returns:
            True if the service is available, False otherwise
        """
        ...

