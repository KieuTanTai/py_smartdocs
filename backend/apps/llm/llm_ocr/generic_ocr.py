from pathlib import Path
from typing import Dict, Any
from pypdf import PdfReader
import io
from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
from backend.apps.core.interfaces.services.rag_base.storage.i_create_file_response import (
    ICreateFileResponse,
)
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr import ILLMOCR
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.dataclass.ocr.i_ocr_response import IOCRResponse, OCRPage, OCRUsageInfo

class GenericOCR(ILLMOCR):
    """Generic OCR implementation using pypdf for document extraction.
    This serves as a fallback for providers that don't have dedicated OCR support."""

    def __init__(
        self,
        provider_name: str,
        logger: ILogger,
        storage_dir: Path,
    ):
        self.provider_name = provider_name
        self.logger = logger
        self.storage_dir = storage_dir

    def process_ocr(
        self, uploaded_pdf: ICreateFileResponse, call_by: str = ""
    ) -> IOCRResponse:
        """Process OCR on the uploaded document using pypdf."""
        self.logger.info(
            f"Starting generic OCR process for file ID: {uploaded_pdf.id} with provider: {self.provider_name}",
            source=str(self.__class__),
            call_by=call_by,
            method_call=self.process_ocr.__name__,
        )
        try:
            # Find the file in storage directory
            file_path = self.__find_file_in_storage(uploaded_pdf.filename, call_by=call_by)
            
            # Read the file content
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Determine file type and extract text
            mime_type = self.__get_mime_type(uploaded_pdf, call_by=call_by)
            
            if mime_type == "application/pdf":
                extracted_text = self.__extract_from_pdf(file_bytes, call_by=call_by)
            elif mime_type == "text/plain":
                extracted_text = file_bytes.decode('utf-8', errors='ignore')
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                # For DOCX, we'll try to extract text using python-docx if available
                try:
                    import docx
                    doc = docx.Document(io.BytesIO(file_bytes))
                    extracted_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    self.logger.warning(
                        f"python-docx not available, falling back to raw text extraction",
                        source=str(self.__class__), call_by=call_by
                    )
                    extracted_text = file_bytes.decode('utf-8', errors='ignore')
            else:
                # Fallback: try to decode as text
                extracted_text = file_bytes.decode('utf-8', errors='ignore')
            
            # Create response
            pages = [OCRPage(markdown=extracted_text, page_number=1)]
            usage_info = OCRUsageInfo(pages_processed=1, doc_size_bytes=len(file_bytes))
            
            ocr_response = IOCRResponse(
                model=f"generic-{self.provider_name}",
                pages=pages,
                usage_info=usage_info,
                id=uploaded_pdf.id,
                created_at=None
            )
            
            self.logger.info(
                f"Generic OCR process completed successfully for file ID: {uploaded_pdf.id}",
                source=str(self.__class__), call_by=call_by, method_call=self.process_ocr.__name__
            )
            return ocr_response
            
        except Exception as e:
            self.logger.error(
                f"Error during generic OCR processing for file ID: {uploaded_pdf.id} - {e}",
                source=str(self.__class__), call_by=call_by, method_call=self.process_ocr.__name__
            )
            raise e

    def __find_file_in_storage(self, filename: str, call_by: str = "") -> Path:
        """Find the file in the storage directory."""
        # Search in common subdirectories
        search_dirs = [
            self.storage_dir,
            self.storage_dir / "pdf",
            self.storage_dir / "docx",
            self.storage_dir / "txt",
        ]
        
        for search_dir in search_dirs:
            if search_dir.exists():
                file_path = search_dir / filename
                if file_path.exists():
                    return file_path
                    
                # Try to find by pattern if exact match fails
                for file in search_dir.glob(f"*{filename}*"):
                    if file.is_file():
                        return file
        
        # If not found, raise error
        raise FileNotFoundError(f"File {filename} not found in storage directory {self.storage_dir}")

    def __extract_from_pdf(self, file_bytes: bytes, call_by: str = "") -> str:
        """Extract text from PDF using pypdf."""
        try:
            pdf_reader = PdfReader(io.BytesIO(file_bytes))
            text_parts = []
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                if text:
                    text_parts.append(f"# Page {page_num}\n\n{text}")
            
            return "\n\n".join(text_parts)
        except Exception as e:
            self.logger.error(
                f"Error extracting text from PDF: {e}",
                source=str(self.__class__), call_by=call_by, method_call=self.__extract_from_pdf.__name__
            )
            raise e

    def __get_mime_type(self, file_response: ICreateFileResponse, call_by: str = "") -> str:
        """Get the MIME type of the file."""
        if hasattr(file_response, "mimetype"):
            return str(file_response.mimetype)
        else:
            self.logger.warning(
                f"File response does not have 'mimetype' attribute. Defaulting to 'application/pdf'.",
                source=str(self.__class__), call_by=call_by, method_call=self.__get_mime_type.__name__
            )
            return "application/pdf"
