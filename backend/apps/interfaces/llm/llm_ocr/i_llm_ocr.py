from pathlib import Path
from abc import ABC, abstractmethod
from backend.apps.interfaces.conversation.i_completion import ICompletionResponse
from backend.apps.interfaces.storage.i_create_file_response import ICreateFileResponse


class ILLMOCR(ABC):
    """
    Abstract interface for OCR (Optical Character Recognition) services.
    Defines method for extracting text from images.
    """

    @abstractmethod
    async def process_ocr(
        self, uploaded_pdf: ICreateFileResponse
    ) -> ICompletionResponse:
        """Process OCR on the uploaded PDF file and return extracted text."""
        pass
