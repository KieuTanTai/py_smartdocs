from abc import ABC, abstractmethod
from typing import Any, Dict

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.job.i_conversation_job import IConversationJobResponse

class IConversationTask(ABC):
    """Contract for Celery Conversation Preparation Task."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, conversation_id: str, provider_name: EProviderName, model_name: str | None = None, file_caller: str = "") -> IConversationJobResponse:
        """
        Executes conversation bootstrap flow.
        Must return a JSON-serializable dictionary (Serialized BootstrapMessageResponse).
        Args:
            conversation_id (str): The ID of the conversation to prepare.
            provider_name (EProviderName): The LLM provider to use for generating the bootstrap message.
            model_name (str | None): Optional specific model name to use for generation. If None, a default model will be used based on the provider.
            file_caller (str): The file that called this method, for logging purposes.
        Returns:
            IConversationJobResponse: The response containing the generated bootstrap message and related metadata.
        """
        pass