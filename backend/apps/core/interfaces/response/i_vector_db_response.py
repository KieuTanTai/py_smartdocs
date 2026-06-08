from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np


@dataclass
class IVectorDBUpsertResponse:
    UUID: str
    create_at: datetime
    sumarize_content: str
    is_success: bool
    message: str = ""  # Optional message field for additional info or error messages

@dataclass
class IVectorDBQueryResponse:
    UUID: str
    distances: list[float]
    indices: list[int] # This can be used to retrieve the original content or metadata associated with the vector
    message: str = ""  # Optional message field for additional info or error messages

@dataclass
class IVectorDBDeleteResponse:
    UUID: str
    is_success: bool
    deleted_count: int = 0
    message: str = ""  # Optional message field for additional info or error messages

@dataclass
class IVectorDBLoadResponse:
    UUID: str
    is_success: bool
    index: Any = None  # Provider-specific index object or identifier, if applicable
    message: str = ""  # Optional message field for additional info or error messages