# interfaces/chat_message.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IChatMessage:
    role: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)
    assistant: bool = False
    ts: float = 0
