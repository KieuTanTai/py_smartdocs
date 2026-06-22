from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from celery import Task

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IconversationDocumentGetResponse
from backend.apps.core.interfaces.dataclass.tasks.i_upload_response import IEmbedResponse, IGraphRagUploadResponse, IUploadResponse
from backend.apps.services.chat.models import ConversationModel

class IUploadTask(ABC, Task):
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
    def load_document(self, conversation_id: str, file_caller: str = "") -> IconversationDocumentGetResponse:
        """
        Load document for a given conversation.
        Args:
            conversation_id: Unique identifier for the conversation
            file_caller: Name of the file caller (for logging purposes)
        Returns:
            An IconversationDocumentGetResponse containing document URL, associated files, and optional vector DB load response
        Raises:
            ValueError: If conversation_id is invalid or document is not found
            Exception: For any other loading errors
        """
        pass

    @abstractmethod
    def run_with_paths(self, conversation_id: str, file_paths: list[Path], provider_name: EProviderName, model_name: str, file_caller:str = "") -> IUploadResponse:
        """
        Executes document RAG pipeline via UploadJob.
        Must return a JSON-serializable dictionary.
        Args:
            conversation_id: The ID of the conversation associated with the upload
            file_paths: List of file paths to process
            provider_name: Name of the LLM provider to use for embedding
            model_name: Name of the model to use for embedding
            file_caller: Name of the file caller (for logging purposes)
        Returns:
            A dictionary containing embedding results and metadata
        Raises:
            ValueError: If provider_name is invalid or document is not found
            Exception: For any other processing errors
        """
        pass

    @abstractmethod
    async def run_graph_pipeline_with_paths(self, conversation_id: str, file_paths: list[Path], provider_name: EProviderName, embed_model_name: str, model_name: str, file_caller:str = "") -> IGraphRagUploadResponse:
        """
        Executes document RAG pipeline with graph retriever via UploadJob.
        Must return a JSON-serializable dictionary.
        Args:
            conversation_id: The ID of the conversation associated with the upload
            file_paths: List of file paths to process
            provider_name: Name of the LLM provider to use for embedding
            embed_model_name: Name of the embedding model to use for creating graph retriever
            model_name: Name of the LLM model to use for creating graph retriever
            file_caller: Name of the file caller (for logging purposes)
        Returns:
            A dictionary containing graph retriever results and metadata
        Raises:
            ValueError: If provider_name is invalid or document is not found
            Exception: For any other processing errors
        """
        pass