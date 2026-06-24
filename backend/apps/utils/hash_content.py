import hashlib
from typing import List

import numpy as np

def sha256_embedded_content(content: np.ndarray) -> str:
    """Hash the embedded content using SHA-256."""
    hash_object = hashlib.sha256(memoryview(content))
    return hash_object.hexdigest()

def sha256_embedded_contents(contents: list[np.ndarray]) -> list[str]:
    """Hash multiple embedded contents using SHA-256."""
    return [sha256_embedded_content(content) for content in contents]

def sha256_text_content(content: str) -> str:
    """Hash the text content using SHA-256."""
    hash_object = hashlib.sha256(content.encode("utf-8"))
    return hash_object.hexdigest()

def hash_to_numpy_int64_by_str_content(content: str) -> np.int64:
    """Convert a SHA-256 hash string to a 64-bit signed integer.
    
    Note: We mask to 63 bits (not 64) to ensure the value fits in a signed int64.
    FAISS expects signed int64 values in the range [-2^63, 2^63-1].
    """
    # Use SHA-256 for consistent hashing and take first 8 bytes
    hash_bytes = hashlib.sha256(content.encode("utf-8")).digest()[:8]
    # Convert to int and mask to 63 bits to ensure positive value within signed int64 range
    hash_value = int.from_bytes(hash_bytes, byteorder='big', signed=False)
    # Mask to 63 bits to ensure it fits in signed int64 (0 to 2^63-1)
    return np.int64(hash_value & 0x7fffffffffffffff)