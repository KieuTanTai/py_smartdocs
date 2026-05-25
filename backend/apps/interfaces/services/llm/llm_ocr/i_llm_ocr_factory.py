from pathlib import Path
from abc import ABC, abstractmethod

from backend.apps.interfaces.services.llm.llm_ocr.i_llm_ocr import ILLMOCR
from sys_services.enums.e_provider_name import EProviderName


class ILLMOCRFactory(ABC):
    """
    Abstract factory interface for creating OCR extractors.
    Defines method for creating OCR extractor instances.
    """

    @abstractmethod
    def create_ocr_extractor(self, provider_name: EProviderName) -> ILLMOCR:
        """
        Create an OCR extractor instance based on the specified provider name.

        Args:
            provider_name (EProviderName): The name of the OCR provider.

        Returns:
            ILLMOCR: An instance of an OCR extractor that implements the ILLMOCR interface.
        """
        pass
