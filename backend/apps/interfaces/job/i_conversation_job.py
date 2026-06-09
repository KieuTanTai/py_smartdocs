
from abc import ABC, abstractmethod

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.response.i_conversation_job_response import IConversationJobResponse


class IConversationJob(ABC):
    @abstractmethod
    def documents_ready(self, conversation_id: str) -> bool:
        """Check if documents attached to conversation are indexed and ready for retrieval."""
        pass
 
    @abstractmethod
    def prepare_conversation(
        self,
        conversation_id: str,
        provider: EProviderName,
        model_name: str,
    ) -> IConversationJobResponse:
        """Prepare conversation for chat by verifying documents, building retrieval context, and generating bootstrap assistant message."""
        pass

    @abstractmethod
    def generate_bootstrap_message(
        self,
        conversation_id: str,
        provider: EProviderName,
        model_name: str,
    ) -> IConversationJobResponse:
        """Generate initial assistant message for conversation without saving to DB."""
        pass