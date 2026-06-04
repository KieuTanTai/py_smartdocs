from dataclasses import dataclass

from backend.apps.core.interfaces.system.i_provider import IProvider

@dataclass
class ChatRequest:
    conversation_id: str
    provider: IProvider
    messages: str