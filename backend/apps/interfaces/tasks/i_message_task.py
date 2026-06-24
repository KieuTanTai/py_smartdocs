from abc import ABC, abstractmethod
from typing import Any, Dict

from celery import Task

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.application.i_message_response import IChatHistoryResponse
from backend.apps.core.interfaces.dataclass.job.i_message_job import IMessageJobResponse

class IMessageTask(ABC, Task):
    """Contract for Celery Chat Message RAG Inference Task."""

    @abstractmethod
    def run(self, conversation_id: str, content: str, provider_name: EProviderName, pipeline_type: EPipelineType, model_name: str) -> IMessageJobResponse:
        """
        Executes async RAG inference.
        Must return a JSON-serializable dictionary (Serialized MessageResponse).
        """
        pass
    
    @abstractmethod
    def get_history(self, conversation_id: str, limit: int = 50, offset: int = 0) -> IChatHistoryResponse:
        """Lấy lịch sử chat"""
        pass