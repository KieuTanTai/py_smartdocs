from backend.apps.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.interfaces.llm.i_llm_client import ILLMClient
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER


class LLMProviderFactory(ILLMProviderFactory):
    def __init__(self, model_name: str, logger: ILogger | None = None):
        self.provider = model_name
        self.logger = logger or DEFAULT_LOGGER

    def get_provider(self) -> ILLMClient:
        self.logger.info(
            f"Creating LLM client for provider: {self.provider}",
            source="LLMProviderFactory.get_provider",
        )

        if self.provider == "gemini":
            from .gemini import GeminiClient

            EMBEDDING_CONFIG = DEFAULT_CONFIG_PROVIDER.get_gemini_config()
            return GeminiClient(
                api_key=EMBEDDING_CONFIG["api_key"],
                model=EMBEDDING_CONFIG["model"],
                timeout=EMBEDDING_CONFIG["timeout_seconds"],
                logger=self.logger,
            )
        elif self.provider == "mistral":
            from .mistral import MistralClient

            MISTRAL_CONFIG = DEFAULT_CONFIG_PROVIDER.get_mistral_config()
            return MistralClient(
                api_key=MISTRAL_CONFIG["api_key"],
                model=MISTRAL_CONFIG["model"],
                timeout=MISTRAL_CONFIG["timeout_seconds"],
                logger=self.logger,
            )
        elif self.provider == "ollama":
            from .ollama import OllamaClient

            OLLAMA_CONFIG = DEFAULT_CONFIG_PROVIDER.get_ollama_config()
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
