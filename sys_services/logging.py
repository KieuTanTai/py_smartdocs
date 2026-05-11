import sys
import datetime
from pathlib import Path
from sys_services.system_dirs import ROOT_DIR
from sys_services.enums import TypeMessage


class Logger:
    _log_dirs: dict[str, Path] = {}

    @classmethod
    def log(
        cls, type_message: TypeMessage, log_message: str, source_log: str = ""
    ) -> None:
        cls._add_log_message_to_file(type_message, log_message, source_log)

    @classmethod
    def _ensure_log_dir(cls, folder_name: str) -> Path:
        key = folder_name
        if key in cls._log_dirs:
            return cls._log_dirs[key]
        if str(ROOT_DIR) not in sys.path:
            sys.path.insert(0, str(ROOT_DIR))
        logging_out_dir = ROOT_DIR / "docs" / "logs" / folder_name
        logging_out_dir.mkdir(parents=True, exist_ok=True)
        cls._log_dirs[key] = logging_out_dir
        return logging_out_dir

    @classmethod
    def _execute_log_file_name(cls, folder_name: str) -> str:
        return f"{folder_name}.log"

    @classmethod
    def _execute_log_file_path(cls, log_dir: Path, folder_name: str) -> Path:
        file_name = cls._execute_log_file_name(folder_name)
        log_file_path = log_dir / file_name
        log_file_path.touch(exist_ok=True)
        return log_file_path

    @classmethod
    def _add_log_message_to_file(
        cls,
        type_message: TypeMessage,
        log_message: str,
        source_log: str,
    ) -> None:
        try:
            folder_name = datetime.date.today().strftime("%Y-%m-%d")
            log_dir = cls._ensure_log_dir(folder_name=folder_name)
            log_file_path = cls._execute_log_file_path(log_dir, folder_name)
            with open(log_file_path, "a") as log_file:
                log_file.write(f"[{type_message.value.upper()}] {log_message}\n")
                if source_log.strip():
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    log_file.write(
                        f"--- End of log message from {source_log} at {timestamp} ---\n"
                    )
        except Exception as exc:
            print(f"Error writing log message to file: {exc}")
