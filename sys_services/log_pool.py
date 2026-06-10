"""
Manual Pooled Logger implementation.
Buffers logs in memory and requires an explicit flush invocation to perform block I/O.
"""

import sys
from pathlib import Path
from datetime import datetime

from backend.apps.core.enums.e_type_message import ETypeMessage
from backend.apps.core.interfaces.system.i_log_pool import ILogPool
from sys_services.system_dirs import LOGS_DIR


class LogPool(ILogPool):
    _separator = "─" * 80

    def __init__(self, logs_dir: Path | None = None, log_file_name: str = "app_runtime.log"):
        """
        Khởi tạo Log Pool.
        Args:
            logs_dir: Thư mục chứa log (Mặc định lấy từ hệ thống LOGS_DIR)
            log_file_name: Tên file log cụ thể (Mặc định là app_runtime.log, có thể thay đổi lúc test)
        """
        self._pool: list[dict] = []
        self._logs_dir = logs_dir if logs_dir else LOGS_DIR
        self._log_file_path = Path(self._logs_dir) / log_file_name

    def info(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        """Log info message"""
        self._enqueue_log_message(ETypeMessage.INFO, message, source, call_by, method_call)

    def warning(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        """Log warning message"""
        self._enqueue_log_message(ETypeMessage.WARNING, message, source, call_by, method_call)

    def error(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        """Log error message"""
        self._enqueue_log_message(ETypeMessage.ERROR, message, source, call_by, method_call)

    def debug(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        """Log debug message"""
        self._enqueue_log_message(ETypeMessage.DEBUG, message, source, call_by, method_call)
    
    def _enqueue_log_message(
        self,
        type_message: ETypeMessage,
        message: str,
        source: str,
        call_by: str,
        method_call: str,
    ) -> None:
        """Đẩy log vào pool trên RAM """
        self._pool.append({
            "timestamp": datetime.now().isoformat(),
            "type_message": type_message.value.upper(),
            "message": message,
            "source": source,
            "call_by": call_by,
            "method_call": method_call
        })

    def flush(self) -> None:
        """
        Mở trực tiếp file ra làm Block I/O hàng loạt (Batch Write),
        ghi toàn bộ log trong pool vào file, sau đó clear pipeline.
        """
        if not self._pool:
            return  # Không có log nào để flush

        log_lines = []
        for log in self._pool:
            log_lines.append(f"\n{self._separator}\n")
            log_lines.append(f"[{log['timestamp']}] [{log['type_message']}]\n")
            log_lines.append(f"Source: {log['source']}\n")
            log_lines.append(f"Called by: {log['call_by']} - Method: {log['method_call']}\n")
            log_lines.append(f"Message: {log['message']}\n")

        try:
            self._log_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self._log_file_path, "a", encoding="utf-8") as log_file:
                log_file.writelines(log_lines)

            # Đồng thời đẩy ra console để theo dõi realtime lúc chạy server
            sys.stdout.write(f"--- Flushed {len(self._pool)} logs from pool to {self._log_file_path} ---\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Failed to flush log pool: {e}\n")
            sys.stderr.flush()
        finally:
            self._pool.clear()  # Chắc chắn xóa pool sau khi đã flush