"""
Custom OCR Response dataclasses to replace mistralai.OCRResponse.
These dataclasses define the structure of OCR responses independently of the mistralai SDK version.
"""
from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class OCRUsageInfo:
    """Usage information from OCR processing."""
    pages_processed: int
    doc_size_bytes: Optional[int] = None


@dataclass
class OCRPage:
    """Single page from OCR response."""
    markdown: str
    page_number: Optional[int] = None


@dataclass
class IOCRResponse:
    """
    Custom OCR Response interface.
    Replaces mistralai.OCRResponse to be independent of SDK version.
    """
    model: str
    pages: List[OCRPage]
    usage_info: OCRUsageInfo
    object: str = "ocr_response"
    id: Optional[str] = None
    created_at: Optional[int] = None
