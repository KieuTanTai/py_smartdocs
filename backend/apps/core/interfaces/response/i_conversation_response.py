from dataclasses import dataclass
from typing import Any

@dataclass
class IConversationResponse:
    id: str
    title: str
    provider: str
    model: str
    system_prompt: str
    mode: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> IConversationResponse:
        data = payload.get("data", payload)

        return cls(
            id=str(
                data.get("id")
                or data.get("conversation_id")
                or data.get("uuid")
                or ""
            ),
            title=data.get("title", ""),
            provider=data.get("provider", ""),
            model=data.get("model", ""),
            system_prompt=data.get("system_prompt", ""),
            mode=data.get("mode", ""),
        )
