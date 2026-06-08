from pathlib import Path

import numpy as np

from backend.apps.services.rag_base.locate.faiss_service import FaissService
from sys_services.logging import Logger

CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"

demo_vectors = np.vstack([
    np.array([0.1, 0.2, 0.3], dtype=np.float32),
    np.array([0.4, 0.5, 0.6], dtype=np.float32),
    np.array([0.7, 0.8, 0.39], dtype=np.float32),
    np.array([0.7, 0.8, 0.9], dtype=np.float32),
    np.array([0.7, 0.25, 0.5], dtype=np.float32),
    np.array([0.23, 0.6677, 0.5653], dtype=np.float32),
])
demo_ids = np.array([1, 2, 3, 4, 5, 6], dtype=np.int64)


def test_backend_faiss_service():
    faiss_service = FaissService(metadata_dir=OUTPUT_DIR, logger=Logger())

    index = faiss_service.create_index(np_vectors=demo_vectors, ids=demo_ids, file_caller=Path(__file__).name)
    faiss_service.upsert(index=index, vector_id="test_embedding", file_caller=Path(__file__).name)
    query_vector = np.array([[0.7, 0.25, 0.5]], dtype=np.float32)
    response = faiss_service.search(index=index, vector_id="test_vector", query_vector=query_vector, limit=3, file_caller=Path(__file__).name)
    print("Search response:", response)

if __name__ == "__main__":
    test_backend_faiss_service()
    print("All tests passed!")