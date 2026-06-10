from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List
import numpy as np
from redis import Redis

class ICacheService(ABC):
    """
    Interface for a singleton cache service.
    This interface defines the contract for a cache service that can be used to store and retrieve data across the application.
    I prefer using redis cache for its performance and scalability, but this interface allows for flexibility in the underlying cache implementation.
    """

    @abstractmethod
    def get(self, key: str, file_caller="") -> List[Any] | None:
        """Retrieve a value from the cache by key.
            Automatic convert to origin type when get value from cache, for example if the value is a list of tuple, it will be converted back to list of tuple instead of string.
            This is done by using ast.literal_eval to safely evaluate the string representation of the value back to its original type.
            
            Args:
                key: The key to retrieve from the cache.
                file_caller: Optional string to indicate the caller file for logging purposes.
            Returns:
                The value associated with the key in the cache, or None if the key does not exist.
        """

        pass

    @abstractmethod
    def set(
        self,
        key: str,
        value: List[tuple[np.int64, str]],
        expire: int | None = None,
        file_caller: str = "",
    ) -> Path | None:
        """Store a value in the cache with the specified key.
        Args:
        key: The primary key to store the value under in the cache.
        value: The value to store in the cache (tuple[key: np.int64, value: str]).
        expire: The expiration time for the cached value.
        file_caller: Optional string to indicate the caller file for logging purposes.
        Returns:
        The path to the metadata file created for this cache entry, or None if no metadata file was created.
        """

        pass

    @abstractmethod
    def delete(self, key: str, file_caller: str = "") -> int:
        """Remove a value from the cache by key.
        Args:
            key: The key to remove from the cache.
            file_caller: Optional string to indicate the caller file for logging purposes.
        Returns:
            The number of keys that were removed from the cache (0 or 1)."""
        pass

    @abstractmethod
    def clear(self, file_caller: str = "") -> int:
        """Clear all entries from the cache.
        Args:
            file_caller: Optional string to indicate the caller file for logging purposes.
        Returns:
            The number of keys that were removed from the cache.
        """
        pass

    @abstractmethod
    def exists(self, key: str, file_caller: str = "") -> Any:
        """Check if a key exists in the cache.
        Args:
            key: The key to check for existence in the cache.
            file_caller: Optional string to indicate the caller file for logging purposes.
        Returns:
            Return value from cache if exists, otherwise None or False
        """
        pass
