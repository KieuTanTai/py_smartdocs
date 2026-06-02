from pathlib import Path

from backend.apps.core.interfaces.core.i_dataclass_transaction import (
    ICompletionResponse,
)
from backend.apps.core.interfaces.services.rag_base.storage.i_storage import (
    IFileStorage,
)
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr_factory import ILLMOCRFactory
from sys_services.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER
from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import (
    IExtractContent,
)


class ExtractContentService(IExtractContent):

    def __init__(
        self,
        factory: ILLMOCRFactory,
        storage: IFileStorage,
        logger: ILogger | None = None,
    ):
        self.factory = factory
        self.storage = storage
        self.logger = logger or DEFAULT_LOGGER

    def extract_from_file_text(
        self,
        file_path: Path,
        provider: EProviderName,
    ) -> ICompletionResponse:
        if provider is None:
            raise ValueError("Provider must be specified for extract_from_file_text")
        uploaded_file = self.storage.save_file(file_path)
        ocr_extractor = self.factory.create_ocr_extractor(provider)
        return ocr_extractor.process_ocr(uploaded_file)

    def extract_from_file_image(
        self,
        file_path: Path,
        provider: EProviderName,
    ) -> ICompletionResponse:
        if provider is None:
            raise ValueError("Provider must be specified for extract_from_file_image")
        uploaded_file = self.storage.save_file(file_path)
        ocr_extractor = self.factory.create_ocr_extractor(provider)
        return ocr_extractor.process_ocr(uploaded_file)
