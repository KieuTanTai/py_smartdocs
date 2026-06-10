from dataclasses import dataclass

@dataclass
class IConversationJobResponse:
    conversation_id: str
    assistant_message: str
    provider: str
    model: str