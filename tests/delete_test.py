import pytest
from unittest.mock import MagicMock


from backend.apps.interfaces.job.i_delete_job import IDeleteJob
from backend.apps.tasks.delete_task import DeleteTask

# ==========================================
# TEST 1: LUỒNG XÓA THÀNH CÔNG
# ==========================================
def test_delete_task_success():
    """Kiểm tra Task gọi đủ 3 bước xóa RAG (Cache, Vector, Graph) khi thành công"""
    
    # SETUP MOCKS (Giả lập môi trường)
    mock_logger = MagicMock()
    mock_delete_job = MagicMock(spec=IDeleteJob)
    
    # Giả lập các hàm chạy thành công
    mock_delete_job.step_clear_cache.return_value = True
    mock_delete_job.step_delete_vectors.return_value = True
    mock_delete_job.step_delete_graph_data.return_value = True

    # KHỞI TẠO TASK CẦN TEST
    task = DeleteTask(delete_job=mock_delete_job, logger=mock_logger)
    
    # KÍCH HOẠT CHẠY THỰC TẾ
    document_id = "doc_cleanup_123"
    result = task.run(document_id=document_id, file_caller="Test")

    # KIỂM CHỨNG (ASSERTIONS)
    # Đảm bảo Cache được xóa đầu tiên (hoặc gọi đúng tham số)
    mock_delete_job.step_clear_cache.assert_called_once_with(
        document_id, file_caller=task.run.__name__
    )
    
    # Đảm bảo FAISS/BM25 Vector được xóa
    mock_delete_job.step_delete_vectors.assert_called_once_with(
        document_id, file_caller=task.run.__name__
    )
    
    # Đảm bảo Neo4j Graph được xóa
    mock_delete_job.step_delete_graph_data.assert_called_once_with(
        document_id, file_caller=task.run.__name__
    )
    
    # Đảm bảo kết quả trả về đúng chuẩn JSON yêu cầu
    assert result == {
        "status": "success", 
        "document_id": document_id, 
        "message": "All RAG data completely removed."
    }

# ==========================================
# TEST 2: LUỒNG LỖI VÀ RETRY (THỬ LẠI)
# ==========================================
def test_delete_task_retry_on_failure():
    """Kiểm tra Task có kích hoạt Celery Retry khi Database gặp sự cố không"""
    
    # SETUP MOCKS
    mock_logger = MagicMock()
    mock_delete_job = MagicMock(spec=IDeleteJob)
    
    # Giả lập việc xóa Vector bị lỗi (Ví dụ: FAISS đang bị lock)
    test_exception = Exception("FAISS is locked")
    mock_delete_job.step_delete_vectors.side_effect = test_exception

    # KHỞI TẠO TASK
    task = DeleteTask(delete_job=mock_delete_job, logger=mock_logger)
    
    # GIẢ LẬP HÀM RETRY CỦA CELERY ĐỂ KHÔNG BỊ VĂNG LỖI RA NGOÀI
    task.retry = MagicMock()

    # KÍCH HOẠT CHẠY
    document_id = "doc_cleanup_456"
    task.run(document_id=document_id, file_caller="Test")

    # KIỂM CHỨNG (ASSERTIONS)

    mock_delete_job.step_delete_vectors.assert_called_once()
    
    task.retry.assert_called_once_with(exc=test_exception, countdown=30, max_retries=3)
    
    # Đảm bảo Logger có ghi nhận lỗi
    assert mock_logger.error.call_count == 1