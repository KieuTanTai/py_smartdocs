from dataclasses import dataclass

@dataclass
class BootstrapMessageResponse:
    conversation_id: str
    assistant_message: str
    provider: str
    model: str