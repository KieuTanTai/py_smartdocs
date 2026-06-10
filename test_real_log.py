import threading
import os
from pathlib import Path

from sys_services.log_pool import LogPool
logger = LogPool()

def first_thread_return_info_log():
    logger.info(
        message="User thực hiện truy vấn RAG",
        source=Path(__file__).name,
        call_by=Path(__file__).name,
        method_call=first_thread_return_info_log.__name__,
    )

def second_thread_return_error_log():
    logger.error(
        message="Lỗi crash kết nối FAISS Database", 
        source=Path(__file__).name, 
        call_by=Path(__file__).name, 
        method_call=second_thread_return_error_log.__name__
    )

def third_thread_return_warning_log():
    logger.warning(
        message="Cảnh báo: CPU đang chạy 80%", 
        source=Path(__file__).name, 
        call_by=Path(__file__).name, 
        method_call=third_thread_return_warning_log.__name__
    )

def fourth_thread_return_debug_log():
    logger.debug(
        message="Debug: Kiểm tra kết nối đến Redis Cache", 
        source=Path(__file__).name, 
        call_by=Path(__file__).name, 
        method_call=fourth_thread_return_debug_log.__name__
    )

def test_log_pool_with_multiple_threads():
    """Test 5: Mô phỏng nhiều thread cùng log vào pool, sau đó flush để xem kết quả."""
    threads = []
    threads.append(threading.Thread(target=first_thread_return_info_log))
    threads.append(threading.Thread(target=second_thread_return_error_log))
    threads.append(threading.Thread(target=third_thread_return_warning_log))
    threads.append(threading.Thread(target=fourth_thread_return_debug_log))

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

def mock_thread_for_mock_return_thread():
    """Test 6: Mock thread for thread return resouce from classes."""
    logger.info(
        message="Đây là log giả lập từ thread test", 
        source=Path(__file__).name, 
        call_by=Path(__file__).name, 
        method_call=mock_thread_for_mock_return_thread.__name__
    )

def mock_thread_for_mock_write_log_to_file():
    """Test 7: Mock thread for thread write log to file."""
    logger.info(
        message="Đây là log giả lập từ thread test", 
        source=Path(__file__).name, 
        call_by=Path(__file__).name, 
        method_call=mock_thread_for_mock_write_log_to_file.__name__
    )
    logger.flush()  # Đảm bảo xả log hiện tại trước khi test

def test_log_pool_flush_with_mock_thread():
    """Test 7: Mô phỏng một thread thực hiện flush log xuống file thật, kiểm tra file log có được tạo ra hay không."""
    threads = []
    first_mock_thread = threading.Thread(target=mock_thread_for_mock_return_thread)
    second_mock_thread = threading.Thread(target=mock_thread_for_mock_write_log_to_file)
    threads.extend([first_mock_thread, second_mock_thread])
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

def tao_log_that():
    print("Bắt đầu tạo log...")


    # Khởi tạo LogPool trỏ thẳng vào thư mục này

    # Nạp log vào RAM
    test_log_pool_with_multiple_threads()


    # Chủ động xả (flush) xuống ổ cứng thật
    test_log_pool_flush_with_mock_thread()

    # In ra đường dẫn tuyệt đối để bạn click vào xem
    print(f"\n=> ĐÃ XONG! Hãy mở thư mục này ra xem file log: {logger._logs_dir.absolute()}")

if __name__ == "__main__":
    tao_log_that()
