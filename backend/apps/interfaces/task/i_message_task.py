from abc import ABC, abstractmethod
from typing import Any, Dict

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.job.i_message_job import IMessageJobResponse

class IMessageTask(ABC):
    """Contract for Celery Chat Message RAG Inference Task."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, conversation_id: str, content: str, provider_name: EProviderName, model_name: str | None = None) -> IMessageJobResponse:
        """
        Executes async RAG inference.
        Must return a JSON-serializable dictionary (Serialized MessageResponse).
        """
        pass