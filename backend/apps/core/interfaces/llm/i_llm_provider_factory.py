"""
LLM provider factory interface module.
Abstract interface for LLM provider selection and instantiation.
"""

from abc import ABC, abstractmethod

from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from backend.apps.core.enums.e_provider_name import EProviderName


class ILLMProviderFactory(ABC):
    """
    Abstract interface for LLM provider factory.
    Resolves and instantiates appropriate LLM clients based on provider name.
    """
    @abstractmethod
    def get_provider(self, provider: EProviderName, file_caller: str = "") -> ILLMClient:
        """
        Get LLM provider client.

        Args:
            provider: Provider name ('gemini', 'ollama', 'mistral', etc.)
            file_caller: The file that is calling this method

        Returns:
            ILLMClient implementation

        Raises:
            ValueError: If provider not found or not configured
        """
        pass
