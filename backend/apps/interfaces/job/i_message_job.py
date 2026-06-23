from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Tuple

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.application.i_message_response import IMessageDTO
from backend.apps.core.interfaces.dataclass.job.i_message_job import IMessageJobContextHit, IMessageJobResponse
from backend.apps.services.chat.models import ConversationModel, MessageModel

class IMessageJob(ABC):
    """Contract for RAG Chat Message Processing."""
    
    @abstractmethod
    def get_conversation(self, conversation_id: str) -> ConversationModel:
        """Step 1: Lấy thông tin phòng chat"""
        pass

    @abstractmethod
    def save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        """Step 2 & Step 5: Lưu tin nhắn"""
        pass

    @abstractmethod
    def build_prompt_and_retrieve(self, content: str, conversation: ConversationModel, provider: EProviderName, pipeline_type: EPipelineType, model_name: str, embedding_model_name: str = "gemini-embedding-2") -> Tuple[str, list[IMessageJobContextHit]]:
        """Step 3: Lấy ngữ cảnh và Build Prompt"""
        pass

    @abstractmethod
    def generate_answer(self, provider: EProviderName, model_name: str, prompt: str) -> str:
        """Step 4: Gọi AI sinh câu trả lời"""
        pass
    
    @abstractmethod
    def get_conversation_title(self, conversation_id: str) -> str:
        """Trả về conversation_title"""
        pass
    
    @abstractmethod
    def get_messages(self, conversation_id: str, limit: int, offset: int) ->list[IMessageDTO]:
        """Lấy danh sách tin nhắn có phân trang"""
        pass
    
    @abstractmethod
    def count_messages(self, conversation_id: str) -> int:
        """Đếm tổng số tin nhắn"""
        pass