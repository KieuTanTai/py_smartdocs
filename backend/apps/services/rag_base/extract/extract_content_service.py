from pathlib import Path
from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
from backend.apps.core.interfaces.services.rag_base.storage.i_storage import (
    IFileStorage,
)
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr_factory import ILLMOCRFactory
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import (
    IExtractContent,
)
from backend.apps.core.interfaces.dataclass.ocr.i_ocr_response import IOCRResponse

from backend.apps.utils.is_content_empty import check_empty_content

class ExtractContentService(IExtractContent):

    def __init__(
        self,
        factory: ILLMOCRFactory,
        storage: IFileStorage,
        logger: ILogger,
    ):
        self.factory = factory
        self.storage = storage
        self.logger = logger

    def extract(
        self,
        file_path: Path,
        provider: EProviderName,
        call_by: str = "",
    ) -> IExtractResponse:
        source_log = f"{Path(__file__).parent.absolute()}/{Path(__file__).name}"
        if provider is None:
            raise ValueError("Provider must be specified for extract_from_file_text")
        uploaded_file = self.storage.save_file(file_path)
        ocr_extractor = self.factory.create_ocr_extractor(provider)
        ocr_response = ocr_extractor.process_ocr(uploaded_file)
        extracted_text = self.__process_ocr_response(ocr_response, source_log, call_by=call_by)
        return IExtractResponse(uploaded_file.id, extracted_text, ocr_response.model, ocr_response.usage_info.pages_processed, ocr_response.usage_info.doc_size_bytes)

    def __process_ocr_response(self, ocr_response: IOCRResponse, source_log: str, call_by: str = "") -> str:
        extracted_text = "\n".join([page.markdown for page in ocr_response.pages])
        if self.__validate_response_text(extracted_text, source_log, call_by) is False:
            self.logger.warning(
                f"Extracted text is empty or contains only whitespace. Source log: {source_log}",
                source=str(self.__class__), call_by=call_by, method_call=self.__process_ocr_response.__name__
            )
            raise ValueError("Extracted text is empty or contains only whitespace.")
        return extracted_text

    def __validate_response_text(
        self, text: str, source_log: str, call_by: str = ""
    ) -> bool:
        if check_empty_content(text, source_log, self.logger) is False:
            self.logger.warning(
                f"Extracted text is empty or contains only whitespace. Source log: {source_log}",
                source=str(self.__class__),
                call_by=call_by,
                method_call=self.__validate_response_text.__name__,
            )
            return False
        return True
