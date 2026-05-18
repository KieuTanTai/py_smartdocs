from pathlib import Path
import nltk
from langchain_text_splitters import NLTKTextSplitter

from backend.apps.utils.is_content_empty import check_empty_contents
from sys_services.logging import DEFAULT_LOGGER

logger = DEFAULT_LOGGER


class Chunking:
    @staticmethod
    def chunk_text_by_token(
        text: str, chunk_size: int, chunk_overlap: int
    ) -> list[str]:
        source_log = f"{Path(__file__).parent.absolute()}/{Path(__file__).name}"
        try:
            text_splitter = NLTKTextSplitter(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
            result = text_splitter.split_text(text)
            if not check_empty_contents(result, source_log):
                raise ValueError(
                    "Chunking resulted in empty content. This may indicate an issue with the chunking process."
                )
            logger.info(
                f"Chunking resulted in {len(result)} chunks. Proceeding with the next steps.",
                source=source_log,
            )
            return result
        except LookupError as e:
            logger.error(
                f"Error occurred while downloading NLTK data: {e}",
                source=source_log,
            )
            nltk.download("punkt_tab")
            return Chunking.chunk_text_by_token(text, chunk_size, chunk_overlap)
        except Exception as e:
            logger.error(
                f"An unexpected error occurred: {e}",
                source=source_log,
            )
            raise e
