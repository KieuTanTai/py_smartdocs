from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np


@dataclass
class IChunkAndCacheResponse:
    document_id: str
    chunk_keys: List[np.int64]
    chunk_texts: List[str] 
    path: Path | None = None # path of cached file if needed for some cache service, for example: redis cache may not need this but file system cache may need this
