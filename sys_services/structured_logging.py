"""
Structured JSON logging with request ID tracing.
Replaces the old flat-file Logger with proper structured output.
"""
from __future__ import annotations

import datetime
import json
import logging
import os
import sys
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from backend.apps.core.enums.e_type_message import ETypeMessage
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.system_dirs import LOGS_DIR

# ── Request ID context (thread-local) ─────────────────────────────────────────

_request_local = threading.local()


def get_request_id() -> str:
    return getattr(_request_local, "request_id", "") or ""


def set_request_id(rid: Optional[str] = None) -> str:
    rid = rid or str(uuid.uuid4())[:8]
    _request_local.request_id = rid
    return rid


def clear_request_id() -> None:
    _request_local.request_id = ""


# ── JSON formatter ────────────────────────────────────────────────────────────

_LEVEL_MAP = {
    ETypeMessage.DEBUG: logging.DEBUG,
    ETypeMessage.INFO: logging.INFO,
    ETypeMessage.WARNING: logging.WARNING,
    ETypeMessage.ERROR: logging.ERROR,
}


def _format_json_record(
    message: str,
    level: str,
    source: str,
    call_by: str,
    method_call: str,
    request_id: str,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Build a structured JSON log record."""
    record: Dict[str, Any] = {
        "ts": datetime.datetime.now().isoformat(timespec="milliseconds"),
        "level": level,
        "msg": message,
        "source": source or "",
        "call_by": call_by or "",
        "method": method_call or "",
        "req_id": request_id,
    }
    if extra:
        record["extra"] = extra
    return json.dumps(record, ensure_ascii=False, default=str)


# ── File + console handler setup ─────────────────────────────────────────────

class _StructuredFileHandler(logging.FileHandler):
    """Logging handler that writes JSON records to a file."""

    def __init__(self, filename: Path) -> None:
        filename.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, encoding="utf-8")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if self.stream is None:
                # Stream not opened yet (can happen during process shutdown on Windows)
                return
            self.stream.write(super().format(record) + "\n")
            self.flush()
        except Exception:
            self.handleError(record)


# ── Logger implementation ─────────────────────────────────────────────────────

class Logger(ILogger):
    _loggers: Dict[str, "Logger"] = {}
    _lock = threading.Lock()

    def __init__(
        self,
        logs_dir: Optional[Path] = None,
        name: Optional[str] = None,
    ) -> None:
        self._logs_dir = logs_dir or LOGS_DIR
        self._name = name or "smartdocs"
        self._logger = logging.getLogger(self._name)
        self._logger.setLevel(logging.DEBUG)

        # Avoid duplicate handlers on re-init
        if self._logger.handlers:
            return

        # Console handler (pretty-printed for dev)
        _ch = logging.StreamHandler(sys.stdout)
        _ch.setLevel(logging.DEBUG)
        _ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self._logger.addHandler(_ch)

        # File handler (JSON, one file per day)
        _fh = _StructuredFileHandler(self._logs_dir / "smartdocs.json.log")
        _fh.setLevel(logging.DEBUG)
        _fh.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(_fh)

    @classmethod
    def get(cls, name: str) -> "Logger":
        with cls._lock:
            if name not in cls._loggers:
                cls._loggers[name] = cls(name=name)
            return cls._loggers[name]

    def _log(
        self,
        type_message: ETypeMessage,
        message: str,
        source: str,
        call_by: str,
        method_call: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        req_id = get_request_id()
        level_name = type_message.value.upper()
        level = _LEVEL_MAP.get(type_message, logging.INFO)

        json_line = _format_json_record(
            message=message,
            level=level_name,
            source=source,
            call_by=call_by,
            method_call=method_call,
            request_id=req_id,
            extra=extra,
        )
        self._logger.log(level, json_line)

    def info(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        self._log(ETypeMessage.INFO, message, source, call_by, method_call)

    def warning(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        self._log(ETypeMessage.WARNING, message, source, call_by, method_call)

    def error(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        self._log(ETypeMessage.ERROR, message, source, call_by, method_call)

    def debug(self, message: str, source: str = "", call_by: str = "", method_call: str = "") -> None:
        self._log(ETypeMessage.DEBUG, message, source, call_by, method_call)


DEFAULT_LOGGER = Logger.get("smartdocs")
