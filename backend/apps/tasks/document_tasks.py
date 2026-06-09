"""
Document processing tasks module.
Task implementations for document pipeline:
Extract -> Normalize -> Chunk -> Embed -> Save
"""

import json
from pathlib import Path
from uuid import UUID
from typing import Dict, List, Tuple, Any

import numpy as np
from django.conf import settings

from backend.apps.core.normalize.normalize import Normalize
from backend.apps.core.chunk.chunker import Chunker
from backend.apps.services.chat.models import DocumentModel
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.enums.e_mime_type import EMimeType


from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.services.chat.models import DocumentModel

#! NOTE: INJECT lOGGER BY INIT, NOT CREATE UNNECESSARY INSTANCE,MUST IMPLEMENT INTERFACE ON 'interfaces/tasks/'

class DocumentTaskExecutor:
    """
    Executes document processing pipeline tasks.
    Handles: Extract -> Normalize -> Chunk -> Embed -> Save
    """

    def __init__(self):
        """Initialize document task executor."""
        self.logger = logger
        self.storage_path = Path(settings.MEDIA_ROOT) if hasattr(settings, 'MEDIA_ROOT') else Path('./storage/media')
        self.cache_path = self.storage_path / "cache"
        self.faiss_path = self.storage_path / "faiss"
        
        # Create directories
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.faiss_path.mkdir(parents=True, exist_ok=True)

    def process_document(
        self,
        file_id: UUID,
        file_path: str,
        conversation_id: UUID | None = None,
    ) -> Dict[str, Any]:
        """
        Execute complete document processing pipeline.

        Args:
            file_id: UUID of document
            file_path: Path to file
            conversation_id: Optional conversation ID

        Returns:
            Dictionary with processing results

        Raises:
            Exception: If any stage fails
        """
        try:
            self.logger.info(f"Starting document processing: {file_id}")

            # Stage 1: Extract
            extracted_text = self._extract_content(file_path)
            self.logger.info(f"Extracted text: {len(extracted_text)} characters")

            # Stage 2: Normalize
            normalized_text = self._normalize_content(extracted_text)
            self.logger.info(f"Normalized text: {len(normalized_text)} characters")

            # Stage 3: Chunk + Save Cache + Generate IDs
            chunks_with_ids = self._chunk_and_generate_ids(file_id, normalized_text)
            self.logger.info(f"Created {len(chunks_with_ids)} chunks")

            # Stage 4: Embed (placeholder - requires LLM integration)
            # vectors = self._embed_chunks(chunks_with_ids)
            # self.logger.info(f"Embedded vectors shape: {vectors.shape}")

            # Stage 5: Save FAISS + Metadata
            # file_key = self._save_vectors(file_id, chunks_with_ids, vectors)
            # self.logger.info(f"Saved FAISS index: {file_key}")

            # Update document status
            self._update_document_status(file_id, "indexed", len(chunks_with_ids))

            return {
                "file_id": str(file_id),
                "status": "indexed",
                "chunks_count": len(chunks_with_ids),
                "extracted_chars": len(extracted_text),
                "normalized_chars": len(normalized_text),
            }

        except Exception as e:
            self.logger.error(f"Error processing document {file_id}: {e}")
            self._update_document_status(file_id, "failed")
            raise

    def _extract_content(self, file_path: str) -> str:
        """
        Extract content from file.

        Args:
            file_path: Path to file

        Returns:
            Extracted text content
        """
        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Determine file type
            suffix = file_path_obj.suffix.lower()

            if suffix == ".pdf":
                return self._extract_pdf(file_path)
            elif suffix in [".txt", ".md"]:
                return self._extract_text(file_path)
            elif suffix in [".docx", ".doc"]:
                return self._extract_docx(file_path)
            else:
                return self._extract_text(file_path)

        except Exception as e:
            self.logger.error(f"Error extracting content: {e}")
            raise

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            import pypdf

            text_parts = []
            reader = pypdf.PdfReader(file_path)

            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                except Exception as e:
                    self.logger.warning(f"Error extracting page {page_num}: {e}")

            return "\n".join(text_parts)

        except Exception as e:
            self.logger.error(f"Error extracting PDF: {e}")
            raise

    def _extract_text(self, file_path: str) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"Error extracting text: {e}")
            raise

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text_parts = [para.text for para in doc.paragraphs]
            return "\n".join(text_parts)

        except Exception as e:
            self.logger.error(f"Error extracting DOCX: {e}")
            raise

    def _normalize_content(self, content: str) -> str:
        """
        Normalize extracted content.

        Args:
            content: Raw content text

        Returns:
            Normalized content
        """
        try:
            normalizer = Normalize()
            return normalizer.normalize(content)
        except Exception as e:
            self.logger.error(f"Error normalizing content: {e}")
            raise

    def _chunk_and_generate_ids(
        self, file_id: UUID, normalized_text: str
    ) -> List[Tuple[str, str]]:
        """
        Chunk text and generate IDs.

        Process:
        1. Create chunks using chunker
        2. Generate IDs in format: {file_id}:{chunk_index}
        3. Create tuples: [(chunk_id, chunk_text), ...]
        4. Save to cache as: {file_id}.json

        Args:
            file_id: UUID of file
            normalized_text: Normalized text content

        Returns:
            List of tuples (chunk_id, chunk_text)
        """
        try:
            # Create chunks
            chunker = Chunker(logger=logger)
            chunks = chunker.create_chunks(normalized_text)

            # Generate IDs: file_id:chunk_index (1-indexed)
            chunks_with_ids = []
            chunk_dict = {}

            for idx, chunk_text in enumerate(chunks, start=1):
                chunk_id = f"{file_id}:{idx}"
                chunks_with_ids.append((chunk_id, chunk_text))
                chunk_dict[chunk_id] = chunk_text

            # Save to cache
            cache_file = self.cache_path / f"{file_id}.json"
            cache_data = {
                "file_id": str(file_id),
                "chunks_count": len(chunks),
                "chunks": chunk_dict,
                "persist_path": str(cache_file),
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)

            self.logger.info(f"Saved cache to {cache_file}")

            return chunks_with_ids

        except Exception as e:
            self.logger.error(f"Error chunking document: {e}")
            raise

    def _save_vectors(
        self,
        file_id: UUID,
        chunks_with_ids: List[Tuple[str, str]],
        vectors: np.ndarray,
    ) -> str:
        """
        Save embedding vectors to FAISS.

        Process:
        1. Extract chunk IDs from tuples
        2. Create ids array: np.array(ids, dtype=int64)
        3. Hash vstack result to create file_key
        4. Save FAISS index to file
        5. Save metadata to DB

        Args:
            file_id: UUID of file
            chunks_with_ids: List of (chunk_id, chunk_text) tuples
            vectors: Embedding vectors (np.ndarray)

        Returns:
            file_key (SHA256 hash of vstack)
        """
        try:
            import faiss
            import hashlib

            # Extract chunk IDs
            chunk_ids = np.array([chunk_id for chunk_id, _ in chunks_with_ids], dtype=object)

            # Create file_key as hash of vstack
            vstack_hash = hashlib.sha256(vectors.tobytes()).hexdigest()
            file_key = vstack_hash

            # Create FAISS index
            index = faiss.IndexFlatL2(vectors.shape[1])
            index.add(vectors.astype(np.float32))

            # Save FAISS index
            faiss_file = self.faiss_path / f"{file_key}.faiss"
            faiss.write_index(index, str(faiss_file))

            self.logger.info(f"Saved FAISS index to {faiss_file}")

            # TODO: Update metadata in DB
            # - file_id, file_key, chunks_count, vectors_shape, persist_path

            return file_key

        except Exception as e:
            self.logger.error(f"Error saving vectors: {e}")
            raise

    def _update_document_status(
        self, file_id: UUID, status: str, chunks_count: int = 0
    ) -> None:
        """
        Update document status in database.

        Args:
            file_id: UUID of document
            status: New status
            chunks_count: Number of chunks (for indexed status)
        """
        try:
            document = DocumentModel.objects.get(pk=file_id)
            document.status = status

            if chunks_count > 0:
                # Store metadata (schema limitation - should extend model)
                document.content = f"chunks_count:{chunks_count}"

            document.save()
            self.logger.info(f"Updated document {file_id} status to {status}")

        except DocumentModel.DoesNotExist:
            self.logger.error(f"Document {file_id} not found")
        except Exception as e:
            self.logger.error(f"Error updating document status: {e}")
