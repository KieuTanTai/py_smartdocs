from dataclasses import dataclass
from typing import Optional

@dataclass
class ICreateFileResponse:
    """
    Interface for create file response.
    Contains uploaded file metadata.
    """
    id: str
    object: str
    bytes: int
    created_at: int
    filename: str
    purpose: str
    mimetype: Optional[str] = None
