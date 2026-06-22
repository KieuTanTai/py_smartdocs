from abc import ABC, abstractmethod
from typing import Any, Dict

from celery import Task

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.job.i_message_job import IMessageJobResponse

class IMessageTask(ABC, Task):
    """Contract for Celery Chat Message RAG Inference Task."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def run(self, conversation_id: str, content: str, provider_name: EProviderName, pipeline_type: EPipelineType, model_name: str) -> IMessageJobResponse:
        """
        Executes async RAG inference.
        Must return a JSON-serializable dictionary (Serialized MessageResponse).
        """
        pass