from enum import Enum


class EBackendStorageName(Enum):
    FAISS = "faiss"
    BM25 = "bm25"
    NEO4J = "neo4j"
