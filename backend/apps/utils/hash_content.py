import hashlib
from typing import List

import numpy as np

def sha256_embedded_content(content: np.ndarray) -> str:
    """Hash the embedded content using SHA-256."""
    hash_object = hashlib.sha256(memoryview(content))
    return hash_object.hexdigest()

def sha256_embedded_contents(contents: List[np.ndarray]) -> List[str]:
    """Hash multiple embedded contents using SHA-256."""
    return [sha256_embedded_content(content) for content in contents]

def sha256_text_content(content: str) -> str:
    """Hash the text content using SHA-256."""
    hash_object = hashlib.sha256(content.encode("utf-8"))
    return hash_object.hexdigest()

def hash_to_numpy_int64_by_str_content(content: str) -> np.int64:
    """Convert a SHA-256 hash string to a 64-bit integer."""
    return np.int64(hash(content) & 0xffffffffffffffff)  # Use the first 16 characters (64 bits) of the hash