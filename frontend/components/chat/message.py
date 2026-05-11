from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from sys_services.api_client import ApiClient, ApiError


def build_message(
    role: str, content: str, meta: Optional[dict] = None
) -> Dict[str, Any]:
    return {
        "role": role,
        "content": content,
        "meta": meta or {},
        "ts": time.time(),
    }


def _extract_id(payload: Dict[str, Any]) -> Optional[str]:
    for key in ("id", "conversation_id", "uuid"):
        if key in payload:
            return str(payload[key])
    data = payload.get("data", {})
    if isinstance(data, dict):
        for key in ("id", "conversation_id", "uuid"):
            if key in data:
                return str(data[key])
    return None


def _extract_text(payload: Dict[str, Any]) -> str:
    for key in ("message", "content", "answer", "text"):
        if key in payload and payload[key]:
            return str(payload[key])
    data = payload.get("data", {})
    if isinstance(data, dict):
        for key in ("message", "content", "answer", "text"):
            if key in data and data[key]:
                return str(data[key])
    return ""


def _extract_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "metrics" in payload and isinstance(payload["metrics"], dict):
        return payload["metrics"]
    data = payload.get("data", {})
    if isinstance(data, dict) and isinstance(data.get("metrics"), dict):
        return data["metrics"]
    return {}


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
            conversation_id = _extract_id(conv)
            new_conversation = True
        if not conversation_id:
            raise ApiError("Conversation id missing from create response")

        response = api.send_message(conversation_id, content)
        assistant = _extract_text(response) or "No response text returned."
        metrics = _extract_metrics(response)
        return {
            "assistant": assistant,
            "conversation_id": conversation_id,
            "metrics": metrics,
            "new_conversation": new_conversation,
            "error": None,
            "used_mock": False,
        }
    except ApiError as exc:
        if not allow_mock:
            return {
                "assistant": "Request failed. Check backend connectivity.",
                "conversation_id": conversation_id or f"local-{int(time.time())}",
                "metrics": {},
                "new_conversation": False,
                "error": str(exc),
                "used_mock": False,
            }
        fallback = (
            "Backend unreachable. This is a local mock response so you can continue "
            "designing the UI."
        )
        return {
            "assistant": fallback,
            "conversation_id": conversation_id or f"local-{int(time.time())}",
            "metrics": {
                "provider": provider,
                "model": model,
                "mode": mode,
                "total_ms": 0,
            },
            "new_conversation": False,
            "error": str(exc),
            "used_mock": True,
        }
