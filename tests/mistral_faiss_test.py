from pathlib import Path
import re
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
import numpy as np
import faiss
from mistralai.client import Mistral

CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"
CHUNK_FILE = OUTPUT_DIR / "chunks_output.txt"

id = "test_embedding"

def test_get_chunks() -> list[str]:
    with open(CHUNK_FILE, "r") as f:
        content = f.read()
    chunks = re.split(r"Chunk \d+:", content)
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    print(f"Total chunks found: {len(chunks)}")
    return chunks[:5]


def test_mistral_embedding(chunk: str) -> list[float]:
    client = Mistral(api_key=MISTRAL_CONFIG["api_key"])
    result = client.embeddings.create(
        model=MISTRAL_CONFIG["embedding_model"],
        inputs=chunk,
    )
    if result.data is not None and result.data[0].embedding is not None:
        return result.data[0].embedding
    return []


def test_save_embedding(id: str, responses: np.ndarray) -> None:
    with open(OUTPUT_DIR / f"{id}.csv", "a") as f:
        for vec in responses:
            f.writelines(f"{vec}")


def test_check_output_file(id: str) -> None:
    output_file = OUTPUT_DIR / f"{id}.csv"
    with open(output_file, "r") as f:
        content = f.read()
        print("Length of content:", len(content))


def test_load_to_faiss_index(
    dimension: int, np_vectors: np.ndarray
) -> faiss.IndexFlatL2:
    index = faiss.IndexFlatL2(dimension)
    index.add(np_vectors)  # type: ignore
    print("FAISS index: " + str(index.ntotal))
    print("FAISS index created and vectors added successfully.")
    return index


def test_save_faiss_to_local_file(index: faiss.IndexFlatL2, file_path: Path) -> None:
    faiss.write_index(index, str(file_path))
    print(f"FAISS index saved to {file_path} successfully.")

def test_load_faiss_from_local_file(file_path: Path) -> faiss.IndexFlatL2:
    index = faiss.read_index(str(file_path))
    print(f"FAISS index loaded from {file_path} successfully.")
    return index

if __name__ == "__main__":
    chunks = test_get_chunks()
    chunks = chunks[:5]
    responses = np.array([test_mistral_embedding(chunk) for chunk in chunks])
    test_save_embedding(id, responses)
    test_check_output_file(id)
    faiss_index = test_load_to_faiss_index(dimension=responses.shape[1], np_vectors=responses)
    print(faiss_index)  # Print the index object to verify its creation
    print("FAISS index created with the given embeddings." + str(faiss_index.ntotal))
    test_save_faiss_to_local_file(faiss_index, OUTPUT_DIR / f"{id}.faiss")
    loaded_index = test_load_faiss_from_local_file(OUTPUT_DIR / f"{id}.faiss")
    print(loaded_index)
    print("All tests completed successfully.")
