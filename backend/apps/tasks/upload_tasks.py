"""
Upload tasks module.
Handles the execution flow for uploaded files via background workers.
"""

from dataclasses import asdict
from typing import Any, Dict, List
from pathlib import Path
from celery import Task

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.dataclass.tasks.i_embed_and_save_response import IEmbedResponse
from backend.apps.services.chat.models import DocumentModel
from backend.apps.interfaces.task.i_upload_task import IUploadTask
from backend.apps.interfaces.job.i_upload_job import IUploadJob

class UploadTask(Task, IUploadTask):

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

    def __get_valid_file_path(self, document: DocumentModel) -> List[Path]:
        """Validate and get paths of a document. Supports multiple files."""
        if not document.file_path:
            self.logger.error(f"Document {document.pk} has no stored file path", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__get_valid_file_path.__name__)
            raise ValueError(f"Document {document.pk} has no stored file path")
        paths = []
        
        if isinstance(document.file_path, list):
            paths = [Path(p) for p in document.file_path]
        elif isinstance(document.file_path, str):
            paths = [Path(p.strip()) for p in document.file_path.split(',')]
            
        if not paths:
            raise ValueError(f"Document {document.pk} has invalid file paths")
        
        return paths

    def __execute_pipeline(self, upload_job: IUploadJob, document_id: str, file_path: List[Path], provider: EProviderName) -> IEmbedResponse:
        """Run the Upload pipeline."""
        
        ext_text = upload_job.step_extract(file_path, provider, file_caller=self.__execute_pipeline.__name__)
        self.logger.info(f"Document {document_id} extracted text successfully with {len(ext_text)} characters", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__execute_pipeline.__name__)
        
        norm_text = upload_job.step_normalize(ext_text, file_caller=self.__execute_pipeline.__name__)
        self.logger.info(f"Document {document_id} normalized text successfully with {len(norm_text)} characters", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__execute_pipeline.__name__)
        
        chunk_data = upload_job.step_chunk_and_cache(document_id, norm_text, file_caller=self.__execute_pipeline.__name__)
        self.logger.info(f"Document {document_id} chunked into {len(chunk_data.chunk_texts)} chunks", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__execute_pipeline.__name__)
        
        embed_res = upload_job.step_embed(chunk_data, provider, file_caller=self.__execute_pipeline.__name__)
        self.logger.info(f"Document {document_id} embedded successfully with {len(embed_res.embeded_metadata)} embeddings", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__execute_pipeline.__name__)
        
        save_res = upload_job.step_save(
            provider=provider,
            document_ids=[document_id],
            embed_responses=embed_res.embeded_metadata,
            chunk_texts=chunk_data.chunk_texts,
            file_caller=self.__execute_pipeline.__name__
        )
        self.logger.info(f"Document {document_id} saved to vector store successfully", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.__execute_pipeline.__name__)
        
        try:
            upload_job.step_build_knowledge_graph(
                document_id=document_id,
                extracted_texts=ext_text,
                provider=provider,
                model_name="qwen2.5:1.5b-instruct",
                file_caller=self.__execute_pipeline.__name__
            )
        except Exception as e:
            self.logger.error(f"Graph RAG failed but vector search saved. Error: {e}", source=Path(__file__).name, call_by=Path(__file__).name)

        return save_res

    # --- MAIN ENTRY POINT ---
    @property
    def name(self) -> str:
        """Return the task name for routing."""
        self.logger.info(f"Retrieving task name for routing", source=Path(__file__).name, call_by=Path(__file__).name, method_call=self.name)
        return Path(__file__).stem  # Dynamic name based on filename

    def run(self, document_id: str, provider_name: EProviderName, file_caller: str = "") -> IEmbedResponse:
        """Run the upload task."""
        self.logger.info(f"Starting UploadTask for document {document_id} with provider {provider_name} called by {file_caller}", source=Path(__file__).name, call_by=file_caller, method_call=self.run.__name__)
        try:
            document = self.__update_document_status(document_id, "processing")
            file_paths = self.__get_valid_file_path(document)
            # Chạy luồng lõi
            self.logger.info(f"Executing RAG pipeline for document {document_id}", source=Path(__file__).name, call_by=file_caller, method_call=self.run.__name__)
            result_dataclass = self.__execute_pipeline(self.upload_job, document_id, file_paths, provider_name)

            self.__update_document_status(document_id, "indexed")
            return result_dataclass
            
        except Exception as exc:
            self.logger.error(f"Error processing document {document_id}: {exc}", source=Path(__file__).name, call_by=file_caller, method_call=self.run.__name__)
            self.__update_document_status(document_id, "failed")
            raise exc