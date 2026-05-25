from pathlib import Path

from backend.apps.interfaces.services.chat.i_completion import ICompletionResponse
from backend.apps.interfaces.services.rag_base.extract.i_extract_content import (
    IExtractContent,
)
from backend.apps.interfaces.core.extract.i_extractor import IExtractor
from backend.apps.utils.mime_type import get_mime_type_from_path
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER
from sys_services.enums.e_mime_type import EMimeType


class Extractor(IExtractor):
    def __init__(
        self,
        extractor: IExtractContent,
        logger: ILogger | None = None,
    ):
        self.extractor = extractor
        self.logger = logger or DEFAULT_LOGGER

    async def extract(self, file_path: Path) -> ICompletionResponse:
        mime_type = get_mime_type_from_path(file_path)
        if mime_type in {
            EMimeType.JPEG.value,
            EMimeType.PNG.value,
            EMimeType.JPG.value,
            EMimeType.TIFF.value,
        }:
            return await self.extractor.extract_from_file_image(file_path)

        return await self.extractor.extract_from_file_text(file_path)
