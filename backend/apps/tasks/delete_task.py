from pathlib import Path
from celery import Task

from backend.apps.interfaces.job.i_delete_job import IDeleteJob
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.time_counter import TimeCounter

class DeleteTask(Task):
    def __init__(self, delete_job: IDeleteJob, logger: ILogger, time_counter: TimeCounter):
        self.delete_job = delete_job
        self.logger = logger
        self.time_counter = time_counter

    @property
    def name(self) -> str:
        return "delete_task"

    def run(self, document_id: str, file_id: str = None, file_caller: str = "") -> dict:
        self.logger.info(f"Starting DeleteTask for document {document_id} called by {file_caller}")
        
        self.time_counter.reset()
        self.time_counter.start()
        try:
            # Chạy qua 3 bước dọn dẹp
            self.delete_job.step_clear_cache(document_id, file_caller=self.run.__name__)
            self.delete_job.step_delete_vectors(document_id, file_caller=self.run.__name__)
            self.delete_job.step_delete_graph_data(document_id, file_caller=self.run.__name__)
            
            # Xóa Cloud File
            target_cloud_id = file_id if file_id else document_id
            self.delete_job.step_delete_cloud_file(target_cloud_id, file_caller=self.run.__name__)
            
            self.time_counter.stop()
            elapsed = self.time_counter.get_elapsed_time_ms()
            self.logger.info(f"DeleteTask completed successfully in {elapsed:.2f}ms for document {document_id}")
            
            return {
                "status": "success", 
                "document_id": document_id, 
                "message": "All RAG data completely removed."
            }
        except Exception as exc:
            self.logger.error(f"Error deleting RAG data for document {document_id}: {exc}")
            # Nếu database chết giữa chừng, Celery sẽ thử lại (retry)
            self.retry(exc=exc, countdown=30, max_retries=3)