"""
Structured JSON logging (backward-compatible wrapper).
All existing imports (`from sys_services.logging import DEFAULT_LOGGER`) continue to work.
This module re-exports the structured Logger so the public API is unchanged.
"""
from sys_services.structured_logging import Logger, DEFAULT_LOGGER

__all__ = ["Logger", "DEFAULT_LOGGER"]
