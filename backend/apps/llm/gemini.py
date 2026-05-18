import time

import httpx

from backend.apps.interfaces.completion_interface import CompletionInfoInterface, CompletionRequestInterface, CompletionResponseInterface
from backend.apps.interfaces.llm_client_interface import LLMClientInterface

class GeminiClient(LLMClientInterface):
    provider_name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float = 60.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def generate(self, request: CompletionRequestInterface) -> CompletionResponseInterface:
        started_at = time.perf_counter()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{request.model or self.model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": request.prompt}]}]}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = (
                response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else {}
            )
        content = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            content = "".join(part.get("text", "") for part in parts)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return CompletionResponseInterface(
            provider=self.provider_name,
            model=request.model or self.model,
            content=content,
            latency_ms=elapsed_ms,
        )

    async def is_available(self) -> bool:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json={"contents": [{"parts": [{"text": "ping"}]}]})
                return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> CompletionInfoInterface:
        return CompletionInfoInterface(
            provider=self.provider_name,
            model=self.model,
            capabilities=["text-generation"],
        )

