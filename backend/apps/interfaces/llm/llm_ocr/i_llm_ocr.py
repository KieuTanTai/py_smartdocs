from pathlib import Path
from abc import ABC, abstractmethod

class ILLMOCR(ABC):
    """
    Abstract interface for OCR (Optical Character Recognition) services.
    Defines method for extracting text from images.
    """
    
    @abstractmethod
    async def extract_text_from_image(self, image_path: Path) -> str:
        """
        Extract text from image using OCR.

        Args:
            image_path: Path to the image file

        Returns:
            Extracted text as a string
        """
        pass

    @abstractmethod
    async def extract_text_from_document(self, document_path: Path) -> str:
        """
        Extract text from document using OCR.

        Args:
            document_path: Path to the document file

        Returns:
            Extracted text as a string
        """
        pass
