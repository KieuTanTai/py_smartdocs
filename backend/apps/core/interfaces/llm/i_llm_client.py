"""
LLM client interface module.
Abstract interface for language model providers.
"""

from abc import ABC, abstractmethod

from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest, IEmbeddingResponse

class ILLMClient(ABC):
    """
    Abstract interface for LLM providers.
    Provider-agnostic interface for language model completions.
    """


    @abstractmethod
    def generate(self, request: ICompletionRequest) -> str:
        """
        Generate text completion.

        Args:
            request: CompletionRequest object with prompt, context, params

        Returns:
            CompletionResponse with text, tokens, metadata
        """
        pass

    @abstractmethod
    def embedding(self, request: ICompletionRequest) -> IEmbeddingResponse:
        """
        Generate embedding vector for given input.

        Args:
            request: CompletionRequest object with input text
        Returns:
            IEmbeddingResponse object with embedding vector and dimensions
        """
        pass

    @abstractmethod
    def is_available(self, model: str) -> bool:
        """
        Check if provider is available and configured.

        Returns:
            Boolean availability status
        """
        pass