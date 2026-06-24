from pathlib import Path
from abc import ABC, abstractmethod
from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.dataclass.ocr.i_ocr_response import IOCRResponse

class ILLMOCR(ABC):
    """
    Abstract interface for OCR (Optical Character Recognition) services.
    Defines method for extracting text from images.
    """

    @abstractmethod
    def process_ocr(
        self, uploaded_pdf: ICreateFileResponse, call_by: str = ""
    ) -> IOCRResponse:
        """Process OCR on the uploaded PDF file and return extracted text."""
        pass
