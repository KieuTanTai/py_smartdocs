from abc import ABC, abstractmethod
from dataclasses import dataclass
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.job.i_dataclass_conversation_job import BootstrapMessageResponse

class IConversationJob(ABC):
    """Contract for Conversation Preparation Processing."""
    
    @abstractmethod
    def check_documents_ready(self, conversation_id: str) -> bool:
        pass

    @abstractmethod
    def generate_bootstrap_message(self, conversation_id: str, provider: EProviderName, model_name: str | None = None) -> BootstrapMessageResponse:
        pass