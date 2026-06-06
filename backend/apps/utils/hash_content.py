import hashlib

import numpy as np

def sha256_embedded_content(content: np.ndarray) -> str:
    """Hash the embedded content using SHA-256."""
    hash_object = hashlib.sha256(memoryview(content))
    return hash_object.hexdigest()

def sha256_text_content(content: str) -> str:
    """Hash the text content using SHA-256."""
    hash_object = hashlib.sha256(content.encode("utf-8"))
    return hash_object.hexdigest()