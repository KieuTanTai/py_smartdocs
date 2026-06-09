from pathlib import Path

from celery import shared_task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.services.chat.models import DocumentModel


#! NOTE: CHANGE TO CLASS AND IMPLE INTERFACE ON 'interfaces/tasks/'
def build_upload_job():
    container = BackendContainer()
    return container.upload_job()


@shared_task
def upload_document_task(document_id: str, provider_name: str = EProviderName.MISTRAL.value):
    try:
        provider = EProviderName(provider_name)
    except ValueError:
        raise ValueError(f"Unsupported provider: {provider_name}")

    document = DocumentModel.objects.get(pk=document_id)
    if document.file_path is None:
        raise ValueError(f"Document {document_id} has no stored file path")

    upload_job = build_upload_job()
    result = upload_job.run(document_id=document_id, file_path=Path(document.file_path), provider=provider)

    document.status = "indexed"
    document.save(update_fields=["status"])

    return result
