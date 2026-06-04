import datetime
from pathlib import Path
from sys_services.system_dirs import ROOT_DIR
from sys_services.enums.e_type_message import ETypeMessage
from backend.apps.core.interfaces.system.i_logging import ILogger


class Logger(ILogger):
    _log_dirs: dict[str, Path] = {}
    _separator = "─" * 80

    def info(self, message: str, source: str = "") -> None:
        """Log info message"""
        self._log_message(ETypeMessage.INFO, message, source)

    def warning(self, message: str, source: str = "") -> None:
        """Log warning message"""
        self._log_message(ETypeMessage.WARNING, message, source)

    def error(self, message: str, source: str = "") -> None:
        """Log error message"""
        self._log_message(ETypeMessage.ERROR, message, source)

    def debug(self, message: str, source: str = "") -> None:
        """Log debug message"""
        self._log_message(ETypeMessage.DEBUG, message, source)

    def _log_message(
        self,
        type_message: ETypeMessage,
        message: str,
        source: str,
    ) -> None:
        """Internal method to handle logging to file"""
        try:
            folder_name = datetime.date.today().strftime("%Y-%m-%d")
            log_dir = self._ensure_log_dir(folder_name=folder_name)
            log_file_path = self._execute_log_file_path(log_dir, folder_name)

            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            type_str = type_message.value.upper()

            with open(log_file_path, "a", encoding="utf-8") as log_file:
                # Write separator for readability
                log_file.write(f"\n{self._separator}\n")

                # Write header with timestamp and type
                log_file.write(f"[{timestamp}] [{type_str}]\n")

                # Write source if provided
                if source.strip():
                    log_file.write(f"Source: {source}\n")

                # Write message with proper indentation
                log_file.write(f"Message:\n  {message}\n")

                # Write end marker
                log_file.write(f"{self._separator}\n")

        except Exception as exc:
            print(f"Error writing log message to file: {exc}")

    def _ensure_log_dir(self, folder_name: str) -> Path:
        """Ensure log directory exists"""
        key = folder_name
        if key in self._log_dirs:
            return self._log_dirs[key]
        logging_out_dir = ROOT_DIR / "docs" / "logs" / folder_name
        logging_out_dir.mkdir(parents=True, exist_ok=True)
        self._log_dirs[key] = logging_out_dir
        return logging_out_dir

    def _execute_log_file_name(self, folder_name: str) -> str:
        """Generate log file name"""
        return f"{folder_name}.log"

    def _execute_log_file_path(self, log_dir: Path, folder_name: str) -> Path:
        """Get or create log file path"""
        file_name = self._execute_log_file_name(folder_name)
        log_file_path = log_dir / file_name
        log_file_path.touch(exist_ok=True)
        return log_file_path


DEFAULT_LOGGER = Logger()
