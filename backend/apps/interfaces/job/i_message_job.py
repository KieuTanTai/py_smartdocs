from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.job.i_message_job import IMessageJobResponse

class IMessageJob(ABC):
    """Contract for RAG Chat Message Processing."""
    
    @abstractmethod
    def run(self, conversation_id: str, content: str, provider: EProviderName, 
            pipeline_type: EPipelineType, model_name: str, embedding_model_name: str = "gemini-embedding-2") -> IMessageJobResponse:
        pass