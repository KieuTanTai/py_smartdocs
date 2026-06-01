from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class IEmbeddingStorageResult:
    embedding_path: Path
    metadata_path: Path
    vector_count: int
    dimension: int
