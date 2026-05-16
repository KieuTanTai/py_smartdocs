"""
Completion request and response interface module.
Abstract interfaces for LLM completion operations.
"""

from abc import ABC, abstractmethod


class CompletionRequestInterface(ABC):
    """
    Abstract interface for LLM completion requests.
    Standardizes request format across different LLM providers.
    """

    @abstractmethod
    def to_provider_format(self, provider_name):
        """
        Convert request to provider-specific format.

        Args:
            provider_name: Target provider name

        Returns:
            Provider-specific request object or dict
        """
        pass

    @abstractmethod
    def get_prompt(self):
        """Get the complete prompt text."""
        pass

    @abstractmethod
    def get_context(self):
        """Get retrieval context."""
        pass

    @abstractmethod
    def get_parameters(self):
        """Get generation parameters (temperature, max_tokens, etc.)."""
        pass


class CompletionResponseInterface(ABC):
    """
    Abstract interface for LLM completion responses.
    Standardizes response format across different LLM providers.
    """

    @abstractmethod
    def get_text(self):
        """
        Get generated text content.

        Returns:
            Generated text string
        """
        pass

    @abstractmethod
    def get_tokens(self):
        """
        Get token usage info.

        Returns:
            Dict with input_tokens and output_tokens
        """
        pass

    @abstractmethod
    def get_metadata(self):
        """
        Get response metadata.

        Returns:
            Dict with provider, model, latency_ms, finish_reason, etc.
        """
        pass
