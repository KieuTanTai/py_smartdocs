from abc import ABC, abstractmethod


class ILogger(ABC):
    """Logger interface with standard logging methods"""

    @abstractmethod
    def info(self, message: str, source: str = "") -> None:
        """Log info message"""
        pass

    @abstractmethod
    def warning(self, message: str, source: str = "") -> None:
        """Log warning message"""
        pass

    @abstractmethod
    def error(self, message: str, source: str = "") -> None:
        """Log error message"""
        pass

    @abstractmethod
    def debug(self, message: str, source: str = "") -> None:
        """Log debug message"""
        pass
