from abc import ABC, abstractmethod


class ILogPool(ABC):
    """Logger interface with standard logging methods"""

    @abstractmethod
    def info(self, message: str, source: str = "", call_by: str = "", method_call="") -> None:
        """Log info message"""
        pass

    @abstractmethod
    def warning(self, message: str, source: str = "", call_by: str = "", method_call="") -> None:
        """Log warning message"""
        pass

    @abstractmethod
    def error(self, message: str, source: str = "", call_by: str = "", method_call="") -> None:
        """Log error message"""
        pass

    @abstractmethod
    def debug(self, message: str, source: str = "", call_by: str = "", method_call="") -> None:
        """Log debug message"""
        pass
