"""
Celery tasks for background processing.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from celery import shared_task
from django.db import close_old_connections

from backend.apps.services.chat.models import DocumentModel
from backend.apps.core.normalize.normalize import Normalize
from backend.apps.core.chunk.chunker import Chunker
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.services.rag_base.locate.locate_service import LocateService
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.system_dirs import METADATA_DIR
#! NOTE: THIS VALUES SHOULD BE GET FROM GET_CONFIG, NOT HARDCODED
#! NOTE: INJECT LOGGER BY INIT, CHANGE TO CLASS, IMPLEMENT INTERFACE ON 'interfaces/tasks/'

_INDEX_EMBEDDING_PROVIDER = EProviderName.GEMINI
_INDEX_EMBEDDING_MODEL = "gemini-embedding-2"


def _extract_text(file_path: str) -> str:
    """Extract text from PDF, DOCX, or plain text file."""
    if not file_path or not os.path.exists(file_path):
        return ""

    if file_path.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception as e:
            DEFAULT_LOGGER.error(f"PDF extraction failed: {e}", source="celery._extract_text")
            return ""

    elif file_path.endswith(".docx"):
        try:
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(file_path) as docx:
                root = ET.fromstring(docx.read("word/document.xml"))
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                return "\n".join(
                    "".join(t.text or "" for t in p.findall(".//w:t", ns))
                    for p in root.findall(".//w:p", ns)
                )
        except Exception as e:
            DEFAULT_LOGGER.error(f"DOCX extraction failed: {e}", source="celery._extract_text")
            return ""

    else:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""


def _embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Embed all chunks using the configured embedding provider."""
    factory = LLMProviderFactory(DEFAULT_CONFIG_PROVIDER, DEFAULT_LOGGER)
    client = factory.get_provider(_INDEX_EMBEDDING_PROVIDER)
    embeddings = []
    for chunk in chunks:
        req = ICompletionRequest(
            provider=_INDEX_EMBEDDING_PROVIDER,
            model=_INDEX_EMBEDDING_MODEL,
            prompt=chunk,
        )
        resp = client.embedding(req)
        embeddings.append(resp.embedding.tolist())
    return embeddings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def index_document(self, document_id: str) -> dict:
    """
    Celery task: index a single document asynchronously.
    Replaces the synchronous DocumentIndexView.post() pipeline.
    """
    close_old_connections()
    try:
        doc = DocumentModel.objects.get(pk=document_id)
    except DocumentModel.DoesNotExist:
        return {"error": "Document not found", "document_id": document_id}

    doc.status = "processing"
    doc.save()

    try:
        # 1. Extract
        extracted_text = _extract_text(doc.file_path or "")
        if not extracted_text.strip():
            raise ValueError("No text could be extracted from the document.")

        # 2. Normalize
        normalizer = Normalize()
        normalized_text = normalizer.normalize(extracted_text)

        # 3. Chunk
        chunker = Chunker(logger=DEFAULT_LOGGER)
        chunks = chunker.create_chunks(normalized_text)
        if not chunks:
            raise ValueError("No chunks generated from document.")

        # 4. Embed
        embeddings = _embed_chunks(chunks)
        vectors = np.array(embeddings, dtype=np.float32)

        # 5. FAISS
        vector_id = str(doc.faiss_index_id)
        locate_service = LocateService(metadata_dir=METADATA_DIR, logger=DEFAULT_LOGGER)
        faiss_service = locate_service.get_vector_store(EBackendStorageName.FAISS)
        index = faiss_service.create_index(vectors)
        faiss_service.upsert(index=index, vector_id=vector_id)

        # 6. Save chunk metadata
        chunk_metadata = {str(idx): chunk_text for idx, chunk_text in enumerate(chunks)}
        metadata_path = METADATA_DIR / "docs" / f"{vector_id}.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump({
                "document_id": vector_id,
                "file_name": doc.faiss_index_file_name,
                "chunk_count": len(chunks),
                "embedding_model": _INDEX_EMBEDDING_MODEL,
                "embedding_dimensions": vectors.shape[1],
                "chunks": chunk_metadata,
            }, f, ensure_ascii=False, indent=2)

        # 7. Update DB
        doc.content = normalized_text
        doc.status = "indexed"
        doc.save()

        DEFAULT_LOGGER.info(
            f"Celery indexed document {doc.faiss_index_file_name} "
            f"({len(chunks)} chunks, dim={vectors.shape[1]})",
            source="celery.index_document",
        )
        return {
            "document_id": document_id,
            "status": "indexed",
            "chunks": len(chunks),
            "dimensions": vectors.shape[1],
        }

    except Exception as exc:
        DEFAULT_LOGGER.error(
            f"Celery indexing failed for {document_id}: {exc}",
            source="celery.index_document",
        )
        doc.status = "failed"
        doc.save()
        raise self.retry(exc=exc)


@shared_task(bind=True)
def bulk_index_documents(self, document_ids: list[str]) -> dict:
    """
    Celery task: index multiple documents in sequence.
    Replaces the synchronous DocumentBulkIndexView.post() endpoint.
    """
    close_old_connections()
    results = []
    for doc_id in document_ids:
        try:
            result = index_document.delay(doc_id)
            results.append({"document_id": doc_id, "celery_task_id": result.id, "status": "queued"})
        except Exception as exc:
            results.append({"document_id": doc_id, "error": str(exc), "status": "failed"})

    return {
        "total": len(document_ids),
        "results": results,
    }
