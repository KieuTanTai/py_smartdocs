from dataclasses import asdict
from typing import Any, Dict
from pathlib import Path
from celery import Task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.services.chat.models import DocumentModel
from backend.apps.interfaces.job.i_upload_job import IUploadJob
from backend.apps.interfaces.task.i_document_task import IDocumentTask

class DocumentTask(Task, IDocumentTask): 

    def run(self, document_id: str, provider_name: str) -> Dict[str, Any]:
        container = BackendContainer()
        try:
            provider = EProviderName(provider_name)
        except ValueError as exc:
            raise ValueError(f"Unsupported provider: {provider_name}") from exc

        document = DocumentModel.objects.get(pk=document_id)
        document.status = "processing"
        document.save(update_fields=["status"])

        try:
            if not document.file_path:
                raise ValueError(f"Document {document_id} has no stored file path")
                
            upload_job: IUploadJob = container.upload_job() 
            file_path = Path(document.file_path)
            
            ext_text = upload_job.step_extract(file_path, provider)
            norm_text = upload_job.step_normalize(ext_text)
            chunk_data = upload_job.step_chunk_and_cache(document_id, norm_text)
            
            result_dataclass = upload_job.step_embed_and_save(chunk_data, provider)

            document.status = "indexed"
            document.save(update_fields=["status"])
            
            return asdict(result_dataclass) 
            
        except Exception as exc:
            document.status = "failed"
            document.save(update_fields=["status"])
            raise exc
