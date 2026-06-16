
from abc import ABC


class IVectorDBService(ABC):
    """Interface for a vector database service.
        This is middle layer interface for vector database operations, it defines the contract for a vector database service that can be used to perform operations such as upsert, search, and delete on a vector database.
        The interface abstracts away the underlying implementation details of the vector database, allowing for flexibility in choosing different vector database backends (e.g., Faiss, Pinecone, Weaviate) without affecting the rest of the application.
        By defining this interface, we can ensure that any vector database service implementation adheres to a consistent set of operations, making it easier to integrate and switch between different
    """
    pass