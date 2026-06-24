# Bug Fix Summary: RAG Context Retrieval Issue

## Problem Description

All three LLM providers (Gemini, Mistral, Ollama) were returning mock error responses with the message:
```
⚠️ **Khong the ket noi den model [provider] ([model]).**
Khong tim thay ngon ngu phu hop trong tai lieu de tra loi.
```

Even though:
- All API keys were valid
- All providers worked correctly in isolation
- Documents were successfully uploaded and indexed
- FAISS indices were created

## Root Cause

The bug was in `backend/api/conversations/views.py` in the `_build_rag_context()` function.

**The Issue:**
- FAISS indices are stored by **conversation_id** (e.g., `019efa0c-c884-7750-9ade-9e38055e9c8a.faiss`)
- Metadata JSON files are stored by **document_id** (e.g., `91760add-0407-488d-9973-c2f45b69e1fe.json`)
- The code was trying to load metadata using conversation_id instead of document_id

```python
# BEFORE (WRONG):
vector_id = str(doc.documents_conversation.conversations_id)
metadata_path = METADATA_DIR / "docs" / f"{vector_id}.json"  # ❌ Uses conversation_id
```

This caused the metadata loading to fail, resulting in empty `chunk_texts` dictionary. When FAISS returned search results, there were no actual text chunks to retrieve, so the RAG context was empty.

With empty context, the LLM calls would fail (or return empty responses), triggering the exception handler which returned the mock Vietnamese error message.

## The Fix

Changed the code to use the correct document_id for loading metadata:

```python
# AFTER (CORRECT):
vector_id = str(doc.documents_conversation.conversations_id)  # For FAISS
document_id = str(doc.documents_id)  # For metadata
metadata_path = METADATA_DIR / "docs" / f"{document_id}.json"  # ✅ Uses document_id
```

## Additional Improvements Made

1. **Enhanced Error Logging**: Added traceback logging to exception handlers for better debugging
2. **Added Logging to RAG Context Building**: Added info logs to track embedding creation
3. **Added file_caller Parameters**: Improved traceability of LLM calls through the system
4. **Better Error Messages**: Added warning logs when FAISS index or metadata files are not found

## Files Modified

- `backend/api/conversations/views.py` - Fixed metadata loading bug and added logging

## Testing

### Diagnostic Scripts Created

1. **test_providers.py** - Tests all three LLM providers in isolation (all passed ✅)
2. **test_llm_direct.py** - Tests LLM integration through Django (all passed ✅)

### How to Verify the Fix

1. **Restart the Django server** to load the updated code:
   ```cmd
   python manage.py runserver
   ```

2. **Upload a document** through the Shiny frontend

3. **Send a query** about the document content

4. **Expected Result**: 
   - The LLM should return a proper answer based on document content
   - No more "Khong the ket noi den model" error messages
   - The `used_mock: false` field in the response
   - Non-zero `response_ms` in metrics

5. **Check logs** for confirmation:
   - Look for "Creating embedding for query..." messages
   - Look for "Successfully created embedding vector..." messages
   - No "Metadata file not found" warnings

## Why This Happened

The discrepancy between FAISS indexing (by conversation_id) and metadata storage (by document_id) likely arose from:
- FAISS indices being conversation-scoped (one conversation = one aggregated index)
- Metadata being document-scoped (one document = one metadata file)
- The code not consistently handling this difference

This is a common pattern mismatch that can happen when different parts of the system evolve independently.

## Prevention

To prevent similar issues:
1. Add unit tests for the RAG context building function
2. Add integration tests that verify end-to-end document upload → query flow
3. Add validation that checks metadata file exists before attempting FAISS search
4. Consider refactoring to use consistent IDs for both FAISS and metadata (or document the difference clearly)

## Related Code Patterns

If you see similar patterns elsewhere in the codebase, check:
- Any place that loads files using conversation_id vs document_id
- BM25 index loading (does it use the correct ID?)
- Cache key generation (does it use consistent IDs?)
