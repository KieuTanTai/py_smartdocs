from abc import ABC, abstractmethod
from typing import Any, List
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
        value: List[tuple[str, str]],
        expire: int | None = None,
        file_caller: str = "",
    ):
        """Store a value in the cache with the specified key.
        Args:
        key: The primary key to store the value under in the cache.
        value: The value to store in the cache (tuple[key: str, value: str]).
        expire: The expiration time for the cached value.
        file_caller: Optional string to indicate the caller file for logging purposes.
        """

        pass

    @abstractmethod
    def delete(self, key: str, file_caller: str = ""):
        """Remove a value from the cache by key."""
        pass

    @abstractmethod
    def clear(self, file_caller: str = ""):
        """Clear all entries from the cache."""
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
