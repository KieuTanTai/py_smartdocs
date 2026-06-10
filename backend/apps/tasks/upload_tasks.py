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
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.tasks.i_embed_and_save_response import IEmbedAndSaveResponse
from backend.apps.services.chat.models import DocumentModel
from backend.apps.interfaces.task.i_upload_task import IUploadTask
from backend.apps.interfaces.job.i_upload_job import IUploadJob

class UploadTask(Task, IUploadTask): # <--- Class UploadTask chuẩn chỉ

    def __init__(self, upload_job: IUploadJob, logger: ILogger):
        self.upload_job = upload_job
        self.logger = logger

    # --- SINGLE RESPONSIBILITY METHODS ---

    def __update_document_status(self, document_id: str, status: str) -> DocumentModel:
        """Update status of a document."""
        document = DocumentModel.objects.get(pk=document_id)
        document.status = status
        document.save(update_fields=["status"])
        self.logger.info(f"Document {document_id} status updated to {status}", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__update_document_status.__name__)
        return document

    def __get_valid_file_path(self, document: DocumentModel) -> Path:
        """Validate and get path of a document."""
        if not document.file_path:
            self.logger.error(f"Document {document.pk} has no stored file path", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__get_valid_file_path.__name__)
            raise ValueError(f"Document {document.pk} has no stored file path")
        return Path(document.file_path)

    def __execute_pipeline(self, upload_job: IUploadJob, document_id: str, file_path: Path, provider: EProviderName) -> IEmbedAndSaveResponse:
        """Run the Upload pipeline."""
        ext_text = upload_job.step_extract(file_path, provider, file_caller=self.__execute_pipeline.__name__)
        self.logger.info(f"Document {document_id} extracted text successfully with {len(ext_text)} characters", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__execute_pipeline.__name__)
        norm_text = upload_job.step_normalize(ext_text, file_caller=self.__execute_pipeline.__name__)
        self.logger.info(f"Document {document_id} normalized text successfully with {len(norm_text)} characters", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__execute_pipeline.__name__)
        chunk_data = upload_job.step_chunk_and_cache(document_id, norm_text, file_caller=self.__execute_pipeline.__name__)
        self.logger.info(f"Document {document_id} chunked into {len(chunk_data.chunk_texts)} chunks", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__execute_pipeline.__name__)
        return upload_job.step_embed_and_save(chunk_data, provider)

    # --- MAIN ENTRY POINT ---
    @property
    def name(self) -> str:
        """Return the task name for routing."""
        self.logger.info(f"Retrieving task name for routing", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.name)
        return Path(__file__).stem  # Dynamic name based on filename

    def run(self, document_id: str, provider_name: EProviderName, file_caller: str = "") -> IEmbedAndSaveResponse:
        """Run the upload task."""
        self.logger.info(f"Starting UploadTask for document {document_id} with provider {provider_name} called by {file_caller}", source=Path(__file__).name, call_by=file_caller, method_call=self.run.__name__)
        try:
            document = self.__update_document_status(document_id, "processing")
            file_path = self.__get_valid_file_path(document)
            # Chạy luồng lõi
            self.logger.info(f"Executing RAG pipeline for document {document_id}", source=Path(__file__).name, call_by=file_caller, method_call=self.run.__name__)
            result_dataclass = self.__execute_pipeline(self.upload_job, document_id, file_path, provider_name)

            self.__update_document_status(document_id, "indexed")
            return result_dataclass
            
        except Exception as exc:
            self.logger.error(f"Error processing document {document_id}: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.run.__name__)
            self.__update_document_status(document_id, "failed")
            raise exc