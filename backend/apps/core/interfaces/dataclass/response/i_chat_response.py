from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse

@dataclass
class IChatMetrics:
    provider: EProviderName
    model: str
    mode: str
    total_ms: float = 0.0

@dataclass
class IChatResponse:
    """Response dataclass for chat operations, used by frontend."""
    assistant: str
    conversation_id: str
    metrics: Dict[str, Any]
    generate_response: Optional[IGenerateResponse] = None
    new_conversation: bool = False
    error: Optional[str] = None
    used_mock: bool = False
