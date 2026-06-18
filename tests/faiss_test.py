from pathlib import Path

import numpy as np

from backend.apps.services.rag_base.locate.faiss_service import FaissService
from sys_services.logging import Logger

CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"
CSV_FILE = OUTPUT_DIR / "test_embedding.csv"

"2 first vectors are file A, 2 second vectors are file B, 2 last vectors are file C, "
"the distance between vector in the same file is smaller than the distance between vector in different file"

mock_real_texts = {
    "file_A": [
        "This is the first vector of file A.",
        "This is the second vector of file A."
    ],
    "file_B": [
        "This is the first vector of file B.",
        "This is the second vector of file B."
    ],
    "file_C": [
        "This is the first vector of file C.",
        "This is the second vector of file C."
    ]
}

demo_vectors = np.vstack([
    np.array([0.1, 0.2, 0.3], dtype=np.float32),
    np.array([0.4, 0.5, 0.6], dtype=np.float32),
    np.array([0.7, 0.8, 0.39], dtype=np.float32),
    np.array([0.7, 0.8, 0.9], dtype=np.float32),
    np.array([0.7, 0.25, 0.5], dtype=np.float32),
    np.array([0.23, 0.6677, 0.5653], dtype=np.float32),
])
demo_ids = np.array([1, 2, 3, 4, 5, 6], dtype=np.int64)

def test_get_embeddings_from_csv() -> np.ndarray:
    vectors = []
    with open(CSV_FILE, "r") as f:
        for line in f:
            vector = np
            vectors.append(vector)
            print(f"Read vector from CSV: {vector}")
    return np.vstack(vectors)

def test_backend_faiss_service():
    faiss_service = FaissService(metadata_dir=OUTPUT_DIR, logger=Logger())

    index = faiss_service.create_index(np_vectors=demo_vectors, ids=demo_ids, file_caller=Path(__file__).name)
    faiss_service.upsert(index=index, vector_id="test_embedding", file_caller=Path(__file__).name)
    query_vector = np.array([[0.7, 0.25, 0.5]], dtype=np.float32)
    response = faiss_service.search(index=index, vector_id="test_vector", query_vector=query_vector, limit=3, file_caller=Path(__file__).name)
    print("Search response:", response)

if __name__ == "__main__":
    test_backend_faiss_service()
    # test_get_embeddings_from_csv()
    print("All tests passed!")