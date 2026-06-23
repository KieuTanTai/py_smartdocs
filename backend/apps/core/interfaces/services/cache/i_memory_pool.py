from abc import ABC, abstractmethod
from typing import Any
import uuid

from anyio import Path
import faiss

class IMemoryPool(ABC):
    """
    Contract for Faiss Memory Pool Service.
    This service manages the in-memory storage of Faiss indices for active conversations, allowing for efficient retrieval and management of indices during the conversation lifecycle.
    Key is type Any to allow flexibility in using either conversation_id (str) or faiss_file_id (uuid.UUID) as the key for indexing the Faiss indices in the memory pool.
    """
    @abstractmethod
    def add_to_pool(
        self,
        key: Any,
        index: faiss.IndexFlatL2 | faiss.IndexIDMap,
        file_caller: str = "",
    ) -> dict[str, faiss.IndexFlatL2 | faiss.IndexIDMap | Any]:
        """
        Adds a document to the Faiss memory pool.
        Args:
            key (Any): The unique identifier of the conversation.
            index (faiss.IndexFlatL2 | faiss.IndexIDMap): The Faiss index to be added to the pool.
            file_caller (str): The file name of the caller (for logging purposes).
        Returns:
            dict[str, faiss.IndexFlatL2 | faiss.IndexIDMap | Any]: A dictionary containing the result of the operation.
        """
        pass

    @abstractmethod
    def get_from_pool(self, key: Any, file_caller: str = "") -> faiss.IndexFlatL2 | faiss.IndexIDMap | None:
        """
        Retrieves documents from the Faiss memory pool based on the conversation ID.
        Args:
            key (Any): The unique identifier of the conversation for which to retrieve documents.
            file_caller (str): The file name of the caller (for logging purposes).
        Returns:
            faiss.IndexFlatL2 | faiss.IndexIDMap: The Faiss index associated with the given conversation ID.
        """
        pass

    @abstractmethod
    def remove_from_pool(self, key: Any, file_caller: str = "") -> bool:
        """
        Removes a document from the Faiss memory pool based on the conversation ID.
        Args:
            key (Any): The unique identifier of the conversation for which to remove documents.
            file_caller (str): The file name of the caller (for logging purposes).
        Returns:
            bool: True if the document was successfully removed, False otherwise.
        """
        pass

    @abstractmethod
    def clear_pool(self, file_caller: str = "") -> int:
        """
        Clears all documents from the Faiss memory pool.
        Args:
            file_caller (str): The file name of the caller (for logging purposes).
        Returns:
            int: The number of documents that were cleared.
        """
        pass
