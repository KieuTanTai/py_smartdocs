from abc import ABC, abstractmethod
from typing import Any, Dict

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.tasks.i_embed_and_save_response import IEmbedAndSaveResponse

class IUploadTask(ABC):
    """Contract for Celery Upload Processing Task."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Celery Task routing name
        Returns:
            A string representing the Celery Task name for routing
        """
        pass

    @abstractmethod
    def run(self, document_id: str, provider_name: EProviderName, file_caller:str = "") -> IEmbedAndSaveResponse:
        """
        Executes document RAG pipeline via UploadJob.
        Must return a JSON-serializable dictionary.
        Args:
            document_id: ID of the Document to process
            provider_name: Name of the LLM provider to use for embedding
            file_caller: Name of the file caller (for logging purposes)
        Returns:
            A dictionary containing embedding results and metadata
        Raises:
            ValueError: If provider_name is invalid or document is not found
            Exception: For any other processing errors
        """
        pass
