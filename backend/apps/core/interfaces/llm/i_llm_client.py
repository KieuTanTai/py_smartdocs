"""
LLM client interface module.
Abstract interface for language model providers.
"""

from abc import ABC, abstractmethod

from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest, IEmbeddingResponse
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.embeddings import Embedder

class ILLMClient(ABC):
    """
    Abstract interface for LLM providers.
    Provider-agnostic interface for language model completions.
    """


    @abstractmethod
    def generate(self, request: ICompletionRequest, file_caller: str = "") -> str:
        """
        Generate text completion.

        Args:
            request: CompletionRequest object with prompt, context, params
            file_caller: Optional string indicating the caller for logging purposes
        Returns:
            CompletionResponse with text, tokens, metadata
        """
        pass

    @abstractmethod
    def embedding(self, request: ICompletionRequest, file_caller: str = "") -> IEmbeddingResponse:
        """
        Generate embedding vector for given input.

        Args:
            request: CompletionRequest object with input text
            file_caller: Optional string indicating the caller for logging purposes
        Returns:
            IEmbeddingResponse object with embedding vector and dimensions
        """
        pass

    @abstractmethod
    def get_llm_model(self, model_name: str, file_caller: str = "") -> LLMInterface:
        """
        Get the underlying LLM model instance.
        
        Args:
            model_name: Name of the LLM model to retrieve
            file_caller: Optional string indicating the caller for logging purposes
        Returns:
            LLMInterface instance representing the LLM model
        """
        pass

    @abstractmethod
    def get_embedder_model(self, model: str, file_caller: str = "") -> Embedder:
        """
        Get the underlying embedding model instance.

        Args:
            model: Name of the embedding model to retrieve
            file_caller: Optional string indicating the caller for logging purposes
        Returns:
            Embedder instance representing the embedding model
        """

    @abstractmethod
    def is_available(self, model: str, file_caller: str = "") -> bool:
        """
        Check if provider is available and configured.

        Args:
            model: Name of the model to check
            file_caller: Optional string indicating the caller for logging purposes
        Returns:
            Boolean availability status
        """
        pass