from pathlib import Path
from abc import ABC, abstractmethod

from backend.apps.interfaces.llm.llm_ocr.i_llm_ocr import ILLMOCR

class ILLMOCRFactory(ABC):
    """
    Abstract factory interface for creating OCR extractors.
    Defines method for creating OCR extractor instances.
    """
    
    @abstractmethod
    def create_ocr_extractor(self) -> ILLMOCR:
        pass