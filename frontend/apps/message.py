from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.apps.core.interfaces.request.i_chat_message import IChatMessage
from backend.apps.core.interfaces.request.i_chat_metrics import IChatMetrics
from backend.apps.core.interfaces.response.i_chat_response import IChatResponse
from sys_services.api_client import ApiClient, ApiError


# ? These functions are designed to be called by the frontend to send messages and handle responses in a consistent way, including error handling and fallback behavior.
def build_message(
    role: str, content: str, meta: Optional[dict] = None
) -> IChatMessage:
    return IChatMessage(role=role, content=content, meta=meta or {})

#! NOTE RECOMMEND USE THAT WHEN HAVE DATACLASS FOR RESPONSE, DONT USE dict[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
# def _extract_id(payload: Dict[str, Any]) -> Optional[str]:
#     for key in ("id", "conversation_id", "uuid"):
#         if key in payload:
#             return str(payload[key])
#     data = payload.get("data", {})
#     if isinstance(data, dict):
#         for key in ("id", "conversation_id", "uuid"):
#             if key in data:
#                 return str(data[key])
#     return None

#! NOTE RECOMMEND USE THAT WHEN HAVE DATACLASS FOR RESPONSE, DONT USE dict[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
# def _extract_text(payload: Dict[str, Any]) -> str:
#     for key in ("message", "content", "answer", "text", "assistant"):
#         if key in payload and payload[key]:
#             return str(payload[key])
#     data = payload.get("data", {})
#     if isinstance(data, dict):
#         for key in ("message", "content", "answer", "text", "assistant"):
#             if key in data and data[key]:
#                 return str(data[key])
#     return ""


def _extract_metrics(payload: Dict[str, Any]) -> IChatMetrics:
    metrics = payload.get("metrics")

    if metrics is None:
        data = payload.get("data", {})
        if isinstance(data, dict):
            metrics = data.get("metrics")

    metrics = metrics or {}

    return IChatMetrics(
        provider=metrics.get("provider", ""),
        model=metrics.get("model", ""),
        mode=metrics.get("mode", ""),
        total_ms=metrics.get("total_ms", 0),
    )

#! The send_message function is the core of this module, responsible for sending a message to the backend API and handling the response. It includes logic for creating a new conversation if one doesn't exist, updating conversation documents, and extracting relevant information from the API response to construct an IChatResponse object. It also has error handling to provide fallback responses when the backend is unreachable.
#! Check related method using for get response, dont use dict[str, Any] if possible, use IChatResponse or other dataclass to make it more clear and type safe.
def send_message(
    api: ApiClient,
    conversation_id: Optional[str],
    content: str,
    selected_docs: List[str],
    provider: str,
    model: str,
    system_prompt: str,
    mode: str,
    allow_mock: bool = True,
) -> Dict[str, Any]:
    try:
        new_conversation = False
        if not conversation_id:
            conv = api.create_conversation(
                title=content[:64],
                provider=provider,
                model=model,
                system_prompt=system_prompt,
                document_ids=selected_docs,
                mode=mode,
            )
            conversation_id = conv.get("id") or conv.get("conversation_id") or conv.get("uuid")
            new_conversation = True
        if not conversation_id:
            raise ApiError("Conversation id missing from create response")

        if not new_conversation:
            api.update_conversation_documents(conversation_id, selected_docs)

        response = api.send_message(
            conversation_id,
            content,
            provider=provider,
            model=model,
        )
        assistant = response.get("assistant") or "No response text returned."
        metrics = _extract_metrics(response)
        return IChatResponse(
            assistant=assistant,
            conversation_id=conversation_id,
            metrics=metrics,
            new_conversation=new_conversation,
            error=None,
            used_mock=False,
        ).__dict__
    except ApiError as exc:
        if not allow_mock:
            return IChatResponse(
                assistant="",
                conversation_id=conversation_id or "",
                metrics=IChatMetrics(provider=provider, model=model, mode=mode, total_ms=0),
                new_conversation=False,
                error=str(exc),
                used_mock=False,
            ).__dict__
        fallback = (
            "Backend unreachable. This is a local mock response so you can continue "
            "designing the UI."
        )
        return IChatResponse(
            assistant=fallback,
            conversation_id=conversation_id or "",
            metrics=IChatMetrics(provider=provider, model=model, mode=mode, total_ms=0),
            new_conversation=False,
            error=str(exc),
            used_mock=True,
        ).__dict__
