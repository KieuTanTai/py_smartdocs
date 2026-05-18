import time
import httpx
from sys_services.time_counter import TimeCounter
from backend.apps.interfaces.completion_interface import CompletionInfoInterface, CompletionRequestInterface, CompletionResponseInterface
from backend.apps.interfaces.llm_client_interface import LLMClientInterface

class MistralClient(LLMClientInterface):
    provider_name = "mistral"

    def __init__(self, api_key:str, model:str, timeout:float=60.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    async def generate(self, request: CompletionRequestInterface) -> CompletionResponseInterface:
        time_counter = TimeCounter.start()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": request.model or self.model,
                    "messages": [{"role": "user", "content": request.prompt}],
                },
            )
            response.raise_for_status()
            data = response.json()
        elapsed_ms = TimeCounter.elapsed_ms(time_counter)
        return CompletionResponseInterface(
            provider=self.provider_name,
            model=request.model or self.model,
            content=data["choices"][0]["message"]["content"],
            latency_ms=elapsed_ms,
        )

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    "https://api.mistral.ai/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception:
            return False

    def get_model_info(self) -> CompletionInfoInterface:
        return CompletionInfoInterface(
            provider=self.provider_name,
            model=self.model,
            capabilities=["chat", "completion"],
        )
