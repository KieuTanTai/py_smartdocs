from dataclasses import dataclass
from typing import Optional


@dataclass
class IUploadApplicationResponse:
    """Response dataclass for upload application endpoint.
    Field contract API (rule mục 13): id, title, status, conversation_id, date_create.
    """
    id: str
    title: str
    status: str
    conversation_id: str
    date_create: str


@dataclass
class ISendMessageApplicationResponse:
    """Response dataclass for send message application endpoint.
    Field contract API (rule mục 13): message, used_mock, conversation_id.
    """
    message: str
    used_mock: bool
    conversation_id: str


@dataclass
class IGetConversationApplicationResponse:
    """Response dataclass for get conversation application endpoint.
    Field contract API (rule mục 13): conversation_id, status, date_create.
    """
    conversation_id: str
    status: str
    date_create: str
    title: Optional[str] = None
