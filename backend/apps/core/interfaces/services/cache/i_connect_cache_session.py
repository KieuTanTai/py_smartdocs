
from abc import ABC, abstractmethod

from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService


class IConnectCacheSession(ABC):
    """
    Interface for connecting to cache session.
    This interface defines the contract for connecting to a cache session, which can be implemented by different cache providers (e.g., Redis, Memcached).
    It provides a method to establish a connection to the cache session and return a session object that can be used for cache operations.
    """

    @abstractmethod
    def connect(self, file_caller="") -> ICacheService:
        """
        Connect to the cache session and return a session object.
        This method should be implemented by concrete classes to establish a connection to the cache session and return an appropriate session object for performing cache operations.
        """
        raise NotImplementedError("Connect method must be implemented by subclasses")
    
    @abstractmethod
    def disconnect(self, file_caller=""):
        """
        Disconnect from the cache session.
        This method should be implemented by concrete classes to disconnect from the cache session.
        """
        raise NotImplementedError("Disconnect method must be implemented by subclasses")