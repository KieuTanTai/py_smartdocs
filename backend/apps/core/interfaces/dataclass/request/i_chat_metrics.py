# interfaces/chat_metrics.py

from dataclasses import dataclass


@dataclass
class IChatMetrics:
    provider: str
    model: str
    mode: str
    total_ms: int
