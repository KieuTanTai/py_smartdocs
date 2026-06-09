# Hybrid Search Implementation Guide

## Overview

Hybrid search combines **semantic search (FAISS)** and **keyword search (BM25)** to provide comprehensive document retrieval:

- **FAISS**: Semantic similarity using embeddings (contextual understanding)
- **BM25**: Keyword matching (lexical relevance)
- **Hybrid**: Weighted combination of both for balanced results

## Architecture

### Data Flow During Upload

```
Upload File
  ↓ Extract (OCR)
  ↓ Normalize
  ↓ Chunk text
  ├→ Cache chunks (Redis)
  ├→ Generate embeddings
  ├→ Build FAISS index (semantic search)
  ├→ Build BM25 index (keyword search) ← NEW
  └→ Store metadata (MariaDB)
```

### Components

1. **BM25Service** (`backend/apps/services/rag_base/locate/bm25_service.py`)
   - Implements `IVectorStoreService` interface
   - Stores chunk texts in JSON metadata files
   - Performs BM25-like scoring (word matching)

2. **HybridSearchService** (`backend/apps/services/rag_base/hybrid_search_service.py`)
   - Orchestrates FAISS + BM25 searches
   - Merges and ranks results with weighted scoring
   - Default weights: FAISS 60%, BM25 40%

3. **Updated UploadJob** (`backend/apps/job/upload_job.py`)
   - Builds both FAISS and BM25 indexes during document upload
   - Returns success status for both

4. **Updated ConversationJob** (`backend/apps/job/conversation_job.py`)
   - New method: `hybrid_search_in_conversation()`
   - Supports semantic + keyword search on conversation documents

## Usage

### 1. Upload Document (Automatic)

When uploading a document, both indexes are built automatically:

```python
from backend.apps.config.container import BackendContainer
from backend.apps.tasks.document_tasks import upload_document_task

# Celery task (async)
upload_document_task.delay('document-id', provider='mistral')
# or sync via Django shell
upload_document_task('document-id', provider='mistral')
```

Returns:
```json
{
  "document_id": "doc-123",
  "faiss_upsert": {"uuid": "doc-123", "is_success": true},
  "bm25_upsert": {"uuid": "doc-123", "is_success": true},
  ...
}
```

### 2. Search Within Conversation

Use hybrid search to find relevant chunks:

```python
from backend.apps.config.container import BackendContainer

container = BackendContainer()
conversation_job = container.conversation_job()

# Perform hybrid search
results = conversation_job.hybrid_search_in_conversation(
    conversation_id="conv-123",
    query_text="What is machine learning?",
    limit=5,
    faiss_weight=0.6,    # 60% semantic
    bm25_weight=0.4      # 40% keyword
)

# Results structure:
# {
#   "results": [
#     {
#       "chunk_id": "doc-123:1",
#       "score": 0.75,
#       "sources": ["faiss", "bm25"],
#       "faiss_score": 0.8,
#       "bm25_score": 0.7
#     },
#     ...
#   ]
# }
```

### 3. Adjust Weights

Balance between semantic and keyword relevance:

```python
# More semantic (deep understanding)
results = conversation_job.hybrid_search_in_conversation(
    conversation_id="conv-123",
    query_text="quantum computing principles",
    faiss_weight=0.8,   # 80% semantic
    bm25_weight=0.2     # 20% keyword
)

# More keyword-focused (exact matches)
results = conversation_job.hybrid_search_in_conversation(
    conversation_id="conv-123",
    query_text="Q3 financial report",
    faiss_weight=0.4,   # 40% semantic
    bm25_weight=0.6     # 60% keyword
)
```

## Configuration

### Metadata Storage

- **FAISS indexes**: `metadata/faiss/{document_id}.faiss`
- **BM25 texts**: `metadata/bm25/{document_id}.bm25` (JSON)

### Enum Values

```python
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName

EBackendStorageName.FAISS   # "faiss"
EBackendStorageName.BM25    # "bm25"
EBackendStorageName.NEO4J   # "neo4j"
```

## Advanced Usage

### Direct Service Access

```python
from backend.apps.services.rag_base.locate.locate_service import LocateService
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from sys_services.logging import Logger
from pathlib import Path

logger = Logger()
locate_service = LocateService(metadata_dir=Path("metadata"), logger=logger)

# Get BM25 service
bm25_service = locate_service.get_vector_store(EBackendStorageName.BM25)

# Search BM25
results = bm25_service.search(
    index={},
    vector_id="document-id",
    query_vector=np.array(["search query"], dtype=object),
    limit=10,
    file_caller="custom_search"
)
```

### Merge Custom Results

```python
# Perform individual searches
faiss_results = faiss_service.search(...)
bm25_results = bm25_service.search(...)

# Use HybridSearchService to merge
merged = hybrid_search.search(
    document_id="doc-123",
    query_text="my query",
    query_vector=embedding,
    faiss_weight=0.7,
    bm25_weight=0.3
)
```

## Performance Tuning

### For Recall (Find all relevant docs)
- Increase `limit` parameter
- Increase both weights (closer to 1.0)

### For Precision (Find only highly relevant docs)
- Decrease `limit` parameter
- Use higher `faiss_weight` for semantic relevance

### For Speed
- Use smaller `limit` (fewer merges)
- Cache query embeddings if running multiple searches

## Debugging

### Check if Indexes Exist

```python
from backend.apps.services.rag_base.locate.locate_service import LocateService
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName

locate_service = LocateService(metadata_dir=Path("metadata"), logger=logger)

# FAISS
faiss_service = locate_service.get_vector_store(EBackendStorageName.FAISS)
print(faiss_service.is_existed_in_metadata("document-id"))

# BM25
bm25_service = locate_service.get_vector_store(EBackendStorageName.BM25)
print(bm25_service.is_existed_in_metadata("document-id"))
```

### Load Indexes

```python
# Load FAISS
faiss_load = faiss_service.load("document-id")
print(f"FAISS loaded: {faiss_load.is_success}")

# Load BM25
bm25_load = bm25_service.load("document-id")
print(f"BM25 loaded: {bm25_load.is_success}")
print(bm25_load.index)  # Dict of texts
```

### View Logs

```python
# Logs are written through ILogger interface
# Check system logs for hybrid search operations
# Look for: "hybrid_search_in_conversation", "FAISS search", "BM25 search"
```

## Testing

### Unit Test Example

```python
import numpy as np
from backend.apps.services.rag_base.hybrid_search_service import HybridSearchService
from backend.apps.services.rag_base.locate.locate_service import LocateService
from sys_services.logging import Logger
from pathlib import Path

# Setup
logger = Logger()
locate_service = LocateService(metadata_dir=Path("tests/metadata"), logger=logger)
hybrid_search = HybridSearchService(locate_service, logger)

# Test
results = hybrid_search.search(
    document_id="test-doc",
    query_text="test query",
    query_vector=np.random.randn(384).astype(np.float32),
    limit=5
)

assert len(results["results"]) <= 5
assert all("score" in r for r in results["results"])
assert all("sources" in r for r in results["results"])
```

## Migration from FAISS-Only

If you have existing documents indexed only with FAISS:

1. **Option A**: Re-upload documents (recreates both indexes)
2. **Option B**: Manually build BM25 index:

```python
from backend.apps.services.rag_base.locate.locate_service import LocateService
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName

locate_service = LocateService(metadata_dir=Path("metadata"), logger=logger)
bm25_service = locate_service.get_vector_store(EBackendStorageName.BM25)

# Get chunks from Redis cache or database
chunks = get_document_chunks("document-id")
texts_map = {f"chunk-{i}": text for i, text in enumerate(chunks)}

# Create and upsert BM25 index
index = bm25_service.create_index()
bm25_service.upsert(texts_map, vector_id="document-id")
```

## Known Limitations

1. **BM25 Scoring**: Current implementation uses simple word matching, not full BM25 algorithm. For production, consider using `rank_bm25` library:
   ```bash
   pip install rank-bm25
   ```

2. **Query Embedding**: Uses configured embedding model (default: Mistral). Ensure embedding model is available.

3. **Metadata Directory**: Both FAISS and BM25 use same metadata directory. Ensure sufficient disk space.

## Future Improvements

- [ ] Implement full BM25 algorithm with IDF weighting
- [ ] Support for Elasticsearch as BM25 backend
- [ ] Query expansion (synonyms, lemmatization)
- [ ] Dynamic weight adjustment based on query type
- [ ] Caching of merged results
- [ ] Multi-language support

## Related Files

- **Backend job orchestration**: [backend/apps/job/upload_job.py](../../backend/apps/job/upload_job.py)
- **Conversation search**: [backend/apps/job/conversation_job.py](../../backend/apps/job/conversation_job.py)
- **BM25 service**: [backend/apps/services/rag_base/locate/bm25_service.py](../../backend/apps/services/rag_base/locate/bm25_service.py)
- **Hybrid search**: [backend/apps/services/rag_base/hybrid_search_service.py](../../backend/apps/services/rag_base/hybrid_search_service.py)
- **Enum values**: [backend/apps/core/enums/e_backend_storage_name.py](../../backend/apps/core/enums/e_backend_storage_name.py)
