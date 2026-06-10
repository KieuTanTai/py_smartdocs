import os
from pathlib import Path

from sys_services.log_pool import LogPool

def tao_log_that():
    print("Bắt đầu tạo log...")

    # Ép nó tạo một thư mục tên là 'THU_MUC_LOG_TEST' ngay tại nơi bạn đang đứng
    thu_muc_test = Path(
        "/home/tanthienlang/Devs/Projects/Python/py_smartdocs/docs/logs/2026-06-10"
    )

    # Khởi tạo LogPool trỏ thẳng vào thư mục này
    logger = LogPool(logs_dir=thu_muc_test, log_file_name="log_that.log")

    # Nạp log vào RAM
    logger.info("Hệ thống RAG đã khởi động", source="TestRealLog", method_call="tao_log_that")
    logger.warning("Cảnh báo: CPU đang chạy 80%", source="TestRealLog", method_call="tao_log_that")
    logger.error("Lỗi mất kết nối đến FAISS", source="TestRealLog", method_call="tao_log_that")

    # Chủ động xả (flush) xuống ổ cứng thật
    logger.flush()

    # In ra đường dẫn tuyệt đối để bạn click vào xem
    print(f"\n=> ĐÃ XONG! Hãy mở thư mục này ra xem file log: {thu_muc_test.absolute()}")

if __name__ == "__main__":
    tao_log_that()
