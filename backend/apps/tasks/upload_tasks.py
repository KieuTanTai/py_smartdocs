"""
Upload tasks module.
Handles the execution flow for uploaded files via background workers.
"""

from dataclasses import asdict
from typing import Any, Dict
from pathlib import Path
from celery import Task

from backend.apps.config.container import BackendContainer
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.job.i_dataclass_upload_job import EmbedAndSaveResponse
from backend.apps.services.chat.models import DocumentModel
from backend.apps.interfaces.task.i_upload_task import IUploadTask
from backend.apps.interfaces.job.i_upload_job import IUploadJob

class UploadTask(Task, IUploadTask): # <--- Class UploadTask chuẩn chỉ

    # --- SINGLE RESPONSIBILITY METHODS ---

    def _get_container(self) -> BackendContainer:
        """Lấy Dependency Container sạch cho Worker."""
        return BackendContainer()

    def _resolve_provider(self, provider_name: str) -> EProviderName:
        """Parse và Validate Provider Enum."""
        try:
            return EProviderName(provider_name)
        except ValueError as exc:
            raise ValueError(f"Unsupported provider: {provider_name}") from exc

    def _update_document_status(self, document_id: str, status: str) -> DocumentModel:
        """Cập nhật trạng thái DB độc lập."""
        document = DocumentModel.objects.get(pk=document_id)
        document.status = status
        document.save(update_fields=["status"])
        return document

    def _get_valid_file_path(self, document: DocumentModel) -> Path:
        """Kiểm tra và lấy đường dẫn file vật lý."""
        if not document.file_path:
            raise ValueError(f"Document {document.pk} has no stored file path")
        return Path(document.file_path)

    def _execute_pipeline(self, upload_job: IUploadJob, document_id: str, file_path: Path, provider: EProviderName) -> EmbedAndSaveResponse:
        """Chạy quy trình RAG tuần tự thông qua Job."""
        ext_text = upload_job.step_extract(file_path, provider)
        norm_text = upload_job.step_normalize(ext_text)
        chunk_data = upload_job.step_chunk_and_cache(document_id, norm_text)
        return upload_job.step_embed_and_save(chunk_data, provider)

    # --- MAIN ENTRY POINT ---

    def run(self, document_id: str, provider_name: str) -> Dict[str, Any]:
        """Điều phối các hàm nhỏ để hoàn thành vòng đời Task."""
        container = self._get_container()
        provider = self._resolve_provider(provider_name)
        document = self._update_document_status(document_id, "processing")

        try:
            file_path = self._get_valid_file_path(document)
            upload_job: IUploadJob = container.upload_job()
            
            # Chạy luồng lõi
            result_dataclass = self._execute_pipeline(upload_job, document_id, file_path, provider)

            self._update_document_status(document_id, "indexed")
            
            return asdict(result_dataclass)
            
        except Exception as exc:
            self._update_document_status(document_id, "failed")
            raise exc