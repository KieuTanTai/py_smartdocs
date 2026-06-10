from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np


@dataclass
class IVectorDBUpsertResponse:
    id: str
    create_at: datetime
    is_success: bool
    sumarize_content: str = ""  # Optional field to store a summary of the content associated with the vector, if applicable
    message: str = ""  # Optional message field for additional info or error messages

@dataclass
class IVectorDBQueryResponse:
    id: str
    distances: list[float]
    indices: list[int] # This can be used to retrieve the original content or metadata associated with the vector
    message: str = ""  # Optional message field for additional info or error messages

@dataclass
class IVectorDBDeleteResponse:
    id: str
    is_success: bool
    deleted_count: int = 0
    message: str = ""  # Optional message field for additional info or error messages

@dataclass
class IVectorDBLoadResponse:
    id: str
    is_success: bool
    index: Any = None  # Provider-specific index object or identifier, if applicable
    message: str = ""  # Optional message field for additional info or error messages