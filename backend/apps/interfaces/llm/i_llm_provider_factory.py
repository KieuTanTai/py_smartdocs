"""
LLM provider factory interface module.
Abstract interface for LLM provider selection and instantiation.
"""

from abc import ABC, abstractmethod

from backend.apps.interfaces.llm.i_llm_client import ILLMClient


class ILLMProviderFactory(ABC):
    """
    Abstract interface for LLM provider factory.
    Resolves and instantiates appropriate LLM clients based on provider name.
    """

    @abstractmethod
    def get_provider(self) -> ILLMClient:
        """
        Get LLM provider client.

        Args:
            provider_name: Provider name ('gemini', 'ollama', 'mistral', etc.)

        Returns:
            ILLMClient implementation

        Raises:
            ValueError: If provider not found or not configured
        """
        pass
