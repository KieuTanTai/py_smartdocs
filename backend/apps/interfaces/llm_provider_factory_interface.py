"""
LLM provider factory interface module.
Abstract interface for LLM provider selection and instantiation.
"""

from abc import ABC, abstractmethod


class LLMProviderFactoryInterface(ABC):
    """
    Abstract interface for LLM provider factory.
    Resolves and instantiates appropriate LLM clients based on provider name.
    """

    @abstractmethod
    def get_provider(self, provider_name):
        """
        Get LLM provider client.

        Args:
            provider_name: Provider name ('gemini', 'ollama', 'mistral', etc.)

        Returns:
            LLMClientInterface implementation

        Raises:
            ValueError: If provider not found or not configured
        """
        pass

    @abstractmethod
    def is_provider_available(self, provider_name):
        """
        Check if provider is available and configured.

        Args:
            provider_name: Provider name

        Returns:
            Boolean availability status
        """
        pass

    @abstractmethod
    def get_available_providers(self):
        """
        Get list of available providers.

        Returns:
            List of provider names that are configured and available
        """
        pass
