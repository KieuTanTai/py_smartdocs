import os
from pathlib import Path

from backend.apps.interfaces.base_rag.extract.i_ocr_response import IOCRResponse
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.logging import DEFAULT_LOGGER
from mistralai.client import Mistral
from backend.apps.utils.is_content_empty import check_empty_content
from backend.apps.interfaces.base_rag.extract.i_extract_content import IExtractContent

class MistralOCRExtractor(IExtractContent):

    logger = DEFAULT_LOGGER

    async def extract_from_file_text(self, file_path: Path) -> IOCRResponse:
        
