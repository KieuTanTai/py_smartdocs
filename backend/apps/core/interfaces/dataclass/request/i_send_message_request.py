from dataclasses import dataclass
from typing import Optional


@dataclass
class ISendMessageRequest:
    conversation_id: str
    message: str
    provider: Optional[str] = None
    model: Optional[str] = None