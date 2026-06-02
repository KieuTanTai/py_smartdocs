from langchain_text_splitters import NLTKTextSplitter
from backend.apps.core.interfaces.core.chunk.i_chunking import IChunking
from backend.apps.core.interfaces.system.i_logging import ILogger


class Chunker(IChunking):
    def __init__(
        self,
        logger: ILogger,
        chunk_size: int = 1000,
        overlap: int = 200,
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.logger = logger

    def create_chunks(self, normalized_document: str) -> list[str]:
        try:
            text_splitter = NLTKTextSplitter(
                chunk_size=self.chunk_size, chunk_overlap=self.overlap
            )
            chunks = text_splitter.split_text(normalized_document)
            if len(chunks) == 0:
                self.logger.warning(
                    "No chunks were created from the document. This will fallback to manual chunking.",
                    source=str(self.__class__),
                )
                chunks = self.__chunk_by_size(
                    normalized_document, self.chunk_size, self.overlap
                )
        except Exception as e:
            self.logger.error(
                f"Error occurred while creating chunks: {e}",
                source=str(self.__class__),
            )
            raise ValueError(f"Error occurred while creating chunks: {e}")
        self.logger.info(
            f"Created {len(chunks)} chunks from the document.",
            source=str(self.__class__),
        )
        return chunks

    def __chunk_by_size(self, text, chunk_size, overlap) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start += self.chunk_size - self.overlap
        return chunks
