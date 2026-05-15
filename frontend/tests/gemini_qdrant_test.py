import re
import numpy as np
from google import genai
from pathlib import Path
from qdrant_client import models, QdrantClient as Qd
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
from sys_services.read_config.read_qdrant_config import CLUSTER_CONFIG

CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"
CHUNK_FILE = OUTPUT_DIR / "chunks_5e166ad9-f829-4524-acb1-321adbce55de.md"


def test_get_chunks() -> list[str]:
    with open(CHUNK_FILE, "r") as f:
        content = f.read()
    chunks = re.split(r"--- Chunk \d+ ---", content)
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    print(f"Total chunks found: {len(chunks)}")
    return chunks[:5]


def test_gemini_embedding(chunk: str) -> list[genai.types.ContentEmbedding]:
    client = genai.Client(api_key=GEMINI_EMBEDDING_CONFIG["apiKey"])
    result = client.models.embed_content(
        model=GEMINI_EMBEDDING_CONFIG["model"],
        contents=chunk,
    )
    if result.embeddings is not None:
        return result.embeddings
    return []


def test_load_to_qdrant_cluster() -> Qd:
    from qdrant_client import QdrantClient

    client = QdrantClient(
        url=CLUSTER_CONFIG["endpoint"],
        api_key=CLUSTER_CONFIG["api_key"],
        prefer_grpc=True,
    )
    print("Qdrant client initialized successfully.")
    return client


def test_upsert_to_qdrant_cluster(client: Qd, collection_name: str, np_vectors: list) -> None:
    points = [
        models.PointStruct(
            id=i,
            vector=np_vectors[i] if i < len(np_vectors) else [],  
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
    responses = [test_gemini_embedding(chunk) for chunk in chunks]
    values = []
    for i, response in enumerate(responses):
        if response:
            values.append(response[0].values)
    qdrant_client = test_load_to_qdrant_cluster()
    test_upsert_to_qdrant_cluster(
        qdrant_client, CLUSTER_CONFIG["collection_name"], values
    )
