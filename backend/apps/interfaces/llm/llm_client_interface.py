"""
LLM client interface module.
Abstract interface for language model providers.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from backend.apps.interfaces.conversation.completion_interface import CompletionInfoInterface, CompletionRequestInterface, CompletionResponseInterface


class LLMClientInterface(ABC):
    provider_name: str
    """
    Abstract interface for LLM providers.
    Provider-agnostic interface for language model completions.
    """

    @abstractmethod
    async def generate(self, request: CompletionRequestInterface) -> CompletionResponseInterface:
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
    def get_model_info(self) -> CompletionInfoInterface:
        """
        Get provider and model information.

        Returns:
            CompletionInfoInterface with provider name, model, capabilities
        """
        pass
