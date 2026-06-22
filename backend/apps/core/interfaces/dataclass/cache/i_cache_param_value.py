from typing import Any, List
from dataclasses import dataclass

import faiss
import numpy as np

@dataclass
class ICacheParamValue:
    index: np.int64
    embedding: np.ndarray
    text_value: str

@dataclass
class ICacheParam:
    key: str #conversation_id
    values: list[ICacheParamValue] #stack of chunks on all files of conversation
    expire: int | None = None # Expiration time in seconds, optional