from typing import Any, List
from dataclasses import dataclass

import numpy as np

@dataclass
class ICacheParam:
    key: str
    values: List[ICacheParamValue]
    expire: int | None = None # Expiration time in seconds, optional

@dataclass
class ICacheParamValue:
    index: np.int64
    text_value: str
