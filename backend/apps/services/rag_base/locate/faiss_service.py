from pathlib import Path
import re
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
import numpy as np
import faiss
from mistralai.client import Mistral


class FaissService:
    def __init__(self):
        pass

    def save_embedding(self, id: str, responses: np.ndarray) -> None:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        with open(output_dir / f"{id}.csv", "a") as f:
            for vec in responses:
                f.writelines(f"{vec}")

    def load_to_faiss_index(
        self, dimension: int, np_vectors: np.ndarray
    ) -> faiss.IndexFlatL2:
        index = faiss.IndexFlatL2(dimension)
        index.add(np_vectors) # type: ignore
        print("FAISS index: " + str(index.ntotal))
        print("Data after adding to FAISS index: " + str(index.reconstruct_n(0, index.ntotal)))  # type: ignore
        print("FAISS index created and vectors added successfully.")
        return index

    def save_faiss_to_local_file(
        self, index: faiss.IndexFlatL2, file_path: Path
    ) -> None:
        faiss.write_index(index, str(file_path))
