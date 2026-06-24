from __future__ import annotations

import os
import httpx
from typing import Any, Dict, Optional

from pathlib import Path

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from sys_services.system_dirs import DEFAULT_BASE_URL


class ApiError(RuntimeError):
    pass


def _pipeline_type_value(pipeline_type: str) -> str:
    if pipeline_type == "normal":
        return EPipelineType.BASE.value
    return pipeline_type or EPipelineType.BASE.value


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

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    def set_tokens(self, access_token: str, refresh_token: str, user: Optional[Dict] = None) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token

    #! NOTE RECOMMEND USE DICT[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        print(f"url: {url}")
        headers = self._headers()
        if "headers" in kwargs:
            headers = {**headers, **kwargs.pop("headers")}
        # Multipart uploads set their own Content-Type with boundary;
        # avoid overriding it with application/json.
        print(f"headers: {headers}")
        is_multipart = "files" in kwargs
        print(kwargs.keys())
        print("is_multipart =", "files" in kwargs)
        if is_multipart and "Content-Type" in headers:
            headers = {k: v for k, v in headers.items() if k != "Content-Type"}
        # return {}
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                request = client.build_request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                )

                print("REQUEST HEADERS")
                print(request)

                response = client.send(request)
                print(f"response: {response}")
                response.raise_for_status()
        except httpx.RequestError as exc:
            print("fallback here")
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
        print(f"content_type:{content_type}")
        if "application/json" in content_type:
            return response.json()
        return {"raw": response.text}

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/api/health/")

    def list_conversations(self) -> dict[str, Any]:
        return self._request("GET", "/api/conversations/")

    def create_conversation(
        self,
        title: str,
        provider: str,
        system_prompt: str = "",
        document_ids: Optional[list[str]] = None,
        mode: str = EPipelineType.BASE.value,
    ) -> dict[str, Any]:
        payload = {
            "title": title or "New Conversation",
            "provider": provider,
            "system_prompt": system_prompt,
            "document_ids": document_ids or [],
            "mode": mode,
        }
        return self._request("POST", "/api/conversations/", json=payload)

    def send_message(
        self,
        conversation_id: str,
        content: str,
        provider: str,
    ) -> dict[str, Any]:

        return self._send_message_request(
            "POST", f"/api/documents/send_message/", provider, conversation_id, content)
    
    def _send_message_request(self,method: str ,api_endpoint: str, provider_name:str , conversation_id, content:str) -> dict[str, Any]:
        url = f"{self.base_url}{api_endpoint}"
        print(f"url: {url}")
        headers = self._headers()
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                request = client.build_request(
                    method,
                    url,
                    headers=headers,
                    json={"provider": provider_name,"content": content ,"type": EPipelineType.BASE.value,"conversation_id": conversation_id },
                )

                print("REQUEST HEADERS")
                print(request.content)

                response = client.send(request)
                print(f"response: {response}")
                # response.raise_for_status()
        except httpx.RequestError as exc:
            print("fallback here")
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
        print(f"content_type:{content_type}")
        if "application/json" in content_type:
            return response.json()
        return {"raw": response.text}
        

    #! NOTE RECOMMEND USE DICT[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
    def update_conversation_documents(
        self, conversation_id: str, document_ids: list[str]
    ) -> dict[str, Any]:
        payload = {"document_ids": document_ids}
        return self._request(
            "PATCH",
            f"/api/conversations/{conversation_id}/documents/",
            json=payload,
        )

    #! NOTE RECOMMEND USE DICT[str, Any] IN FUNCTION SIGNATURE, USE IChatResponse or other dataclass to make it more clear and type safe.
    def upload_document(self, file_info: dict, source: str, provider: str) -> dict[str, Any]:
        file_type = file_info.get("type") or "application/octet-stream"
        provider_name = EProviderName(provider)
        print(f"Uploading document with file type: {file_type}")
        print(f"File info: {file_info}")
        print(f"Source: {source}")
        print(f"Provider: ", {provider_name})
        with open(file_info["datapath"], "rb") as handle:
            files = {"file": (file_info["name"], handle, file_type)}
            print(f"files: {files}")
            data = {"source": source}
            print(f"data:{data}")
            # Multipart requests don't use JSON headers
            resp = self._upload_request("POST", "/api/documents/upload/", files,provider, [file_info["datapath"]], EPipelineType.BASE.value, "")
            print(f"Upload response:")
            return resp

    def _upload_request(self,method: str ,api_endpoint: str, file_info: dict,provider_name:str ,document_urls: list[Path], type:str, conversation_id) -> dict[str, Any]:
        url = f"{self.base_url}{api_endpoint}"
        print(f"url: {url}")
        headers = self._headers()
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                request = client.build_request(
                    method,
                    url,
                    headers=headers,
                    json={"provider": provider_name,"document_urls": document_urls ,"type": type,"conversation_id": conversation_id },
                )

                print("REQUEST HEADERS")
                print(request.content)

                response = client.send(request)
                print(f"response: {response}")
                # response.raise_for_status()
        except httpx.RequestError as exc:
            print("fallback here")
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
        print(f"content_type:{content_type}")
        if "application/json" in content_type:
            return response.json()
        return {"raw": response.text}


    
    def delete_document(self, document_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/api/documents/{document_id}/")

    # ── Auth ────────────────────────────────────────────────────────────────
    #! UNUSED: These methods are defined for completeness but not currently called by the frontend.
    def signup(self, email: str, password: str, name: str) -> dict[str, Any]:
        payload = {"email": email, "password": password, "name": name}
        return self._request("POST", "/api/auth/signup/", json=payload)

    def login(self, email: str, password: str) -> dict[str, Any]:
        payload = {"email": email, "password": password}
        return self._request("POST", "/api/auth/login/", json=payload)

    def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        payload = {"refresh_token": refresh_token}
        return self._request("POST", "/api/auth/refresh/", json=payload)

    def me(self) -> dict[str, Any]:
        return self._request("GET", "/api/auth/me/")

    def logout(self, user_id: str) -> dict[str, Any]:
        payload = {"user_id": user_id}
        return self._request("POST", "/api/auth/logout/", json=payload)
