import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest



# =====================================================================
# GIẢ LẬP DJANGO MODELS TRƯỚC KHI IMPORT MỌI THỨ KHÁC
# =====================================================================
mock_django_models = MagicMock()
sys.modules['backend.apps.services.chat.models'] = mock_django_models
sys.modules['apps.services.chat.models'] = mock_django_models

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.tasks.upload_tasks import UploadTask
from backend.apps.core.interfaces.dataclass.tasks.i_chunk_and_cache_response import ICacheResponse
from backend.apps.core.interfaces.dataclass.tasks.i_upload_response import IEmbedResponse, ISaveResponse

# ==========================================
# BÀI TEST: UPLOAD NHIỀU FILE CÙNG LÚC
# ==========================================

@patch("backend.apps.tasks.upload_tasks.DocumentModel")
def test_upload_task_run_multiple_files_success(mock_document_model):
    """Test luồng xử lý mảng file trong UploadTask (Celery)"""
    
    # 1. SETUP MOCKS (Giả lập môi trường)
    mock_logger = MagicMock()
    mock_upload_job = MagicMock()
    
    # Giả lập Database trả về 1 Document có chứa chuỗi nhiều file
    mock_doc_instance = MagicMock()
    mock_doc_instance.file_path = "/tmp/file1.pdf, /tmp/file2.pdf" # Giả lập DB lưu chuỗi
    mock_document_model.objects.get.return_value = mock_doc_instance

    # Giả lập kết quả trả về của từng bước trong UploadJob
    mock_upload_job.step_extract.return_value = ["Nội dung file 1", "Nội dung file 2"]
    mock_upload_job.step_normalize.return_value = ["Clean text 1", "Clean text 2"]
    
    mock_chunk_response = MagicMock(spec=ICacheResponse)
    mock_chunk_response.chunk_texts = ["Chunk 1", "Chunk 2", "Chunk 3"]
    mock_upload_job.step_chunk_and_cache.return_value = mock_chunk_response
    
    mock_embed_response = MagicMock(spec=IEmbedResponse)
    mock_embed_response.embeded_metadata = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
    mock_upload_job.step_embed.return_value = mock_embed_response
    
    mock_save_response = MagicMock(spec=ISaveResponse)
    mock_upload_job.step_save.return_value = mock_save_response

    # 2. KHỞI TẠO TASK CẦN TEST
    task = UploadTask(upload_job=mock_upload_job, logger=mock_logger)

    # 3. KÍCH HOẠT CHẠY THỰC TẾ
    document_id = "doc_999"
    provider = EProviderName.MISTRAL
    result = task.run(document_id=document_id, provider_name=provider, file_caller="Test")

    # 4. KIỂM CHỨNG (ASSERTIONS)
    
    # a. Kiểm tra Document status đã cập nhật "processing" rồi đến "indexed" chưa?
    assert mock_doc_instance.status == "indexed"
    assert mock_doc_instance.save.call_count == 2
    
    # b. Kiểm tra hệ thống có bóc tách đúng thành 2 Path rời rạc không?
    mock_upload_job.step_extract.assert_called_once()
    called_paths = mock_upload_job.step_extract.call_args.args[0]
    assert called_paths == [Path("/tmp/file1.pdf"), Path("/tmp/file2.pdf")]
    
    # c. Kiểm tra Pipeline chạy đủ không thiếu bước nào
    mock_upload_job.step_normalize.assert_called_once_with(
        ["Nội dung file 1", "Nội dung file 2"], file_caller=task._UploadTask__execute_pipeline.__name__
    )
    mock_upload_job.step_chunk_and_cache.assert_called_once()
    mock_upload_job.step_embed.assert_called_once()
    mock_upload_job.step_save.assert_called_once()
    

    # d. Kiểm tra luồng Knowledge Graph (Graph RAG) có được gọi không
    mock_upload_job.step_build_knowledge_graph.assert_called_once_with(
        document_id=document_id,
        extracted_texts=["Nội dung file 1", "Nội dung file 2"],
        provider=provider,
        model_name="qwen2.5:1.5b-instruct",
        file_caller=task._UploadTask__execute_pipeline.__name__
    )
    
    # e. Kết quả trả về phải là Save Response
    assert result == mock_save_response