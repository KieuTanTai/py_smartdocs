from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse

@dataclass
class IChatResponse:
    """Response dataclass for chat operations, used by frontend."""
    assistant: str
    conversation_id: str
    metrics: Dict[str, Any]
    new_conversation: bool = False
    error: Optional[str] = None
    used_mock: bool = False
