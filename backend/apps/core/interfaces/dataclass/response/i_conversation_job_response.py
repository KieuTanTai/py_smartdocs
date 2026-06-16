from dataclasses import dataclass

@dataclass
class IConversationJobResponse:
    conversation_id: str
    status: str
    assistant: str
    provider: str
    model: str
    retrieval_hits: list[dict]
