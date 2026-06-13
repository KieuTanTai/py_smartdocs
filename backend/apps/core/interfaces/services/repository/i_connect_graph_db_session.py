from abc import ABC, abstractmethod

from backend.apps.core.interfaces.services.repository.i_connect_session import IConnectSession

class IConnectGraphDBSession(IConnectSession, ABC):
    """
    Base Interface for connecting to graph database session.
    This interface defines the contract for connecting to a graph database session, which can be implemented by different graph database providers (e.g., Neo4j).
    It provides a method to establish a connection to the graph database session and return a session object that can be used for graph database operations.
    """