from dataclasses import dataclass
from typing import List

from backend.apps.core.enums.e_pipeline_type import EPipelineType

@dataclass
class IMessageDTO:
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str

@dataclass
class IChatHistoryResponse:
    conversation_id: str
    conversation_title: str
    messages: List[IMessageDTO]
    count: int
    total: int

@dataclass
class ISendMessageResponse:
    conversation_id: str
    user_message_id: str
    assistant_message_id: str
    assistant_message: str
    latency_ms: int
    provider: str
    model: str
    pipeline_type: EPipelineType