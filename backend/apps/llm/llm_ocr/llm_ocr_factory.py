from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr import ILLMOCR
from backend.apps.llm.llm_ocr.mistral_ocr import MistralLLMOCR
from backend.apps.llm.llm_ocr.generic_ocr import GenericOCR
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr_factory import ILLMOCRFactory
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.read_config.config_provider import (
    IConfigProvider,
)
from sys_services.system_dirs import METADATA_DIR


class LLMOCRFactory(ILLMOCRFactory):

    def __init__(self, config_provider: IConfigProvider, logger: ILogger):
        self.config_provider = config_provider
        self.logger = logger

    def create_ocr_extractor(self, provider_name: EProviderName) -> ILLMOCR:
        self.logger.info(
            f"Creating LLM OCR Extractor for provider: {provider_name.value}",
            source=str(self.__class__),
        )

        # TEMPORARY FIX: Use Generic OCR for all providers due to Mistral SDK OCR attribute issue
        # TODO: Re-enable MistralLLMOCR when SDK is fixed or upgraded
        if provider_name == EProviderName.MISTRAL:
            self.logger.warning(
                f"Mistral OCR temporarily disabled due to SDK issues. Using Generic OCR instead.",
                source=str(self.__class__),
            )
            # Fallback to generic OCR
            return GenericOCR(
                provider_name=provider_name.value,
                logger=self.logger,
                storage_dir=METADATA_DIR,
            )
        elif provider_name in [EProviderName.GEMINI, EProviderName.OLLAMA]:
            # Use generic OCR for providers without dedicated OCR support
            self.logger.info(
                f"Using generic OCR extractor for provider: {provider_name.value}",
                source=str(self.__class__),
            )
            return GenericOCR(
                provider_name=provider_name.value,
                logger=self.logger,
                storage_dir=METADATA_DIR,
            )
        else:
            raise ValueError(f"Unsupported provider: {provider_name.value}")
