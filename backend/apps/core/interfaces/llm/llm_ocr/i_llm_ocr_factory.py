from pathlib import Path
from abc import ABC, abstractmethod

from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr import ILLMOCR


class ILLMOCRFactory(ABC):
    """
    Abstract factory interface for creating OCR extractors.
    Defines method for creating OCR extractor instances.
    """

    @abstractmethod
    def create_ocr_extractor(self) -> ILLMOCR:
        """
        Create an OCR extractor instance based on the specified provider name.

        Args:
            provider_name (EProviderName): The name of the OCR provider.

        Returns:
            ILLMOCR: An instance of an OCR extractor that implements the ILLMOCR interface.
        """
        pass
