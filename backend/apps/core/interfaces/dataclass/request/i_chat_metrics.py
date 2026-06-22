from dataclasses import dataclass
from typing import Optional


@dataclass
class IChatMetrics:
    """Metrics for chat operations including provider info and performance data."""
    
    provider: str = ""
    model: str = ""
    mode: str = ""
    total_ms: int = 0
