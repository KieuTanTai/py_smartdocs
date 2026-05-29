from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from sys_services.enums.e_provider_name import EProviderName
from sys_services.read_config.config_provider import (
    DEFAULT_CONFIG_PROVIDER,
    IConfigProvider,
)
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER
from .gemini import GeminiClient
from .mistral import MistralClient
from .ollama import OllamaClient


class LLMProviderFactory(ILLMProviderFactory):
    def __init__(self, config_provider: IConfigProvider, logger: ILogger | None = None):
        self.logger = logger or DEFAULT_LOGGER
        self.config_provider = config_provider or DEFAULT_CONFIG_PROVIDER

    def get_provider(self, provider: EProviderName) -> ILLMClient:
        self.logger.info(
            f"Creating LLM client for provider: {provider}",
            source="LLMProviderFactory.get_provider",
        )

        if provider == EProviderName.GEMINI.value:
            EMBEDDING_CONFIG = self.config_provider.get_gemini_config()
            return GeminiClient(
                api_key=EMBEDDING_CONFIG["api_key"],
                model=EMBEDDING_CONFIG["model"],
                provider_name=provider,
                timeout=EMBEDDING_CONFIG["timeout_seconds"],
                logger=self.logger,
            )
        elif provider == EProviderName.MISTRAL.value:
            MISTRAL_CONFIG = self.config_provider.get_mistral_config()
            return MistralClient(
                api_key=MISTRAL_CONFIG["api_key"],
                model=MISTRAL_CONFIG["model"],
                provider_name=provider,
                timeout=MISTRAL_CONFIG["timeout_seconds"],
                logger=self.logger,
            )
        elif provider == EProviderName.OLLAMA.value:
            OLLAMA_CONFIG = self.config_provider.get_ollama_config()
            return OllamaClient(
                base_url=OLLAMA_CONFIG["base_url"],
                model=OLLAMA_CONFIG["model"],
                provider_name=provider,
                timeout=OLLAMA_CONFIG["timeout_seconds"],
                logger=self.logger,
            )
        else:
            self.logger.error(
                f"Unsupported provider: {provider}",
                source="LLMProviderFactory.get_provider",
            )
            raise ValueError(f"Unsupported provider: {provider}")
