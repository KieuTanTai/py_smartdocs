from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr import ILLMOCR
from backend.apps.llm.llm_ocr.mistral_ocr import MistralLLMOCR
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr_factory import ILLMOCRFactory
from sys_services.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.read_config.config_provider import (
    DEFAULT_CONFIG_PROVIDER,
    IConfigProvider,
)


class LLMOCRFactory(ILLMOCRFactory):

    def __init__(self, config_provider: IConfigProvider, logger: ILogger):
        self.config_provider = config_provider or DEFAULT_CONFIG_PROVIDER
        self.logger = logger

    def create_ocr_extractor(self, provider_name: EProviderName) -> ILLMOCR:
        self.logger.info(
            f"Creating LLM OCR Extractor for provider: {provider_name.value}",
            source=str(self.__class__),
        )

        if provider_name == EProviderName.MISTRAL:
            MISTRAL_CONFIG = self.config_provider.get_mistral_config()
            return MistralLLMOCR(
                api_key=MISTRAL_CONFIG["api_key"],
                model=MISTRAL_CONFIG["ocr_model"],
                provider_name=provider_name.value,
                timeout_seconds=MISTRAL_CONFIG.get("timeout_seconds", 60.0),
                logger=self.logger,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider_name.value}")
