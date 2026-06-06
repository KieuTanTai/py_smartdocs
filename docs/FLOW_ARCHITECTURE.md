# SmartDocs RAG System - Complete Flow Architecture

## System Overview
```
┌─────────────┐
│  Frontend   │ (Streamlit)
│(Components) │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌──────────────────┐
│  API Gateway     │ (Django URLs)
│ (urls.py views)  │ - Validate Input (Layer 1)
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────┐
│  Application Layer           │ (apps/application/)
│ - Business Logic             │ - Validate (Layer 2)
│ - Data Preparation           │ - Exception Handling
│ - Call Job Manager           │ - Get Repositories
└──────┬──────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Job Manager (Factory)       │ (apps/job/job_manager.py)
│ - Create Job Instances       │ - Schedule Tasks
│ - Monitor Job Status         │ - Handle Async
└──────┬──────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Tasks (Background Jobs)     │ (apps/tasks/)
│ - Document Processing Task   │ - Extraction
│ - Message/Chat Task          │ - Normalization
│ - Conversation Task          │ - Chunking
│                              │ - Embedding
└──────────────────────────────┘
```

## Detailed Process Flows

### Flow 1: Document Upload Pipeline
```
┌─ REQUEST ─────────────────────────────────────────────────────────┐
│ Frontend: {file, provider, model, conversation_id}               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                    API Layer 1 Validation
                            │
                            ▼
        ┌─── application/upload_document() ───┐
        │  Layer 2 Validation                  │
        │  - Check file size, type             │
        │  - Check conversation exists         │
        │  - Prepare context                   │
        └────────────┬────────────────────────┘
                     │
        job_manager.create_upload_job()
                     │
        ┌────────────▼──────────────────────┐
        │ Task: process_document_task()      │
        │ (Async/Background)                 │
        └────────────┬──────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼──────┐        ┌──────▼─────┐
    │ Storage   │        │ Extraction │
    │ (save to  │        │ (read PDF  │
    │ /storage) │        │ get text)  │
    └───────────┘        └──────┬─────┘
                                │
                    ┌───────────▼──────────┐
                    │ Normalization Task   │
                    │ (clean text)         │
                    └───────────┬──────────┘
                                │
    ┌───────────────────────────▼──────────────────────────────┐
    │ Chunking + Save Cache + Generate IDs                    │
    │                                                          │
    │ Input: normalized_text, file_id=abc                     │
    │ Process:                                                │
    │  1. Create chunks: [chunk1, chunk2, chunk3...]         │
    │  2. chunks_count = len(chunks) = 3                     │
    │  3. Generate IDs: abc:1, abc:2, abc:3                 │
    │  4. Tuple format: [(abc:1, chunk[0]),                 │
    │                    (abc:2, chunk[1]),                 │
    │                    (abc:3, chunk[2])]                 │
    │  5. Save to Cache: {                                  │
    │      file_id: abc,                                    │
    │      chunks: {                                        │
    │        "abc:1": chunk[0],                            │
    │        "abc:2": chunk[1],                            │
    │        "abc:3": chunk[2]                             │
    │      }                                               │
    │    }                                                 │
    │  6. Persist to file: metadata/cache/{file_id}.json  │
    └───────────────────────────┬──────────────────────────┘
                                │
    ┌───────────────────────────▼──────────────────────┐
    │ Embedding + Save (for all uploaded files)        │
    │                                                  │
    │ Input: all tuples from all files                │
    │ Process:                                        │
    │  1. Stack all chunk tuples from cache           │
    │  2. Extract chunk texts: [all_chunks...]        │
    │  3. Call LLM.embed(): vectors = np.array       │
    │  4. Create ids array: np.array([abc:1,         │
    │                                  abc:2,         │
    │                                  abc:3,...],    │
    │                                 dtype=int64)   │
    │  5. vstack_result = np.vstack(all_vectors)    │
    │  6. file_key = hash(vstack_result)            │
    │     NOTE: file_key ≠ upload file_id (abc)!    │
    │  7. Save to FAISS:                            │
    │      - file_id: abc                           │
    │      - file_key: sha256(vstack_hash)         │
    │      - vectors: vstack_result                │
    │      - metadata/faiss/{file_key}.faiss       │
    │  8. Insert to DB (faiss_index table):        │
    │      - file_id, file_key, chunks_count, etc  │
    └───────────────────────────┬──────────────────┘
                                │
                    ┌───────────▼──────────┐
                    │ Update Document DB   │
                    │ - status = "indexed" │
                    │ - embedding_time     │
                    │ - total_chunks       │
                    └───────────┬──────────┘
                                │
                    ┌───────────▼──────────┐
                    │ Return to Frontend   │
                    │ {uuid, status,       │
                    │  chunks_count,       │
                    │  timing...}          │
                    └──────────────────────┘
```

### Flow 2: Chat/Message Pipeline
```
REQUEST:
┌──────────────────────────────────────────┐
│ Frontend: {conversation_id,              │
│           message_type: "normal",        │
│           model: "gemini",               │
│           user_input: "question"}        │
└───────────────────┬──────────────────────┘
                    │
            API Layer 1 Validation
                    │
                    ▼
    ┌─ application/send_message() ─┐
    │ Layer 2 Validation            │
    │ - Check conversation exists   │
    │ - Check model available       │
    │ - Prepare message context     │
    └────────────┬──────────────────┘
                 │
    job_manager.create_message_job()
                 │
    ┌────────────▼─────────────────┐
    │ Task: process_message_task() │
    │ (May be async or sync)       │
    └────────────┬─────────────────┘
                 │
    ┌────────────▼──────────────────────┐
    │ Retrieval Stage                   │
    │ - Get conversation documents      │
    │ - Load FAISS vectors for each doc │
    │ - Embed user_input                │
    │ - Search vectors: get top K       │
    │ - Revert text from vectors        │
    └────────────┬──────────────────────┘
                 │
    ┌────────────▼──────────────────────┐
    │ Context Creation                  │
    │ - Build context from chunks       │
    │ - Format retrieved chunks         │
    │ - Combine from multiple files     │
    └────────────┬──────────────────────┘
                 │
    ┌────────────▼──────────────────────┐
    │ LLM Generation                    │
    │ - Get model instance              │
    │ - Build prompt                    │
    │ - Call LLM.generate()             │
    │ - Get response                    │
    └────────────┬──────────────────────┘
                 │
    ┌────────────▼──────────────────────┐
    │ Save Message to DB                │
    │ - Save user message               │
    │ - Save assistant response         │
    │ - Record timings (retrieval,      │
    │   generation, total)              │
    └────────────┬──────────────────────┘
                 │
    ┌────────────▼──────────────────────┐
    │ Return Response to Frontend       │
    │ {response, timing, metadata}      │
    └──────────────────────────────────┘
```

### Flow 3: Delete Conversation (Transactional)
```
REQUEST: {conversation_id}
    │
    ▼
Application validation
    │
    ├─ Begin Transaction
    │
    ├─ Delete messages (Message table)
    │
    ├─ Get FAISS file_keys from
    │  conversation_files
    │
    ├─ Delete conversation_files records
    │
    ├─ Delete FAISS vectors from memory
    │
    ├─ Delete FAISS files:
    │  metadata/faiss/{file_key}.faiss
    │
    ├─ Delete conversation record
    │
    └─ Commit Transaction
```

## Data Models

### Conversation Flow Data
```python
# Input to application layer
ConversationRequest:
  - conversation_id: UUID
  - message_type: str ("normal" | "cli")
  - model: str (provider.model_name)
  - user_input: str

# Document Upload Response
DocumentUploadResponse:
  - file_id: UUID
  - chunks_count: int
  - status: str ("processing" | "indexed")
  - created_at: datetime
  - embedding_summary: dict
    - total_chunks: int
    - embedding_time: float
    - cache_path: str

# Chunk ID Format
chunk_id = f"{file_id}:{chunk_index}"
# Example: "abc-123:1", "abc-123:2", "abc-123:3"

# Cache Structure
{
  "file_id": "abc-123",
  "chunks_count": 3,
  "chunks": {
    "abc-123:1": "chunk text 1",
    "abc-123:2": "chunk text 2", 
    "abc-123:3": "chunk text 3"
  },
  "created_at": "2024-01-01T10:00:00Z",
  "persist_path": "metadata/cache/{file_id}.json"
}

# FAISS Index Structure
{
  "file_id": "abc-123",
  "file_key": "sha256_hash_of_vstack",
  "chunks_count": 3,
  "vectors": np.ndarray(shape=(3, 384)),
  "ids": np.array(["abc-123:1", "abc-123:2", "abc-123:3"], dtype=object),
  "persist_path": "metadata/faiss/{file_key}.faiss"
}
```

## Database Schema

### Key Tables
```
Conversation:
  - conversation_id: UUID PK
  - conversation_title: str
  - provider_name: str
  - model_name: str
  - status: enum ("preparing", "ready", "failed")
  - created_at: datetime

ConversationFiles (M2M):
  - id: PK
  - conversation_id: FK
  - faiss_index_id: FK (to Document)

Document:
  - faiss_index_id: UUID PK
  - faiss_index_file_name: str
  - file_path: str
  - file_key: str (sha256 hash)
  - status: enum ("uploaded", "processing", "indexed")
  - chunks_count: int
  - created_at: datetime

Message:
  - message_id: UUID PK
  - conversation_id: FK
  - role: enum ("user", "assistant")
  - content: text
  - retrieval_time: float
  - generation_time: float
  - total_time: float
  - created_at: datetime

FAISSIndex (metadata):
  - id: PK
  - file_key: str (unique)
  - file_id: UUID FK
  - chunks_count: int
  - persist_path: str
  - vectors_shape: str (e.g., "3,384")
  - created_at: datetime
```

## Implementation Layers

### 1. API Gateway (backend/api/)
- Initial request validation
- Format response
- Handle HTTP errors

### 2. Application Layer (backend/apps/application/)
- Business logic validation
- Data preparation
- Exception handling
- Call job manager
- Benchmark timings

### 3. Job Manager (backend/apps/job/job_manager.py)
- Factory pattern for jobs
- Create and schedule tasks
- Monitor job status
- Handle retries

### 4. Tasks (backend/apps/tasks/)
- Document processing task:
  - Extract → Normalize → Chunk → Embed → Save
- Message task:
  - Retrieve → Generate → Save
- Conversation task:
  - Prepare → Bootstrap

### 5. Core Services (backend/apps/core/)
- Chunking (already implemented)
- Normalization (already implemented)
- Interfaces for LLM, cache, vector store

### 6. LLM Services (backend/apps/llm/)
- Provider implementations (Gemini, Mistral, Ollama)
- OCR capabilities
- Embedding generation
- Text generation

### 7. Storage (backend/apps/services/)
- FAISS vector store
- Database models (Django ORM)
- Cache service (Redis)

## Key Implementation Notes

1. **Chunking IDs**: Format `{file_id}:{chunk_index}` starting from 1
2. **File Key**: SHA256 hash of np.vstack result, NOT the upload file_id
3. **Cache Persistence**: JSON format in `metadata/cache/{file_id}.json`
4. **FAISS Persistence**: `metadata/faiss/{file_key}.faiss`
5. **Transactions**: Critical for delete operations to maintain consistency
6. **Async Processing**: Use job manager for long-running tasks
7. **Benchmarking**: Track timing at each stage for performance analysis
