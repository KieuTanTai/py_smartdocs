from dataclasses import dataclass, field
from typing import Any, List

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
    provider: str
    model: str
    pipeline_type: EPipelineType
    retrieval_hits: List[Any] = field(default_factory=list)
    time_counter: IChatTimeCounter = field(default_factory=lambda: IChatTimeCounter(0.0, 0.0, 0.0))

@dataclass
class IChatTimeCounter:
    embedding_time: float
    retrieval_time: float
    llm_time: float
    save_time: float = 0.0
    total_time: float = 0.0
