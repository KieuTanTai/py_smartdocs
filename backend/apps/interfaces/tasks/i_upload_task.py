from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, List

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.tasks.i_embed_and_save_response import IEmbedResponse, IGraphRagUploadResponse, IUploadResponse

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

    # @abstractmethod
    # def run(self, document_id: str, provider_name: EProviderName, file_caller:str = "") -> IEmbedResponse:
    #     """
    #     Executes document RAG pipeline via UploadJob.
    #     Must return a JSON-serializable dictionary.
    #     Args:
    #         document_id: ID of the Document to process
    #         provider_name: Name of the LLM provider to use for embedding
    #         file_caller: Name of the file caller (for logging purposes)
    #     Returns:
    #         A dictionary containing embedding results and metadata
    #     Raises:
    #         ValueError: If provider_name is invalid or document is not found
    #         Exception: For any other processing errors
    #     """
    #     pass

    @abstractmethod
    def run_with_paths(self, file_paths: list[Path], provider_name: EProviderName, file_caller:str = "") -> IUploadResponse:
        """
        Executes document RAG pipeline via UploadJob.
        Must return a JSON-serializable dictionary.
        Args:
            file_paths: List of file paths to process
            provider_name: Name of the LLM provider to use for embedding
            file_caller: Name of the file caller (for logging purposes)
        Returns:
            A dictionary containing embedding results and metadata
        Raises:
            ValueError: If provider_name is invalid or document is not found
            Exception: For any other processing errors
        """
        pass

    @abstractmethod
    def run_graph_pipeline_with_paths(self, file_paths: list[Path], provider_name: EProviderName, embed_model_name: str, model_name: str, file_caller:str = "") -> List[IGraphRagUploadResponse]:
        """
        Executes document RAG pipeline with graph retriever via UploadJob.
        Must return a JSON-serializable dictionary.
        Args:
            file_paths: List of file paths to process
            provider_name: Name of the LLM provider to use for embedding
            embed_model_name: Name of the embedding model to use for creating graph retriever
            model_name: Name of the LLM model to use for creating graph retriever
            file_caller: Name of the file caller (for logging purposes)
        Returns:
            A list of graph retriever responses containing retriever instances and metadata
        Raises:
            ValueError: If provider_name is invalid or document is not found
            Exception: For any other processing errors
        """
        pass