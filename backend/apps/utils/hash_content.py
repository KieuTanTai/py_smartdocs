import hashlib

import numpy as np

def sha256_embedded_content(content: np.ndarray) -> str:
    """Hash the embedded content using SHA-256."""
    content_bytes = content.tobytes()
    hash_object = hashlib.sha256(content_bytes)
    return hash_object.hexdigest()