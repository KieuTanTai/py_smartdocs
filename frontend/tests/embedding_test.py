from google import genai
from pathlib import Path
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from qdrant_client import models, QdrantClient as Qd
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
import numpy as np
import faiss

from sys_services.read_config.read_qdrant_config import CLUSTER_CONFIG

CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"
CHUNK_FILE = OUTPUT_DIR / "chunks_5e166ad9-f829-4524-acb1-321adbce55de.md"


def test_get_chunks() -> list[str]:
    with open(CHUNK_FILE, "r") as f:
        chunks = f.read().split("--- Chunk")
    print(f"Total chunks found: {len(chunks) - 1}")
    return chunks[1:]


def test_gemini_embedding(chunk: str) -> list[genai.types.ContentEmbedding]:
    client = genai.Client(api_key=GEMINI_EMBEDDING_CONFIG["apiKey"])
    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_CONFIG["model"],
        contents=chunk,
    )
    print("Embedding result received from Gemini API: ", result.embeddings)
    if result.embeddings is not None:
        return result.embeddings
    # response = result.embeddings
    # if response is not None:
    #     return response
    return []


def test_save_embedding(id: str, responses: np.ndarray) -> None:
    with open(OUTPUT_DIR / f"{id}.csv", "a") as f:
        for vec in responses:
            f.writelines(f"{vec}")


def test_check_output_file() -> None:
    output_file = OUTPUT_DIR / f"{id}.csv"
    with open(output_file, "r") as f:
        content = f.read()
        print("Length of content:", len(content))


def test_load_to_Vector_db(dimension: int, np_vectors: np.ndarray) -> None:
    index = faiss.IndexFlatL2(dimension)
    index.add(np_vectors)  # type: ignore
    print("faiss index: " + str(index.ntotal))
    print("data after adding to faiss index: " + str(index.reconstruct_n(0, index.ntotal)))  # type: ignore
    print("FAISS index created and vector added successfully.")


def test_load_to_qdrant_cluster() -> Qd:
    from qdrant_client import QdrantClient
    from sys_services.read_config.read_qdrant_config import CLUSTER_CONFIG

    client = QdrantClient(
        url=CLUSTER_CONFIG["endpoint"],
        api_key=CLUSTER_CONFIG["api_key"],
        prefer_grpc=True,
    )
    print("Qdrant client initialized successfully.")
    return client


def test_upsert_to_qdrant_cluster(
    client: Qd, collection_name: str, np_vectors: np.ndarray
) -> None:
    points = [
        models.PointStruct(
            id=i,
            vector=np_vectors[i].tolist(),  # type: ignore
            payload={"metadata": f"Chunk {i}"},
        )
        for i in range(len(np_vectors))
    ]
    client.upsert(collection_name=collection_name, points=points)
    print(
        f"Upserted {len(points)} points to Qdrant collection '{collection_name}' successfully."
    )


if __name__ == "__main__":
    chunks = test_get_chunks()
    chunks = chunks[:5]
    responses = np.array([test_gemini_embedding(chunk) for chunk in chunks])
    # print("Shape of responses:", responses.shape[1])
    # test_save_embedding(id, responses)
    # test_check_output_file()
    # test_load_to_Vector_db(dimension=1536, np_vectors=responses)
    # qdrant_client = test_load_to_qdrant_cluster()
    # test_upsert_to_qdrant_cluster(
    #     qdrant_client, CLUSTER_CONFIG["collection_name"], responses
    # )
    print("Gemini embedding test completed successfully.")
