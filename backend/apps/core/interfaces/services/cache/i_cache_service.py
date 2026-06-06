
from abc import ABC
from typing import Any
from redis import Redis

class ICacheService(ABC):
    """
    Interface for a singleton cache service.
    This interface defines the contract for a cache service that can be used to store and retrieve data across the application.
    I prefer using redis cache for its performance and scalability, but this interface allows for flexibility in the underlying cache implementation.
    """

    def get(self, key: str, file_caller="") -> Any:
        """Retrieve a value from the cache by key.
        Args:
            key: The key to retrieve from the cache.
            file_caller: Optional string to indicate the caller file for logging purposes.
        Returns:
            The value associated with the key in the cache, or None if the key does not exist.
        """
        pass

    def set(self, key: str, value: Any, expire = None, file_caller=""):
        """Store a value in the cache with the specified key."""
        pass

    def delete(self, key: str, file_caller=""):
        """Remove a value from the cache by key."""
        pass

    def clear(self, file_caller=""):
        """Clear all entries from the cache."""
        pass

    def exists(self, key: str, file_caller="") -> Any:
        """Check if a key exists in the cache.
        Args:
            key: The key to check for existence in the cache.
            file_caller: Optional string to indicate the caller file for logging purposes.
        Returns:
            Return value from cache if exists, otherwise None or False
        """
        pass