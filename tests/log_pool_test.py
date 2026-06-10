"""
Unit tests for LogPool implementation using pytest and unittest.mock.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from backend.apps.core.enums.e_type_message import ETypeMessage
from sys_services.log_pool import LogPool




def test_logger_buffers_in_memory_without_io():
    """Test 1: Gọi các hàm log chỉ được nạp vào RAM pool, tuyệt đối không được mở file."""
    logger = LogPool(logs_dir=Path("."), log_file_name="mock_app.log")
    
    with patch("builtins.open", mock_open()) as mocked_open:
        logger.info(
            message="User thực hiện truy vấn RAG", 
            source="MessageJob", 
            call_by="CeleryTask", 
            method_call="run"
        )
        
        assert len(logger._pool) == 1
        assert logger._pool[0]["type_message"] == "INFO"
        assert logger._pool[0]["message"] == "User thực hiện truy vấn RAG"
        assert logger._pool[0]["source"] == "MessageJob"
        assert logger._pool[0]["call_by"] == "CeleryTask"
        assert logger._pool[0]["method_call"] == "run"
        
        mocked_open.assert_not_called()


def test_logger_flush_performs_block_io_and_clears_pool():
    """Test 2: Khi gọi flush(), hệ thống phải tạo thư mục, mở file đúng 1 lần và dọn sạch pool RAM."""
    logger = LogPool(logs_dir=Path("./mock_logs"), log_file_name="mock_app.log")
    
    logger.info("Tin nhắn thử nghiệm hệ thống thành công")
    logger.error("Lỗi crash kết nối FAISS Database")
    
    assert len(logger._pool) == 2 
    
    m_open = mock_open()
    with patch("builtins.open", m_open), \
         patch.object(Path, "mkdir") as mock_mkdir:
        
        logger.flush()
        
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        expected_path = Path("./mock_logs/mock_app.log")
        m_open.assert_called_once_with(expected_path, "a", encoding="utf-8")
        
        handle = m_open()
        handle.writelines.assert_called_once()
        
        written_lines = handle.writelines.call_args[0][0]
        full_written_text = "".join(written_lines)
        assert "INFO" in full_written_text
        assert "ERROR" in full_written_text
        assert "Source:" in full_written_text
        assert "Called by:" in full_written_text
        
        assert len(logger._pool) == 0


def test_logger_flush_empty_pool_does_nothing():
    """Test 3: Nếu Pool đang trống, gọi flush() phải thoát sớm, không mở file bừa bãi gây lãng phí CPU."""
    logger = LogPool(logs_dir=Path("."), log_file_name="mock_app.log")
    
    m_open = mock_open()
    with patch("builtins.open", m_open), \
         patch.object(Path, "mkdir") as mock_mkdir:
         
        logger.flush()
        
        m_open.assert_not_called()
        mock_mkdir.assert_not_called()

def test_logger_creates_a_real_physical_file(tmp_path):
    """Test 4: Ép hệ thống tạo ra FILE THẬT trên ổ cứng để lập trình viên kiểm chứng."""

    logger = LogPool(logs_dir=tmp_path, log_file_name="real_test_file.log")

    logger.info("Log này được ghi xuống ổ cứng thật thông qua pytest!")
    logger.warning("Cảnh báo khẩn cấp hệ thống RAG")
    
    logger.flush()

    real_file_path = tmp_path / "real_test_file.log"
    
    assert real_file_path.exists()
    
    file_content = real_file_path.read_text(encoding="utf-8")
    assert "INFO" in file_content
    assert "WARNING" in file_content
    assert "Log này được ghi xuống ổ cứng thật" in file_content 
    
    print(f"\n\n[ĐƯỜNG DẪN FILE THẬT]: {real_file_path.resolve()}\n")