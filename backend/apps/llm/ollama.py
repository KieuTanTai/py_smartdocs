import httpx
from sys_services.time_counter import TimeCounter
from backend.apps.interfaces.services.chat.i_completion import (
    ICompletionInfo,
    ICompletionRequest,
    ICompletionResponse,
)
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER


class OllamaClient(ILLMClient):

    def __init__(
        self,
        base_url: str,
        model: str,
        provider_name: str,
        timeout: float = 60.0,
        logger: ILogger | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.provider_name = provider_name
        self.logger = logger or DEFAULT_LOGGER

    async def generate(self, request: ICompletionRequest) -> ICompletionResponse:
        self.logger.info(
            f"Sending request to Ollama: model={request.model or self.model}, prompt_length={len(request.prompt)}",
            source="OllamaClient.generate",
        )

        started_at = TimeCounter.start()
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
        elapsed_ms = TimeCounter.elapsed_ms(started_at)

        self.logger.info(
            f"Generated content in {elapsed_ms} ms", source="OllamaClient.generate"
        )
        self.logger.info(
            f"Ollama response content length: {len(data.get('response', ''))}",
            source="OllamaClient.generate",
        )
        self.logger.info(
            "successfully generated content from Ollama API.",
            source="OllamaClient.generate",
        )
        return ICompletionResponse(
            provider=self.provider_name,
            model=request.model or self.model,
            content=data.get("response", ""),
            latency_ms=elapsed_ms,
        )

    async def is_available(self) -> bool:
        self.logger.info(
            "Checking Ollama API availability.", source="OllamaClient.is_available"
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/version")
                response.raise_for_status()
            return True
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            self.logger.error(
                f"Ollama API is not available: {str(e)}",
                source="OllamaClient.is_available",
            )
            return False

    def get_model_info(self) -> ICompletionInfo:
        self.logger.info(
            "Retrieving Ollama model info.", source="OllamaClient.get_model_info"
        )
        return ICompletionInfo(
            provider=self.provider_name,
            model=self.model,
            capabilities=["text-generation"],
        )
