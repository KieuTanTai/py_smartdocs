from abc import ABC, abstractmethod
from typing import Any

import faiss

class IFaissMemoryPool(ABC):
    @abstractmethod
    def add_to_pool(
        self,
        conversation_id: str,
        index: faiss.IndexFlatL2 | faiss.IndexIDMap,
        file_caller: str = "",
    ) -> dict[str, faiss.IndexFlatL2 | faiss.IndexIDMap | Any]:
        """
        Adds a document to the Faiss memory pool.
        Args:
            conversation_id (str): The unique identifier of the conversation.
            index (faiss.IndexFlatL2 | faiss.IndexIDMap): The Faiss index to be added to the pool.
            file_caller (str): The file name of the caller (for logging purposes).
        Returns:
            dict[str, faiss.IndexFlatL2 | faiss.IndexIDMap | Any]: A dictionary containing the result of the operation.
        """
        pass

    @abstractmethod
    def get_from_pool(self, conversation_id: str, file_caller: str = "") -> faiss.IndexFlatL2 | faiss.IndexIDMap | None:
        """
        Retrieves documents from the Faiss memory pool based on the conversation ID.
        Args:
            conversation_id (str): The unique identifier of the conversation for which to retrieve documents.
            file_caller (str): The file name of the caller (for logging purposes).
        Returns:
            faiss.IndexFlatL2 | faiss.IndexIDMap: The Faiss index associated with the given conversation ID.
        """
        pass

    @abstractmethod
    def remove_from_pool(self, conversation_id: str, file_caller: str = "") -> bool:
        """
        Removes a document from the Faiss memory pool based on the conversation ID.
        Args:
            conversation_id (str): The unique identifier of the conversation for which to remove documents.
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