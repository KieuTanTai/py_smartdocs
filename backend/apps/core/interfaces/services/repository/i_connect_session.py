from abc import ABC, abstractmethod

class IConnectSession(ABC):
    """
    Base Interface for connecting to session.
    This interface defines the contract for connecting to a cache session, which can be implemented by different cache providers (e.g., Redis, Memcached).
    It provides a method to establish a connection to the cache session and return a session object that can be used for cache operations.
    """

    #* NOTE: change return type to a more specific session type if needed, e.g., RedisSession, MemcachedSession, etc.   
    @abstractmethod
    def connect(self, file_caller="") -> object:
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
