from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List
import uuid

import numpy as np

from backend.apps.core.interfaces.dataclass.cache.i_cache_param_value import ICacheParam


@dataclass
class ICacheResponse:
    conversation_id: uuid.UUID
    cache_param: ICacheParam
    path: Path # path of cached file if needed for some cache service, for example: redis cache may not need this but file system cache may need this

@dataclass
class IChunkResponse:
    document_id: str
    chunk_keys: list[np.int64]
    chunk_texts: list[str]
