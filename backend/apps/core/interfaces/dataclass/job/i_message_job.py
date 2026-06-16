from dataclasses import dataclass, field
from typing import List

@dataclass
class IMessageJobContextHit:
    text: str
    score: float
    source_document_id: str | None = None

@dataclass
class IMessageJobResponse:
    conversation_id: str
    assistant: str
    provider: str
    model: str
    latency_ms: int
    retrieval_hits: List[IMessageJobContextHit] = field(default_factory=list)