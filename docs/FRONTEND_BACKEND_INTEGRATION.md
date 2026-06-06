# Frontend-Backend Integration & API Endpoints

## API Gateway Structure

### 1. Document Upload Endpoints

#### POST `/api/v1/documents/upload`
**Request (Frontend → Backend):**
```python
{
    "file": <binary file>,
    "conversation_id": "uuid-v7",  # Optional, for attaching to conversation
}
```

**Response (Backend → Frontend):**
```python
{
    "status": 201,
    "data": {
        "id": "doc-uuid",
        "title": "filename.pdf",
        "status": "uploading",
        "created_at": "2024-01-01T10:00:00Z"
    }
}
```

**Flow:**
1. Frontend sends file via multipart/form-data
2. API Layer 1 Validation (file size, type)
3. DocumentApplication validates (Layer 2)
4. File saved to storage
5. DocumentModel created with status="uploaded"
6. Job Manager schedules DocumentUploadJob
7. Return document metadata to frontend

---

#### GET `/api/v1/documents`
**Request:** No body

**Response:**
```python
{
    "status": 200,
    "data": [
        {
            "id": "doc-uuid",
            "title": "document.pdf",
            "status": "indexed",  # uploaded, processing, indexed, failed
            "created_at": "2024-01-01T10:00:00Z"
        }
    ]
}
```

---

#### GET `/api/v1/documents/{doc_id}`
**Request:** No body

**Response:**
```python
{
    "status": 200,
    "data": {
        "id": "doc-uuid",
        "title": "document.pdf",
        "status": "indexed",
        "chunks_count": 145,
        "created_at": "2024-01-01T10:00:00Z"
    }
}
```

---

#### DELETE `/api/v1/documents/{doc_id}`
**Request:** No body

**Response:**
```python
{
    "status": 200,
    "data": {
        "message": "Document deleted successfully"
    }
}
```

---

### 2. Conversation Endpoints

#### POST `/api/v1/conversations`
**Request:**
```python
{
    "title": "My Analysis",
    "provider": "gemini",  # or "mistral", "ollama"
    "model": "gemini-2.0",
    "document_ids": ["doc-uuid-1", "doc-uuid-2"]
}
```

**Response:**
```python
{
    "status": 201,
    "data": {
        "id": "conv-uuid",
        "title": "My Analysis",
        "status": "ready",
        "created_at": "2024-01-01T10:00:00Z",
        "documents": [
            {
                "id": "doc-uuid-1",
                "title": "document1.pdf",
                "status": "indexed"
            },
            {
                "id": "doc-uuid-2",
                "title": "document2.pdf",
                "status": "indexed"
            }
        ]
    }
}
```

**Flow:**
1. API validation (Layer 1)
2. ConversationApplication validation (Layer 2)
3. ConversationModel created
4. Documents attached to conversation
5. Job Manager schedules ConversationPrepareJob
6. FAISS indices preloaded for retrieval
7. Bootstrap message prepared
8. Return conversation metadata

---

#### GET `/api/v1/conversations`
**Response:**
```python
{
    "status": 200,
    "data": [
        {
            "id": "conv-uuid",
            "title": "My Analysis",
            "status": "ready",
            "created_at": "2024-01-01T10:00:00Z"
        }
    ]
}
```

---

#### GET `/api/v1/conversations/{conv_id}`
**Response:**
```python
{
    "status": 200,
    "data": {
        "id": "conv-uuid",
        "title": "My Analysis",
        "status": "ready",
        "created_at": "2024-01-01T10:00:00Z",
        "documents": [
            {
                "id": "doc-uuid-1",
                "title": "document1.pdf",
                "status": "indexed"
            }
        ]
    }
}
```

---

#### DELETE `/api/v1/conversations/{conv_id}`
**Request:** No body

**Response:**
```python
{
    "status": 200,
    "data": {
        "message": "Conversation and associated data deleted"
    }
}
```

**Flow (Transactional):**
1. Get conversation & documents
2. Begin transaction
3. Delete messages
4. Delete FAISS files from disk
5. Delete conversation_files records
6. Delete conversation record
7. Commit transaction
8. Clear from frontend

---

### 3. Message/Chat Endpoints

#### POST `/api/v1/conversations/{conv_id}/messages`
**Request:**
```python
{
    "content": "What is the main topic?",
    "type": "normal"  # or "cli"
}
```

**Response (Streaming or Polling):**
```python
# Option 1: Immediate response (for fast responses)
{
    "status": 200,
    "data": {
        "message_id": "msg-uuid",
        "role": "assistant",
        "content": "The main topic is...",
        "metrics": {
            "retrieval_time": 0.234,
            "generation_time": 1.456,
            "total_time": 1.690
        }
    }
}

# Option 2: Job reference (for async responses)
{
    "status": 202,
    "data": {
        "job_id": "job-uuid",
        "status": "processing",
        "message": "Processing your message..."
    }
}
```

**Flow:**
1. API validation (Layer 1)
2. MessageApplication validation (Layer 2)
3. User message saved to database
4. Job Manager schedules MessageProcessJob
5. Task retrieves relevant chunks from FAISS
6. Context created from chunks
7. LLM generates response
8. Assistant message saved to database
9. Response returned to frontend with timing metrics

---

#### GET `/api/v1/conversations/{conv_id}/messages`
**Query Parameters:**
```
?limit=50&offset=0
```

**Response:**
```python
{
    "status": 200,
    "data": {
        "conversation_id": "conv-uuid",
        "messages": [
            {
                "id": "msg-uuid-1",
                "role": "user",
                "content": "What is the main topic?",
                "created_at": "2024-01-01T10:00:00Z"
            },
            {
                "id": "msg-uuid-2",
                "role": "assistant",
                "content": "The main topic is...",
                "metrics": {
                    "retrieval_time": 0.234,
                    "generation_time": 1.456,
                    "total_time": 1.690
                },
                "created_at": "2024-01-01T10:00:05Z"
            }
        ],
        "count": 2,
        "total": 2
    }
}
```

---

#### GET `/api/v1/conversations/{conv_id}/messages/{msg_id}`
**Response:**
```python
{
    "status": 200,
    "data": {
        "id": "msg-uuid",
        "role": "assistant",
        "content": "...",
        "metrics": {...},
        "created_at": "2024-01-01T10:00:00Z"
    }
}
```

---

### 4. Job Status Endpoints

#### GET `/api/v1/jobs/{job_id}`
**Response:**
```python
{
    "status": 200,
    "data": {
        "job_id": "job-uuid",
        "job_type": "document_upload",
        "status": "completed",  # pending, running, completed, failed
        "result": {
            "file_id": "doc-uuid",
            "chunks_count": 145,
            "status": "indexed"
        },
        "error": null
    }
}
```

---

#### POST `/api/v1/jobs/{job_id}/cancel`
**Response:**
```python
{
    "status": 200,
    "data": {
        "job_id": "job-uuid",
        "status": "cancelled"
    }
}
```

---

## Frontend Implementation Examples

### Upload Document
```python
import requests

async def upload_document(file_path, conversation_id=None):
    """Upload document from frontend."""
    url = "http://backend:8000/api/v1/documents/upload"
    
    with open(file_path, "rb") as f:
        files = {"file": f}
        data = {"conversation_id": conversation_id}
        
        response = requests.post(url, files=files, data=data)
        
    return response.json()
```

### Send Message
```python
async def send_message(conversation_id, user_input):
    """Send message to conversation."""
    url = f"http://backend:8000/api/v1/conversations/{conversation_id}/messages"
    
    payload = {
        "content": user_input,
        "type": "normal"
    }
    
    response = requests.post(url, json=payload)
    
    # Handle response or job reference
    if response.status_code == 200:
        # Immediate response
        data = response.json()["data"]
        return data["content"]
    elif response.status_code == 202:
        # Async job - poll for completion
        job_id = response.json()["data"]["job_id"]
        return await poll_job(job_id)
```

### Poll Job Status
```python
import asyncio

async def poll_job(job_id, max_attempts=30):
    """Poll job status until completion."""
    url = f"http://backend:8000/api/v1/jobs/{job_id}"
    
    for attempt in range(max_attempts):
        response = requests.get(url)
        job_data = response.json()["data"]
        
        if job_data["status"] == "completed":
            return job_data["result"]
        elif job_data["status"] == "failed":
            raise Exception(f"Job failed: {job_data['error']}")
        
        await asyncio.sleep(1)  # Wait before next poll
    
    raise TimeoutError(f"Job {job_id} did not complete in {max_attempts} seconds")
```

---

## Error Handling

### Error Response Format
```python
{
    "status": 400,  # or 404, 500, etc.
    "error": {
        "code": "INVALID_FILE_TYPE",
        "message": "File type '.exe' not allowed. Allowed: .pdf, .txt, .docx",
        "details": {
            "provided": ".exe",
            "allowed": [".pdf", ".txt", ".docx"]
        }
    }
}
```

### Common Error Codes
- `400_BAD_REQUEST`: Invalid input validation
- `404_NOT_FOUND`: Resource not found (conversation, document, message)
- `409_CONFLICT`: Duplicate resource or state conflict
- `422_UNPROCESSABLE_ENTITY`: Business logic validation failed
- `500_INTERNAL_SERVER_ERROR`: Server error

---

## Performance Metrics

### Response Timing (Captured by backend)

**For Messages:**
```python
metrics = {
    "retrieval_time": 0.234,      # FAISS search
    "generation_time": 1.456,     # LLM generation
    "total_time": 1.690           # retrieval + generation
}
```

**For Documents:**
```python
metrics = {
    "extraction_time": 0.123,     # PDF/text extraction
    "normalization_time": 0.045,  # Text normalization
    "chunking_time": 0.078,       # Text chunking
    "embedding_time": 0.567,      # LLM embedding
    "total_time": 0.813           # All stages
}
```

---

## Frontend-Backend Interaction Flow

### Document Upload Flow
```
Frontend (Upload Button)
    ↓
API Layer 1 Validation
  - Check file exists
  - Check file size
  - Check file type
    ↓ (pass)
API Layer 2 (ApplicationLayer)
  - Validate file bytes
  - Validate conversation_id if provided
    ↓ (pass)
Save File to Storage
    ↓
Create DocumentModel
    ↓
Job Manager → DocumentUploadJob
    ↓
DocumentTaskExecutor:
  - Extract content
  - Normalize text
  - Chunk text
  - Generate chunk IDs
  - Save to cache
  - Embed chunks (LLM call)
  - Save to FAISS
  - Update DocumentModel status → "indexed"
    ↓
Return Response to Frontend
    ↓
Frontend (Update UI with status)
```

### Message Flow
```
Frontend (Send Message)
    ↓
API Layer 1 Validation
    ↓
API Layer 2 (ApplicationLayer)
  - Validate conversation exists
  - Validate input length
  - Save user message to DB
    ↓
Job Manager → MessageProcessJob
    ↓
MessageTaskExecutor:
  - Retrieve chunks from FAISS
  - Create context
  - Call LLM with context
  - Get response
    ↓
Application saves assistant message to DB
    ↓
Return Response with metrics
    ↓
Frontend (Display response + timings)
```

### Delete Conversation Flow
```
Frontend (Delete Button)
    ↓
API Layer 1 Validation
    ↓
API Layer 2 (ApplicationLayer)
    ↓
BEGIN TRANSACTION
    ↓
Get conversation documents
    ↓
Delete messages from DB
    ↓
Delete conversation_files records
    ↓
Delete FAISS files from disk
    ↓
Delete conversation record
    ↓
COMMIT TRANSACTION
    ↓
Return success response
    ↓
Frontend (Remove from UI)
```

---

## Testing Frontend-Backend Integration

### Test Scenario 1: Upload and Message
```python
def test_document_upload_and_message():
    """Test complete flow from upload to message."""
    
    # 1. Create conversation
    conv_response = post("/api/v1/conversations", {
        "title": "Test",
        "provider": "gemini",
        "model": "gemini-2.0"
    })
    conv_id = conv_response["data"]["id"]
    
    # 2. Upload document
    doc_response = post("/api/v1/documents/upload", 
        files={"file": open("test.pdf", "rb")},
        data={"conversation_id": conv_id}
    )
    doc_id = doc_response["data"]["id"]
    
    # 3. Poll document status until indexed
    while True:
        status = get(f"/api/v1/documents/{doc_id}")
        if status["data"]["status"] == "indexed":
            break
        time.sleep(1)
    
    # 4. Send message
    msg_response = post(f"/api/v1/conversations/{conv_id}/messages", {
        "content": "What is the main topic?"
    })
    
    # 5. Verify response
    assert msg_response["data"]["role"] == "assistant"
    assert len(msg_response["data"]["content"]) > 0
    assert "metrics" in msg_response["data"]
    
    print("✓ Full flow test passed")
```

---

## Deployment Considerations

### Development Setup
```bash
# Backend
python manage.py runserver 0.0.0.0:8000

# Frontend  
streamlit run frontend/app.py --server.port 8501
```

### Production Setup
```bash
# Use Gunicorn for backend
gunicorn -w 4 -b 0.0.0.0:8000 app.wsgi:application

# Use production Streamlit settings
streamlit run frontend/app.py \
  --server.port 8501 \
  --logger.level=warning
```

### CORS Configuration
```python
# Add to Django settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://localhost:3000",
    "https://example.com"
]
```
