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
def send_message(
    api: ApiClient,
    conversation_id: Optional[str],
    content: str,
    selected_docs: list[str],
    provider: str,
    system_prompt: str,
    mode: str,
    allow_mock: bool = True,
) -> dict[str, Any]:
    try:
        new_conversation = False
        if not conversation_id:
            conv = api.create_conversation(
                title=content[:64],
                provider=provider,
                system_prompt=system_prompt,
                document_ids=selected_docs,
                mode=mode,
            )
            conversation_id = _conversation_id(conv)
            new_conversation = True
        if not conversation_id:
            raise ApiError("Conversation id missing from create response")
        print(f"Sending message to conversation {conversation_id} with content: {content}")
        print(f"Provider: {provider}, Mode: {mode}, Selected Docs: {selected_docs}")
        response = api.send_message(
            conversation_id,
            content,
            provider=provider,
            pipeline_type=mode,
        )
        assistant = (
            response.get("assistant")
            or response.get("assistant_message")
            or response.get("message")
            or "No response text returned."
        )
        response_conversation_id = _conversation_id(response) or conversation_id
        metrics = _extract_metrics(response, provider, mode)
        return _response_dict(IChatResponse(
            assistant=assistant,
            conversation_id=response_conversation_id,
            metrics=metrics,
            new_conversation=new_conversation,
            error=None,
            used_mock=bool(response.get("used_mock", False)),
        ))
    except ApiError as exc:
        error_metrics = IChatMetrics(
            provider=_provider(provider),
            model="",
            mode=_enum_value(mode or EPipelineType.BASE.value),
            total_ms=0,
        )
        if not allow_mock:
            return _response_dict(IChatResponse(
                assistant="",
                conversation_id=conversation_id or "",
                metrics=error_metrics,
                new_conversation=False,
                error=str(exc),
                used_mock=False,
            ))
        fallback = (
            "Backend unreachable. This is a local mock response so you can continue "
            "designing the UI."
        )
        return _response_dict(IChatResponse(
            assistant=fallback,
            conversation_id=conversation_id or "",
            metrics=error_metrics,
            new_conversation=False,
            error=str(exc),
            used_mock=True,
        ))
