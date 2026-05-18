import httpx
from sys_services.time_counter import TimeCounter
from backend.apps.interfaces.conversation.completion_interface import (
    CompletionInfoInterface,
    CompletionRequestInterface,
    CompletionResponseInterface,
)
from backend.apps.interfaces.llm.llm_client_interface import LLMClientInterface
from sys_services.interfaces.logging_interface import ILogger
from sys_services.logging import DEFAULT_LOGGER


class MistralClient(LLMClientInterface):
    provider_name = "mistral"

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

    async def generate(
        self, request: CompletionRequestInterface
    ) -> CompletionResponseInterface:
        self.logger.info("Sending request to Mistral API.", source=str(self.__class__))

        started_at = TimeCounter.start()
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
        elapsed_ms = TimeCounter.elapsed_ms(started_at)

        self.logger.info(
            f"Generated content in {elapsed_ms} ms", source=str(self.__class__)
        )
        self.logger.info(
            "successfully generated content using Mistral API.",
            source=str(self.__class__),
        )

        return CompletionResponseInterface(
            provider=self.provider_name,
            model=request.model or self.model,
            content=data["choices"][0]["message"]["content"],
            latency_ms=elapsed_ms,
        )

    async def is_available(self) -> bool:
        self.logger.info(
            "Checking Mistral API availability.", source=str(self.__class__)
        )

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    "https://api.mistral.ai/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                self.logger.info(
                    "Mistral API is available.", source=str(self.__class__)
                )
                return response.status_code == 200
        except Exception as e:
            self.logger.error(
                f"Error occurred while checking Mistral API availability: {e}",
                source=str(self.__class__),
            )
            return False

    def get_model_info(self) -> CompletionInfoInterface:
        self.logger.info("Retrieving Mistral model info.", source=str(self.__class__))
        return CompletionInfoInterface(
            provider=self.provider_name,
            model=self.model,
            capabilities=["chat", "completion"],
        )
