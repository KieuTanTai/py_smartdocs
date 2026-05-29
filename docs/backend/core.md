# Core Module

## Purpose

`core` main focus of project, just implements chunking, normalize for pipeline rag, and define interfaces for external modules.

Its job is:

- normalize content
- chunking
- define interfaces for external services (using on `extract`, `embedding`, `indexing`, `storage`)

## Main Files

- `backend/apps/core/normalize/normalize.py`
  - cleans raw text into a stable normalized form
- `backend/apps/core/chunk/chunker.py`
  - splits normalized text into chunks using LangChain text splitters
- `backend/apps/core/interfaces/`
  - define interfaces for external services, also for chunker.py and normalize.py

## Current Behavior

### Normalization

- collapses repeated whitespace
- reduces excessive blank lines
- preserves paragraph-ish separation
- returns a `NormalizedDocument` payload

### Chunking

- uses `RecursiveCharacterTextSplitter`
- produces chunk payloads with metadata

## Endpoint

- `GET /api/core/search/?query=...&document_ids=1&document_ids=2`

Useful for:

- manual retrieval checks
- FE/backend debugging
- validating search shape independently of chat

## Dependencies

- depends on `documents` for index metadata
- depends on LangChain splitter utilities
- is used by `jobs` during background processing
- is used by `chat` during message handling

## What To Extend Next

- replace stub vector adapter with real Qdrant collection operations
- add real embedding generation
- add metadata filters per document or conversation
- improve summaries beyond first-chunk truncation
