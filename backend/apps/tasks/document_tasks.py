"""
Document tasks module.
Celery tasks for document processing.
"""

from pathlib import Path

from celery import shared_task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.services.chat.models import DocumentModel


def _build_upload_job():
    container = BackendContainer()
    return container.upload_job()


def _resolve_provider(provider_name: str) -> EProviderName:
    try:
        return EProviderName(provider_name)
    except ValueError as exc:
        raise ValueError(f"Unsupported provider: {provider_name}") from exc


def _get_document(document_id: str) -> DocumentModel:
    return DocumentModel.objects.get(pk=document_id)


def _run_upload_job(document_id: str, provider: EProviderName) -> dict:
    document = _get_document(document_id)
    if not document.file_path:
        raise ValueError(f"Document {document_id} does not have a saved file path")
    upload_job = _build_upload_job()
    return upload_job.run(document_id=document_id, file_path=Path(document.file_path), provider=provider)


@shared_task
def upload_document_task(document_id: str, provider_name: str = EProviderName.MISTRAL.value):
    provider = _resolve_provider(provider_name)

    document = _get_document(document_id)
    document.status = "processing"
    document.save(update_fields=["status"])

    try:
        result = _run_upload_job(document_id, provider)
        document.status = "indexed"
        document.save(update_fields=["status"])
        return result
    except Exception as exc:
        document.status = "failed"
        document.save(update_fields=["status"])
        raise exc


@shared_task
def process_document(document_id: str, provider_name: str = EProviderName.MISTRAL.value):
    return upload_document_task(document_id, provider_name)


@shared_task
def normalize_document(document_id: str, raw_text: str):
    container = BackendContainer()
    normalizer = container.normalize()
    return normalizer.normalize(raw_text)


@shared_task
def chunk_document(document_id: str, normalized_text: str):
    container = BackendContainer()
    chunker = container.chunker()
    return chunker.create_chunks(normalized_text)


@shared_task
def index_document(document_id: str, chunk_texts, provider_name: str = EProviderName.MISTRAL.value):
    provider = _resolve_provider(provider_name)
    document = _get_document(document_id)
    if not document.file_path:
        raise ValueError(f"Document {document_id} does not have a saved file path")

    upload_job = _build_upload_job()
    return upload_job.run(document_id=document_id, file_path=Path(document.file_path), provider=provider)


@shared_task
def summarize_document(document_id: str):
    document = _get_document(document_id)
    return {
        "document_id": document_id,
        "status": document.status,
        "summary": None,
    }
