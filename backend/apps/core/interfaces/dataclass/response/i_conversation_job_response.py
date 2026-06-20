from dataclasses import dataclass
from typing import Optional

from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse
from backend.apps.services.chat.models import MessageModel

@dataclass
class IConversationJobResponse:
    conversation_id: str
    status: bool
    message_model: MessageModel
    generate_response: Optional[IGenerateResponse] = None
