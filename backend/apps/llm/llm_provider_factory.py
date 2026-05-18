from backend.apps.interfaces.llm.llm_provider_factory_interface import (
    LLMProviderFactoryInterface,
)
from backend.apps.interfaces.llm.llm_client_interface import LLMClientInterface
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.read_config.read_ollama_config import OLLAMA_CONFIG
from sys_services.interfaces.logging_interface import ILogger
from sys_services.logging import DEFAULT_LOGGER


class LLMProviderFactory(LLMProviderFactoryInterface):
    def __init__(self, model_name: str, logger: ILogger | None = None):
        self.provider = model_name
        self.logger = logger or DEFAULT_LOGGER

    def get_provider(self) -> LLMClientInterface:
        self.logger.info(
            f"Creating LLM client for provider: {self.provider}",
            source="LLMProviderFactory.get_provider",
        )

        if self.provider == "gemini":
            from .gemini import GeminiClient

            return GeminiClient(
                api_key=GEMINI_EMBEDDING_CONFIG["api_key"],
                model=GEMINI_EMBEDDING_CONFIG["model"],
                timeout=GEMINI_EMBEDDING_CONFIG["timeout_seconds"],
                logger=self.logger,
            )
        elif self.provider == "mistral":
            from .mistral import MistralClient

            return MistralClient(
                api_key=MISTRAL_CONFIG["api_key"],
                model=MISTRAL_CONFIG["model"],
                timeout=MISTRAL_CONFIG["timeout_seconds"],
                logger=self.logger,
            )
        elif self.provider == "ollama":
            from .ollama import OllamaClient

            return OllamaClient(
                base_url=OLLAMA_CONFIG["base_url"],
                model=OLLAMA_CONFIG["model"],
                timeout=OLLAMA_CONFIG["timeout_seconds"],
                logger=self.logger,
            )
        else:
            self.logger.error(
                f"Unsupported provider: {self.provider}",
                source="LLMProviderFactory.get_provider",
            )
            raise ValueError(f"Unsupported provider: {self.provider}")
