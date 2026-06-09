from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.job.i_dataclass_message_job import MessageResponse

class IMessageJob(ABC):
    """Contract for RAG Chat Message Processing."""
    
    @abstractmethod
    def run(self, conversation_id: str, content: str, provider: EProviderName, model_name: str | None = None) -> MessageResponse:
        pass