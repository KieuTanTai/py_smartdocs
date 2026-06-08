from dataclasses import dataclass
from typing import Any, Optional

from backend.apps.core.interfaces.request.i_chat_metrics import IChatMetrics


@dataclass
class IChatResponse:
    assistant: str
    conversation_id: str
    metrics: IChatMetrics
    new_conversation: bool
    error: Optional[str]
    used_mock: bool

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, Any],
        conversation_id: str,
        new_conversation: bool = False,
    ) -> "IChatResponse":

        data = payload.get("data", payload)

        assistant = ""

        for key in (
            "assistant",
            "message",
            "content",
            "answer",
            "text",
        ):
            value = data.get(key)
            if value:
                assistant = str(value)
                break

        metrics_data = data.get("metrics", {})

        metrics = IChatMetrics(
            provider=metrics_data.get("provider", ""),
            model=metrics_data.get("model", ""),
            mode=metrics_data.get("mode", ""),
            total_ms=metrics_data.get("total_ms", 0),
        )

        return cls(
            assistant=assistant,
            conversation_id=conversation_id,
            metrics=metrics,
            new_conversation=new_conversation,
            error=None,
            used_mock=False,
        )
