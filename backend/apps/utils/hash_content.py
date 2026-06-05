import hashlib

import numpy as np

def sha256_embedded_content(content: np.ndarray) -> str:
    """Hash the embedded content using SHA-256."""
    hash_object = hashlib.sha256(memoryview(content))
    return hash_object.hexdigest()
