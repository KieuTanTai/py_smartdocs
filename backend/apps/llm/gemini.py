import httpx
from sys_services.time_counter import TimeCounter
from backend.apps.interfaces.conversation.i_completion import (
    ICompletionInfo,
    ICompletionRequest,
    ICompletionResponse,
)
from backend.apps.interfaces.llm.i_llm_client import ILLMClient
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER


class GeminiClient(ILLMClient):
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 60.0,
        logger: ILogger | None = None,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.logger = logger or DEFAULT_LOGGER

    async def generate(self, request: ICompletionRequest) -> ICompletionResponse:
        self.logger.info("Sending request to Gemini API.", source=str(self.__class__))

        started_at = TimeCounter.start()
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
        elapsed_ms = TimeCounter.elapsed_ms(started_at)

        self.logger.info(
            f"Generated content in {elapsed_ms} ms", source=str(self.__class__)
        )
        self.logger.info(
            "successfully generated content using Gemini API.",
            source=str(self.__class__),
        )

        return ICompletionResponse(
            provider=self.provider_name,
            model=request.model or self.model,
            content=content,
            latency_ms=elapsed_ms,
        )

    async def is_available(self) -> bool:
        self.logger.info(
            "Checking Gemini API availability.", source=str(self.__class__)
        )

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    url, json={"contents": [{"parts": [{"text": "ping"}]}]}
                )
                self.logger.info("Gemini API is available.", source=str(self.__class__))
                return response.status_code == 200
        except Exception as e:
            self.logger.error(
                f"Error occurred while checking Gemini API availability: {e}",
                source=str(self.__class__),
            )
            return False

    def get_model_info(self) -> ICompletionInfo:
        self.logger.info("Retrieving Gemini model info.", source=str(self.__class__))
        return ICompletionInfo(
            provider=self.provider_name,
            model=self.model,
            capabilities=["text-generation"],
        )
