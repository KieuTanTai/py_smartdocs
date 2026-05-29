# RULES

## Project Architect

Frontend:

- `frontend`: using shiny with css + js for build ui and handle request from users
- `frontend/components/`: define components on UI for index.py
- `frontend/assets`: resources for ui components, includes css & js

Backend:

### 1. Goal: initialize a django backend

- Django + Django REST framework
- Mariadb as the transactional database
- Faiss, Qdrant as the vector database (Qdrant for gemini)
- Langchain-based retrieval boundary
- LLM interace for Gemini, Mistral and other (Ollama or Nvidia)
- Background processing for normalization, indexing, and sumarization
- Conversation history persistence
- Multi-file document upload
- Async-safe runtime boundaries so long-running work does not block request handling

This phase only establishes the project skeleton, interfaces, utilities, and baseline API surface. It does not implement full OCR, production auth, or production-grade retrieval quality.

### 2. Constraints and decissions

- Framework: Django + DRF
- API style: JSON REST API
- Auth: none in this phase
- Document support: multi-file upload
- Conversation support: one conversation may reference many documents
- Chat history: persisted in Mariadb
- Background work: normalization, chunking, vector indexing, and summary generation
- Retrieval order: normalize -> store/search vector DB -> build context -> call LLM interface
- Provider strategy: real Gemini/Mistral/Others adapters with fallback when config is missing
- Runtime strategy: ASGI + async HTTP clients + background worker so request threads are not blocked
- Database strategy: support both Mariadb in Docker and external Mariadb via environment configuration.

### 3. Recommended Architecture

Use a modular monolith.
This keeps deployment simple while giving clear boundaries between upload, chat, retrieval, and provider logic. The system remains a single Django project, but domain responsibilities are split into focused apps and services.

Project Layout:

```text
backend/
    api/
    apps/
        application/
            conversations/
                conversation.py
            messages/
                message.py
        core/
            extract_file/
            embedding/
            locate/
            responses/
        llm/
            gemini.py
            ollama.py
            other.py
        job/
        exceptions/
        config/
        documents/
            models.py
            serializers.py
            views.py
            urls.py
        interfaces/
            base.py
        services/
            base_pipeline/
                normalize_service.py
                chunking_service.py
                indexing_service.py
                search_service.py
                locate_service.py
                extract_content_service.py
                summarization_service.py
            graph_pipeline/
            chat/
                models.py
                serializers.py
                views.py
                urls.py
        utils/
        media/
        tasks/
            document_tasks.py
            conversation_tasks.py
        requirements/
frontend/
    assets/
    components/
    tests/
sys_services/
    enums/
    read_config/

```

Responsibilities By Domain:

- `core`
  - handle base of pipeline: extract -  embed - locate - response and llm models
- `llm`
  - LLM interface, provider selection, real provider clients, mock fallback
- `documents`
  - document metadata, file upload, file storage abstraction, document status APIs
- `services/base_pipeline/`
  - implements base pipeline using core entities
- `services/graph_pipeline/`
  - implements graph pipeline using core entities
- `services/chat`
  - conversations, messages, history APIs, conversation-document relationships
- `application`
  - normalization, chunk preparation, indexing, vector search, summary generation
- `jobs`
  - Celery tasks and orchestration for background processing

### 4. Runtime Model

Web Runtime:

- Django runs under ASGI
- DRF handles REST endpoints
- Outbound provider calls use an async HTTP client
- The API process should return quickly and avoid performing normalization or indexing inline

Background Runtime:

Use Celery + Redis for queue and worker processing.

Reason:

- Upload and conversation preparation should not block request handling
- Normalization, chunking, indexing, and summarization are background responsibilities
- The queue boundary is cleaner than relying on request threads for long-running work

Persistence:

- Mariadb stores transactional data and history
- Chat history, messages, and conversation-document mappings are persisted in Mariadb
- Faiss/Qdrant stores vectors and searchable chunk metadata
- Files are stored in Django media storage for now (on mistral cloud if using mistral api branch)

Core User Flows:

- Upload Documents:

1. User uploads one or more files
2. API stores files and document metadata in Mariadb
3. API returns immediately with `processing_status=uploaded`
4. Background task starts:
   - extract content
   - normalize content
   - create chunks
   - upsert chunks to Qdrant/Faiss
   - generate summary
5. Document status becomes `indexed` or `failed`

Create Conversation:

1. User creates a conversation with one or more `document_ids`
2. Conversation is created in Mariadb
3. If any attached document is not ready, conversation starts as `preparing`
4. Background task checks document readiness and can generate a bootstrap assistant summary message
5. When preparation completes, conversation becomes `ready`

Ask A Question:

1. User posts a message to a conversation
2. If conversation is `preparing`, API returns a non-ready response and current state
3. If conversation is `ready`:
   - save user message
   - run retrieval search against Qdrant/Faiss
   - build prompt context
   - call selected LLM interface
   - save assistant message
   - return answer plus retrieval metadata

### 6. Data Model

Document:

Stores uploaded file metadata.

- Suggested fields:
  - `id`
  - `title`
  - `original_filename`
  - `file_path`
  - `mime_type`
  - `size_bytes`
  - `source`
  - `status`
  - `processing_status`
  - `summary_status`
  - `summary`
  - `error_message`
  - `created_at`
  - `updated_at`

- Suggested statuses:
  - `uploaded`
  - `processing`
  - `indexed`
  - `failed`

DocumentIndex:

Stores index metadata only, not vectors.

- Suggested fields:
  - `id`
  - `document`
  - `vector_collection`
  - `chunk_count`
  - `index_status`
  - `last_indexed_at`
  - `created_at`
  - `updated_at`

Conversation:

- Suggested fields:
  - `id`
  - `title`
  - `provider`
  - `model`
  - `system_prompt`
  - `status`
  - `created_at`
  - `updated_at`

- Suggested statuses:

  - `preparing`
  - `ready`
  - `failed`

ConversationDocument:

Many-to-many join table between conversations and documents.
Stored in Mariadb to preserve chat-to-file mapping.

- Suggested fields:
  - `id`
  - `conversation`
  - `document`
  - `created_at`

Message:

Stored in Mariadb as the canonical chat history record.

- Suggested fields:
  - `id`
  - `conversation`
  - `role`
  - `content`
  - `provider`
  - `model`
  - `tokens_input`
  - `tokens_output`
  - `latency_ms`
  - `metadata_json`
  - `created_at`

- Suggested roles:
  - `system`
  - `assistant`
  - `user`

### 7. API Surface

Base prefix: `/api`

Health:

- `GET /api/health/`
  - checks application, Mariadb, Redis, and Qdrant reachability

Documents:

- `GET /api/documents/`
  - list documents
- `POST /api/documents/upload/`
  - upload one or many files
- `GET /api/documents/{id}/`
  - document detail
- `DELETE /api/documents/{id}/`
  - delete metadata and optionally stored file
- `GET /api/documents/{id}/status/`
  - processing/indexing status
- `POST /api/documents/{id}/index/`
  - manually trigger indexing job
- `POST /api/documents/index/bulk/`
  - trigger indexing for multiple documents

Conversations:

- `GET /api/application/conversations/`
  - list conversations
- `POST /api/application/conversations/`
  - create conversation and attach `document_ids`
- `GET /api/application/conversations/{id}/`
  - conversation detail
- `GET /api/application/conversations/{id}/status/`
  - readiness state for FE polling
- `PATCH /api/application/conversations/{id}/documents/`
  - replace or update attached documents

Messages:

- `GET /api/application/conversations/{id}/messages/`
  - fetch chat history
- `POST /api/application/conversations/{id}/messages/`
  - send message, retrieve context, call provider, save response

Services Retrieval Debug:

- `GET /api/services/search/`
  - debug endpoint to test vector search against current documents

### 8. Background Processing Design

Why Background Jobs Are Required:

Normalization, indexing, and summarization should not run inside request-response handling. These steps may involve file IO, parsing, vector operations, network calls, and provider latency. Running them inline would block workers and reduce concurrency.

Background Tasks:

Recommended task boundaries:

- `process_document(document_id)`
  - load file
  - normalize text
  - create chunks
  - store vectors in Qdrant
  - generate summary
  - update document statuses
- `prepare_conversation(conversation_id)`
  - verify attached documents are ready
  - create or refresh conversation bootstrap summary message
  - move conversation to `ready` or `failed`

Conversation Bootstrap Message:a

When a conversation becomes ready, create an assistant message that summarizes the attached documents. This gives the frontend something useful to render immediately and matches the intended product flow: upload first, prepare in the background, then wait for the user’s next question.

### 9. Normalization Design

What Normalization Must Do:

- Normalization is the preprocessing stage before chunking and indexing. In this scaffold it should:
  - load file content or extracted text
  - standardize line endings and whitespace
  - remove repeated empty blocks
  - preserve readable paragraph boundaries
  - attach document metadata to the normalized payload
  - produce a deterministic text output that downstream chunking can consume

This phase does not need full OCR or advanced PDF extraction quality yet. It only needs a clean service boundary and baseline text normalization flow.

Where The Code Goes:

- Primary code location:

  - `apps/services/{pipeline}/normalization_service.py`

- Supporting code:

  - `apps/documents/services/storage.py`
    - file loading helpers
  - `apps/application/langchain/{pipeline}/pipelines.py`
    - orchestration with chunking/indexing
  - `apps/jobs/tasks/document_tasks.py`
    - worker entrypoint that calls normalization

Expected Interface:

- Suggested service contract:

```python
class NormalizationService:
    async def normalize_document(self, document: Document) -> NormalizedDocument:
        ...
```

- The return object should include:
  - `document_id`
  - `normalized_text`
  - `metadata`
  - `content_hash`

### 10. Vector Store And Search Design

What Vector Storage Must Do:

- The vector layer must:
  - receive normalized text chunks
  - generate or accept embeddings through the chosen embedding pipeline
  - upsert chunk vectors into Qdrant
  - store chunk metadata for filtering and traceability
  - support similarity search by conversation and attached documents

What Search Must Do:

- Search should:

  - accept a user query and target document scope
  - perform similarity search in Qdrant
  - return top matching chunks with metadata
  - provide enough context for prompt building

This scaffold can keep ranking logic simple and focus on stable interfaces.

Where The Code Goes:

- Primary code locations:
  - `apps/services/{pipeline}/{qdrant/faiss/others}.py`
  - `apps/services/{pipeline}/indexing_service.py`
  - `apps/services/{pipeline}/search_service.py`
  - `apps/services/{pipeline}/chunking_service.py`

- LangChain integration boundary:
  - `apps/services/langchain/pipelines.py`

- Worker integration:
  - `apps/jobs/tasks/document_tasks.py`

Expected Interfaces:

- Suggested contracts:

```python
class VectorStoreService:
    async def upsert_document(self, document: Document, chunks: list[ChunkPayload]) -> IndexResult:
        ...

    async def search(self, query: str, document_ids: list[int], limit: int = 5) -> list[SearchHit]:
        ...
```

The Qdrant adapter should stay behind this interface so the storage backend can be replaced later without rewriting chat logic.

### 11. LLM Interface Design

What The LLM Layer Must Do:

- The LLM layer must:
  - expose a provider-agnostic completion interface
  - support Gemini and Ollama adapters
  - select provider by conversation or request config
  - support real calls when environment variables are present
  - fall back to mock responses when provider config is absent
  - return normalized response metadata to the chat layer

Where The Code Goes

- Primary code locations:
  - `apps/services/llm/interfaces/base.py`
  - `apps/services/llm/clients/gemini.py`
  - `apps/services/llm/clients/ollama.py`
  - `apps/services/llm/clients/mock.py`
  - `apps/services/llm/services/provider_factory.py`
  - `apps/services/llm/services/completion_service.py`

- Chat integration:

- `apps/application/messages/message.py`

Expected Interfaces

- Suggested contracts:

```python
class LLMClient:
    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        ...
```

The factory should resolve a provider name such as `gemini` or `ollama` and return an adapter implementing `LLMClient`.

Provider Notes

- `GeminiClient`
  - reads API key and model from environment
  - uses async HTTP calls
- `OllamaClient`
  - reads base URL and model from environment
  - uses async HTTP calls to the local or remote Ollama server
- `MockClient`
  - returns deterministic fake answers and metadata
  - used when provider configuration is incomplete

### 12. Prompt And Retrieval Composition

Message handling should follow this order:

1. save user message
2. search vector store using conversation documents
3. build context from top chunks
4. create completion request
5. call provider client
6. save assistant response
7. return answer, citations metadata, and provider info

The chat service should never directly depend on Qdrant SDK or provider-specific APIs. Those dependencies remain behind retrieval and LLM service boundaries.

### 13. Frontend Integration Contract

The frontend will need clear status-driven flows.

Upload Flow

- Frontend behavior:

1. call `POST /api/documents/upload/` with multiple files
2. render the returned document list with `processing_status`
3. poll `GET /api/documents/{id}/status/` until document becomes `indexed` or `failed`

Conversation Creation Flow

- Frontend behavior:

1. call `POST /api/conversations/` with selected `document_ids`
2. inspect returned `status`
3. if `preparing`, poll `GET /api/conversations/{id}/status/`
4. once `ready`, call `GET /api/conversations/{id}/messages/`
5. render the bootstrap summary message before the user sends the next question

Chat Flow

- Frontend behavior:

1. call `POST /api/conversations/{id}/messages/`
2. if conversation is still `preparing`, disable the input or show waiting state
3. if response is successful, append both user and assistant messages to the UI
4. optionally show provider/model/debug metadata in developer mode

FE Error Cases

- Frontend should handle:
  - document processing failure
  - conversation preparation failure
  - provider unavailable but mock fallback active
  - retrieval returns no relevant chunks

Suggested Response Shape

- Keep responses consistent and explicit:
  - `success`
  - `message`
  - `data`
  - `errors`

- For status endpoints, include:
  - `status`
  - `processing_status`
  - `summary_status`
  - `ready_for_chat`
  - `error_message`

### 14. Configuration Design

Environment Variables

Core:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`

Mariadb:

- `DB_ENGINE`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_USE_DOCKER`

Redis/Celery:

- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

Qdrant:

- `QDRANT_URL`
- `QDRANT_API_KEY`
- `QDRANT_COLLECTION`

Gemini:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`

Mistral:

- `MISTRAL_API_KEY`
- `MISTRAL_MODEL`

Ollama:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`

Storage:

- `MEDIA_ROOT`
- `MEDIA_URL`

Docker Compose Expectations

Compose should support:

- Django web
- Celery worker
- Redis
- Qdrant
- optional Mariadb container

The Mariadb service should be easy to enable or bypass. The Django config should accept either:

- Docker Mariadb host such as `Mariadb`
- external Mariadb host from `.env`
