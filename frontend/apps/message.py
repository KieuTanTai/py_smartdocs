from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.request.i_chat_message import IChatMessage
from backend.apps.core.interfaces.dataclass.response.i_chat_response import IChatMetrics, IChatResponse
from sys_services.api_client import ApiClient, ApiError


# ? These functions are designed to be called by the frontend to send messages and handle responses in a consistent way, including error handling and fallback behavior.
def build_message(
    role: str, content: str, meta: Optional[dict] = None
) -> dict[str, Any]:
    return asdict(IChatMessage(role=role, content=content, meta=meta or {}))


def _enum_value(value: Any) -> str:
    return getattr(value, "value", value) or ""


def _provider(value: Any) -> EProviderName:
    if isinstance(value, EProviderName):
        return value
    try:
        return EProviderName(str(value))
    except ValueError:
        return EProviderName.OLLAMA


def _extract_metrics(payload: dict[str, Any], provider: str, mode: str) -> IChatMetrics:
    metrics = payload.get("metrics")

    if metrics is None:
        data = payload.get("data", {})
        if isinstance(data, dict):
            metrics = data.get("metrics")

    metrics = metrics or {}
    response_mode = metrics.get("mode") or metrics.get("pipeline_type") or payload.get("pipeline_type") or mode
    total_ms = metrics.get("total_ms") or payload.get("latency_ms") or 0

    return IChatMetrics(
        provider=_provider(metrics.get("provider") or payload.get("provider") or provider),
        model=metrics.get("model") or payload.get("model") or "",
        mode=_enum_value(response_mode),
        total_ms=total_ms,
    )


def _conversation_id(payload: dict[str, Any]) -> str:
    return str(
        payload.get("conversation_id")
        or payload.get("id")
        or payload.get("uuid")
        or ""
    )


def _response_dict(response: IChatResponse) -> dict[str, Any]:
    return asdict(response)

#! The send_message function is the core of this module, responsible for sending a message to the backend API and handling the response. It includes logic for creating a new conversation if one doesn't exist, updating conversation documents, and extracting relevant information from the API response to construct an IChatResponse object. It also has error handling to provide fallback responses when the backend is unreachable.
#! Check related method using for get response, dont use dict[str, Any] if possible, use IChatResponse or other dataclass to make it more clear and type safe.
# def send_message(
#     api: ApiClient,
#     conversation_id: Optional[str],
#     content: str,
#     selected_docs: list[str],
#     provider: str,
#     model: str,
#     system_prompt: str,
#     mode: str,
#     allow_mock: bool = True,
# ) -> dict[str, Any]:
#     try:
#         new_conversation = False
#         if not conversation_id:
#             conv = api.create_conversation(
#                 title=content[:64],
#                 provider=provider,
#                 model=model,
#                 system_prompt=system_prompt,
#                 document_ids=selected_docs,
#                 mode=mode,
#             )
#             conversation_id = conv.get("id") or conv.get("conversation_id") or conv.get("uuid")
#             new_conversation = True
#         if not conversation_id:
#             raise ApiError("Conversation id missing from create response")

#         if not new_conversation:
#             api.update_conversation_documents(conversation_id, selected_docs)

#         response = api.send_message(
#             conversation_id,
#             content,
#             provider=provider,
#             model=model,
#         )
#         assistant = response.get("assistant") or "No response text returned."
#         metrics = _extract_metrics(response)
#         return IChatResponse(
#             assistant=assistant,
#             conversation_id=conversation_id,
#             metrics=metrics,
#             new_conversation=new_conversation,
#             error=None,
#             used_mock=False,
#         ).__dict__
#     except ApiError as exc:
#         if not allow_mock:
#             return IChatResponse(
#                 assistant="",
#                 conversation_id=conversation_id or "",
#                 metrics=IChatMetrics(provider=EProviderName(provider), model=model, mode=mode, total_ms=0),
#                 new_conversation=False,
#                 error=str(exc),
#                 used_mock=False,
#             ).__dict__
#         fallback = (
#             "Backend unreachable. This is a local mock response so you can continue "
#             "designing the UI."
#         )
#         return IChatResponse(
#             assistant=fallback,
#             conversation_id=conversation_id or "",
#             metrics=IChatMetrics(provider=provider, model=model, mode=mode, total_ms=0),
#             new_conversation=False,
#             error=str(exc),
#             used_mock=True,
#         ).__dict__
