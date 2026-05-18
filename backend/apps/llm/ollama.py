import time

import httpx

from backend.apps.interfaces.completion_interface  import CompletionInfoInterface, CompletionRequestInterface, CompletionResponseInterface
from backend.apps.interfaces.llm_client_interface import LLMClientInterface

class OllamaClient(LLMClientInterface):
    provider_name = "ollama"

    def __init__(self, base_url: str, model: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def generate(self, request: CompletionRequestInterface) -> CompletionResponseInterface:
        started_at = time.perf_counter()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": request.model or self.model,
                    "prompt": request.prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_ctx": 8192,
                        "num_predict": 256,
                    },
                },
            )
            response.raise_for_status()
            data = (
                response.json()
                if response.headers.get("content-type", "").startswith(
                    "application/json"
                )
                else {}
            )
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        return CompletionResponseInterface(
            provider=self.provider_name,
            model=request.model or self.model,
            content=data.get("response", ""),
            latency_ms=elapsed_ms,
        )

    async def is_available(self) -> bool:
        raise NotImplementedError

    def get_model_info(self) -> CompletionInfoInterface:
        raise NotImplementedError

