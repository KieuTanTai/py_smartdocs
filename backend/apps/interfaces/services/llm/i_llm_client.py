"""
LLM client interface module.
Abstract interface for language model providers.
"""

from abc import ABC, abstractmethod

from backend.apps.interfaces.services.conversation.i_completion import (
    ICompletionInfo,
    ICompletionRequest,
    ICompletionResponse,
)


class ILLMClient(ABC):
    """
    Abstract interface for LLM providers.
    Provider-agnostic interface for language model completions.
    """

    @abstractmethod
    async def generate(self, request: ICompletionRequest) -> ICompletionResponse:
        """
        Generate text completion.

        Args:
            request: CompletionRequest object with prompt, context, params

        Returns:
            CompletionResponse with text, tokens, metadata
        """
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if provider is available and configured.

        Returns:
            Boolean availability status
        """
        pass

    @abstractmethod
    def get_model_info(self) -> ICompletionInfo:
        """
        Get provider and model information.

        Returns:
            ICompletionInfo with provider name, model, capabilities
        """
        pass
