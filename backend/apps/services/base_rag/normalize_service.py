import re
from pathlib import Path

from sys_services.logging import DEFAULT_LOGGER
from backend.apps.utils.is_content_empty import check_empty_content

logger = DEFAULT_LOGGER


class Normalize:
    @staticmethod
    def normalize_markdown(content: str) -> str:
        normalized_content = content.strip()
        normalized_content = re.sub(r"\n+", "\n", normalized_content)
        normalized_content = re.sub(r"[ \t]+", " ", normalized_content)
        return normalized_content

    @staticmethod
    def normalize_markdown_file(content: str, index: str) -> tuple[str, str]:
        source_log = f"{Path(__file__).parent.absolute()}/{Path(__file__).name}"
        if not check_empty_content(content, source_log):
            raise ValueError(
                f"Input content is empty for index {index}. Cannot normalize empty content."
            )
        normalized_content = Normalize.normalize_markdown(content)
        try:
            if not check_empty_content(normalized_content, source_log):
                raise ValueError(
                    f"Normalized content is empty for index {index}. Cannot write empty content to file."
                )
            logger.info(
                f"Normalized content for index {index} is not empty. Proceeding to write to file.",
                source=source_log,
            )
            return normalized_content, index
        except Exception as e:
            logger.error(
                f"An error occurred while writing normalized content to file: {e}",
                source=source_log,
            )
            raise Exception(
                f"An error occurred while writing normalized content to file: {e}"
            )
