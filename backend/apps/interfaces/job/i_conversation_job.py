from abc import ABC, abstractmethod
from dataclasses import dataclass
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.job.i_conversation_job import IConversationJobResponse

class IConversationJob(ABC):
    """Contract for Conversation Preparation Processing."""
    
    @abstractmethod
    def check_documents_ready(self, conversation_id: str) -> bool:
        """Checks if all documents attached to the conversation are ready (e.g., indexed) for processing.
        Args:
            conversation_key (str): The key of the conversation to check.
        Returns:
            bool: True if all documents are ready, False otherwise.
        """
        pass

    @abstractmethod
    def generate_bootstrap_message(self, conversation_id: str, provider: EProviderName, model_name: str | None = None) -> IConversationJobResponse:
        """
        Generates the initial assistant message for a conversation based on the attached documents and the specified LLM provider/model.
        Args:
            conversation_key (str): The key of the conversation for which to generate the bootstrap message.
            provider (EProviderName): The LLM provider to use for generating the message.
            model_name (str): The specific model name to use for generation.
            prompt (str): The prompt to use for generating the bootstrap message.
        Returns:
            IConversationJobResponse: The response containing the generated bootstrap message and related metadata.
        """
        pass