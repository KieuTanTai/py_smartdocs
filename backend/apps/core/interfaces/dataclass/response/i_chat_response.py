from dataclasses import dataclass
from typing import Any, Optional

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse

@dataclass
class IChatResponse:
    assistant: str
    conversation_id: str
    metrics: IChatMetrics
    generate_response: Optional[IGenerateResponse] = None
    new_conversation: bool = False
    error: Optional[str] = None
    used_mock: bool = False

@dataclass
class IChatMetrics:
    provider: EProviderName
    model: str
    mode: str
    total_ms: float = 0.0