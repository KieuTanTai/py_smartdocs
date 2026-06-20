from dataclasses import dataclass
from typing import Any, Optional

from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse

@dataclass
class IChatResponse:
    conversation_id: str
    generate_response: Optional[IGenerateResponse] = None
    new_conversation: bool = False
    error: Optional[str] = None
