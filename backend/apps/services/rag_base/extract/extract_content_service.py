from pathlib import Path

from backend.apps.interfaces.services.chat.i_completion import ICompletionResponse
from backend.apps.interfaces.core.storage.i_storage import IFileStorage
from backend.apps.interfaces.llm.llm_ocr.i_llm_ocr_factory import ILLMOCRFactory
from sys_services.enums.e_provider_name import EProviderName
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER
from backend.apps.interfaces.services.rag_base.extract.i_extract_content import (
    IExtractContent,
)
from backend.apps.utils.mime_type import get_mime_type_from_path


class IExtractContentService(IExtractContent):

    def __init__(
        self,
        factory: ILLMOCRFactory,
        storage: IFileStorage,
        provider: EProviderName,
        logger: ILogger | None = None,
    ):
        if provider is None:
            raise ValueError("Provider must be specified for ExtractContentService")
        self.provider = provider
        self.factory = factory
        self.storage = storage
        self.logger = logger or DEFAULT_LOGGER

    async def extract_from_file_text(self, file_path: Path) -> ICompletionResponse:
        mime_type = get_mime_type_from_path(file_path)
        uploaded_file = await self.storage.save_file(mime_type, file_path)
        ocr_extractor = self.factory.create_ocr_extractor(self.provider)
        return await ocr_extractor.process_ocr(uploaded_file)

    async def extract_from_file_image(self, file_path: Path) -> ICompletionResponse:
        mime_type = get_mime_type_from_path(file_path)
        uploaded_file = await self.storage.save_file(mime_type, file_path)
        ocr_extractor = self.factory.create_ocr_extractor(self.provider)
        return await ocr_extractor.process_ocr(uploaded_file)
