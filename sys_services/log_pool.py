"""
Manual Pooled Logger implementation.
Buffers logs in memory and requires an explicit flush invocation to perform block I/O.
"""

import sys
from pathlib import Path
import datetime
from backend.apps.core.enums.e_type_message import ETypeMessage
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.system_dirs import LOGS_DIR
from threading import Lock


class LogPool(ILogger):
    _log_dirs: dict[str, Path] = {}
    _separator = "─" * 80

    def __init__(self, logs_dir: Path | None = None):
        """Initialize LogPool with optional logs directory."""
        if logs_dir:
            self._logs_dir = logs_dir
        else:
            self._logs_dir = LOGS_DIR
        self._pool = []  # Buffer to hold log entries in memory
        self._lock = Lock()

    def info(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        """Log info message"""
        self.__enqueue_log_message(ETypeMessage.INFO, message, source, call_by, method_call)

    def warning(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        """Log warning message"""
        self.__enqueue_log_message(ETypeMessage.WARNING, message, source, call_by, method_call)

    def error(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        """Log error message"""
        self.__enqueue_log_message(ETypeMessage.ERROR, message, source, call_by, method_call)

    def debug(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        """Log debug message"""
        self.__enqueue_log_message(ETypeMessage.DEBUG, message, source, call_by, method_call)

    def __enqueue_log_message(
        self,
        type_message: ETypeMessage,
        message: str,
        source: str,
        call_by: str,
        method_call: str,
    ) -> None:
        """Đẩy log vào pool trên RAM """
        with self._lock:
            self._pool.append({
                "timestamp": datetime.datetime.now().isoformat(),
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
        """Lock pool during flush to prevent new logs from being added while flushing.
            Also lock file writing to ensure thread safety if multiple threads call flush simultaneously.
        """
        with self._lock:
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
            folder_name = datetime.date.today().strftime("%Y-%m-%d")
            path = self.__ensure_file_log_path(folder_name)
            self.__write_log_to_file(log_lines, path)

            # Đồng thời đẩy ra console để theo dõi realtime lúc chạy server
            sys.stdout.write(f"--- Flushed {len(self._pool)} logs from pool to {path} ---\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Failed to flush log pool: {e}\n")
            sys.stderr.flush()
        finally:
            self._pool.clear()  # Chắc chắn xóa pool sau khi đã flush

    def __write_log_to_file(self, log_lines: list[str], path: Path) -> None:
        """Internal method to write log lines to file."""
        with open(path, "a", encoding="utf-8") as log_file:
            log_file.writelines(log_lines)

    def __ensure_file_log_path(self, folder_name: str) -> Path:
        """Ensure log file path exists"""
        folder_name = datetime.date.today().strftime("%Y-%m-%d")
        log_dir = self.__ensure_log_dir(folder_name=folder_name)
        log_file_path = self.__execute_log_file_path(log_dir, folder_name)
        return log_file_path

    def __ensure_log_dir(self, folder_name: str) -> Path:
        """Ensure log directory exists"""
        key = folder_name
        if key in self._log_dirs:
            return self._log_dirs[key]
        logging_out_dir = self._logs_dir / folder_name
        logging_out_dir.mkdir(parents=True, exist_ok=True)
        self._log_dirs[key] = logging_out_dir
        return logging_out_dir

    def __execute_log_file_name(self, folder_name: str) -> str:
        """Generate log file name"""
        return f"{folder_name}.log"

    def __execute_log_file_path(self, log_dir: Path, folder_name: str) -> Path:
        """Get or create log file path"""
        file_name = self.__execute_log_file_name(folder_name)
        log_file_path = log_dir / file_name
        log_file_path.touch(exist_ok=True)
        return log_file_path
