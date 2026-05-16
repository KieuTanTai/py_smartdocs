"""
LLM client interface module.
Abstract interface for language model providers.
"""

from abc import ABC, abstractmethod


class LLMClientInterface(ABC):
    """
    Abstract interface for LLM providers.
    Provider-agnostic interface for language model completions.
    """

    @abstractmethod
    async def generate(self, completion_request):
        """
        Generate text completion.

        Args:
            completion_request: CompletionRequest object with prompt, context, params

        Returns:
            CompletionResponse with text, tokens, metadata
        """
        pass

    @abstractmethod
    def is_available(self):
        """
        Check if provider is available and configured.

        Returns:
            Boolean availability status
        """
        pass

    @abstractmethod
    def get_model_info(self):
        """
        Get provider and model information.

        Returns:
            Dict with provider name, model, capabilities
        """
        pass
