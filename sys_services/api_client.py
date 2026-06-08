from __future__ import annotations

import os
import httpx
from typing import Any, Dict, Optional
from backend.apps.core.interfaces.request.i_create_conversation_request import ICreateConversationRequest
from backend.apps.core.interfaces.request.i_send_message_request import ISendMessageRequest
from sys_services.system_dirs import DEFAULT_BASE_URL


class ApiError(RuntimeError):
    pass


class ApiClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0) -> None:
        self.base_url = (
            base_url or os.getenv("SMARTDOCS_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    def clear_session(self) -> None:
        self._access_token = None
        self._refresh_token = None

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def set_tokens(self, access_token: str, refresh_token: str, user: Optional[Dict] = None) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token

    #! NOTE RECOMMEND USE DICT[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = self._headers()
        if "headers" in kwargs:
            headers = {**headers, **kwargs.pop("headers")}
        # Multipart uploads set their own Content-Type with boundary;
        # avoid overriding it with application/json.
        is_multipart = "files" in kwargs
        if is_multipart and "Content-Type" in headers:
            headers = {k: v for k, v in headers.items() if k != "Content-Type"}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
        except httpx.RequestError as exc:
            raise ApiError(f"Request failed: {exc}") from exc
        except httpx.HTTPStatusError as exc:
            # Safely read response body, handling non-UTF-8 content (e.g. HTML error pages)
            raw_body = exc.response.content
            try:
                body_text = raw_body.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    body_text = raw_body.decode("latin-1")
                except Exception:
                    body_text = raw_body.decode("utf-8", errors="replace")
            raise ApiError(
                f"HTTP {exc.response.status_code}: {body_text}"
            ) from exc

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return {"raw": response.text}

    #! NOTE RECOMMEND USE DICT[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
    def _request_with_fallback(
        self, method: str, primary_path: str, fallback_path: str, **kwargs: Any
    ) -> Dict[str, Any]:
        try:
            return self._request(method, primary_path, **kwargs)
        except ApiError as exc:
            print(f"Primary path {primary_path} failed: {exc}")
            if "HTTP 404" not in str(exc):
                raise
        return self._request(method, fallback_path, **kwargs)

    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/api/health/")

    def list_conversations(self) -> Dict[str, Any]:
        return self._request("GET", "/api/conversations/")

    #! NOTE RECOMMEND USE DICT[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
    def create_conversation(
        self,
        title: str,
        provider: str,
        model: str,
        system_prompt: str,
        document_ids: list[str],
        mode: str,
    ) -> Dict[str, Any]:
        payload = ICreateConversationRequest(
            title=title,
            provider=provider,
            model=model,
            system_prompt=system_prompt,
            document_ids=document_ids,
            mode=mode,
        )
        return self._request("POST", "/api/conversations/", json=payload)

    def send_message(
        self,
        conversation_id: str,
        content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        request = ISendMessageRequest(
            conversation_id=conversation_id,
            message=content,
            provider=provider,
            model=model,
        )
        return self._request(
            "POST", f"/api/conversations/{conversation_id}/messages/", json=request
        )

    #! NOTE RECOMMEND USE DICT[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
    def update_conversation_documents(
        self, conversation_id: str, document_ids: list[str]
    ) -> Dict[str, Any]:
        payload = {"document_ids": document_ids}
        return self._request(
            "PATCH",
            f"/api/conversations/{conversation_id}/documents/",
            json=payload,
        )

    #! NOTE RECOMMEND USE DICT[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
    def upload_document(self, file_info: dict, source: str) -> Dict[str, Any]:
        file_type = file_info.get("type") or "application/octet-stream"
        print(f"Uploading document with file type: {file_type}")
        print(f"File info: {file_info}")
        print(f"Source: {source}")
        with open(file_info["datapath"], "rb") as handle:
            files = {"file": (file_info["name"], handle, file_type)}
            data = {"source": source}
            # Multipart requests don't use JSON headers
            resp = self._request_with_fallback(
                "POST",
                "/api/documents/upload/",
                "/api/documents/",
                files=files,
                data=data,
            )
            print(f"Upload response: {resp}")
            return resp

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

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/api/documents/{document_id}/")

    # ── Auth ────────────────────────────────────────────────────────────────
    #! UNUSED: These methods are defined for completeness but not currently called by the frontend.
    def signup(self, email: str, password: str, name: str) -> Dict[str, Any]:
        payload = {"email": email, "password": password, "name": name}
        return self._request("POST", "/api/auth/signup/", json=payload)

    def login(self, email: str, password: str) -> Dict[str, Any]:
        payload = {"email": email, "password": password}
        return self._request("POST", "/api/auth/login/", json=payload)

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        payload = {"refresh_token": refresh_token}
        return self._request("POST", "/api/auth/refresh/", json=payload)

    def me(self) -> Dict[str, Any]:
        return self._request("GET", "/api/auth/me/")

    def logout(self, user_id: str) -> Dict[str, Any]:
        payload = {"user_id": user_id}
        return self._request("POST", "/api/auth/logout/", json=payload)
