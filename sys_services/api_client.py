from __future__ import annotations

import os
import httpx
from typing import Any, Dict, Optional
from sys_services.system_dirs import DEFAULT_BASE_URL


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 20.0) -> None:
        self.base_url = (
            base_url or os.getenv("SMARTDOCS_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, **kwargs)
            response.raise_for_status()
        except httpx.RequestError as exc:
            raise ApiError(f"Request failed: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            raise ApiError(
                f"HTTP {exc.response.status_code}: {exc.response.text}"
            ) from exc

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return {"raw": response.text}

    def _request_with_fallback(
        self, method: str, primary_path: str, fallback_path: str, **kwargs: Any
    ) -> Dict[str, Any]:
        try:
            return self._request(method, primary_path, **kwargs)
        except ApiError as exc:
            if "HTTP 404" not in str(exc):
                raise
        return self._request(method, fallback_path, **kwargs)

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/api/health/")

    def list_conversations(self) -> Dict[str, Any]:
        return self._request("GET", "/api/conversations/")

    def create_conversation(
        self,
        title: str,
        provider: str,
        model: str,
        system_prompt: str,
        document_ids: list[str],
        mode: str,
    ) -> Dict[str, Any]:
        payload = {
            "title": title,
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "document_ids": document_ids,
            "mode": mode,
        }
        return self._request("POST", "/api/conversations/", json=payload)

    def send_message(self, conversation_id: str, content: str) -> Dict[str, Any]:
        payload = {"content": content}
        return self._request(
            "POST", f"/api/conversations/{conversation_id}/messages/", json=payload
        )

    def update_conversation_documents(
        self, conversation_id: str, document_ids: list[str]
    ) -> Dict[str, Any]:
        payload = {"document_ids": document_ids}
        return self._request(
            "PATCH",
            f"/api/conversations/{conversation_id}/documents/",
            json=payload,
        )

    def upload_document(self, file_info: dict, source: str) -> Dict[str, Any]:
        file_type = file_info.get("type") or "application/octet-stream"
        print(f"Uploading document with file type: {file_type}")
        print(f"File info: {file_info}")
        print(f"Source: {source}")
        with open(file_info["datapath"], "rb") as handle:
            files = {"file": (file_info["name"], handle, file_type)}
            data = {"source": source}
            return self._request_with_fallback(
                "POST",
                "/api/documents/upload/",
                "/api/documents/",
                files=files,
                data=data,
            )

    def index_document(self, document_id: str) -> Dict[str, Any]:
        return self._request_with_fallback(
            "POST",
            f"/api/documents/{document_id}/index/",
            f"/api/documents/{document_id}/process/",
        )

    def document_status(self, document_id: str) -> Dict[str, Any]:
        return self._request_with_fallback(
            "GET",
            f"/api/documents/{document_id}/status/",
            f"/api/documents/{document_id}/",
        )

    def signup(self, email: str, password: str, name: str) -> Dict[str, Any]:
        payload = {"email": email, "password": password, "name": name}
        return self._request("POST", "/api/auth/signup/", json=payload)
