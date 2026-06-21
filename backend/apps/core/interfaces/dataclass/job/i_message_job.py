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
    provider: str
    model: str
    latency_ms: int
    mode: str
    retrieval_hits: list[IMessageJobContextHit] = field(default_factory=list)