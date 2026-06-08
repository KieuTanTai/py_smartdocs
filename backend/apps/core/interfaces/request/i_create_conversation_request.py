
from dataclasses import dataclass


@dataclass
class ICreateConversationRequest:
    title: str
    provider: str
    model: str
    system_prompt: str
    document_ids: list[str]
    mode: str
