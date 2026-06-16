from pathlib import Path
from celery import Task

from backend.apps.interfaces.job.i_delete_job import IDeleteJob
from backend.apps.core.interfaces.system.i_logging import ILogger

class DeleteTask(Task):
    def __init__(self, delete_job: IDeleteJob, logger: ILogger):
        self.delete_job = delete_job
        self.logger = logger

    @property
    def name(self) -> str:
        return "delete_task"

    def run(self, document_id: str, file_caller: str = "") -> dict:
        self.logger.info(f"Starting DeleteTask for document {document_id} called by {file_caller}")
        try:
            # Chạy qua 3 bước dọn dẹp
            self.delete_job.step_clear_cache(document_id, file_caller=self.run.__name__)
            self.delete_job.step_delete_vectors(document_id, file_caller=self.run.__name__)
            self.delete_job.step_delete_graph_data(document_id, file_caller=self.run.__name__)
            
            return {
                "status": "success", 
                "document_id": document_id, 
                "message": "All RAG data completely removed."
            }
        except Exception as exc:
            self.logger.error(f"Error deleting RAG data for document {document_id}: {exc}")
            # Nếu database chết giữa chừng, Celery sẽ thử lại (retry)
            self.retry(exc=exc, countdown=30, max_retries=3)