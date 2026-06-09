from dataclasses import dataclass, field
from typing import List

@dataclass
class ContextHit:
    text: str
    score: float
    source_document_id: str | None = None

@dataclass
class MessageResponse:
    conversation_id: str
    assistant: str
    provider: str
    model: str
    latency_ms: int
    retrieval_hits: List[ContextHit] = field(default_factory=list)