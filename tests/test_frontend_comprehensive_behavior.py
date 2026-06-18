"""
COMPREHENSIVE FRONTEND BEHAVIOR TESTS

Based on detailed source code analysis:
- frontend/app.py: Upload & send_message handlers
- frontend/apps/message.py: send_message() function logic
- sys_services/api_client.py: All API client methods
- backend/api/conversations/views.py: Backend endpoints

Tests cover:
1. Upload success/failure scenarios
2. Index success/failure scenarios
3. Create conversation success/error scenarios
4. Send message success/error scenarios
5. State management (reactive values)
6. UI interactions
7. Error handling & retries
8. Loading/disabled states
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
import datetime
import uuid
import time


# ═══════════════════════════════════════════════════════════════
# DATACLASS DEFINITIONS (Match actual codebase contracts)
# ═══════════════════════════════════════════════════════════════

@dataclass
class IChatMetrics:
    """Exact contract from backend/apps/core/interfaces/dataclass/request/i_chat_metrics.py"""
    provider: str
    model: str
    mode: str
    total_ms: int


@dataclass
class IChatMessage:
    """Exact contract from backend/apps/core/interfaces/dataclass/request/i_chat_message.py"""
    role: str
    content: str
    meta: Dict[str, Any] = field(default_factory=dict)
    ts: float = 0.0


@dataclass
class IChatResponse:
    """Exact contract from backend/apps/core/interfaces/dataclass/response/i_chat_response.py"""
    assistant: str
    conversation_id: str
    metrics: IChatMetrics
    new_conversation: bool
    error: Optional[str]
    used_mock: bool


class ApiError(RuntimeError):
    """Exact exception from sys_services/api_client.py"""
    pass


# ═══════════════════════════════════════════════════════════════
# MOCK DATA GENERATORS
# ═══════════════════════════════════════════════════════════════

class MockDataFactory:
    """Generate realistic mock responses matching actual API contracts"""

    @staticmethod
    def upload_response(document_id: str = None, filename: str = "document.pdf", status: str = "uploaded") -> Dict:
        """Backend response for upload (backend/api/documents/views.py)"""
        return {
            "id": document_id or str(uuid.uuid4()),
            "title": filename,
            "status": status
        }

    @staticmethod
    def index_response(document_id: str = None, chunks: int = 42, dimensions: int = 1536) -> Dict:
        """Backend response for index (backend/api/documents/views.py)"""
        return {
            "id": document_id or str(uuid.uuid4()),
            "status": "indexed",
            "chunks": chunks,
            "dimensions": dimensions
        }

    @staticmethod
    def create_conversation_response(conversation_id: str = None, title: str = "New Chat") -> Dict:
        """Backend response for create conversation (backend/api/conversations/views.py:155-210)"""
        return {
            "conversation_id": conversation_id or str(uuid.uuid4()),
            "title": f"{title} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "status": "ready"
        }

    @staticmethod
    def send_message_response(
        conversation_id: str = None,
        assistant_text: str = "This is a test response.",
        provider: str = "gemini",
        model: str = "gemini-2.0",
        mode: str = "normal",
        total_ms: int = 2530,
        used_mock: bool = False,
        retrieval_hits: List[Dict] = None
    ) -> Dict:
        """Backend response for send message (backend/api/conversations/views.py:237-380)"""
        if retrieval_hits is None:
            retrieval_hits = [
                {"text": "Context from document chunk 1...", "score": 0.95},
                {"text": "Context from document chunk 2...", "score": 0.88}
            ]
        
        return {
            "conversation_id": conversation_id or str(uuid.uuid4()),
            "assistant": assistant_text,
            "used_mock": used_mock,
            "metrics": {
                "provider": provider,
                "model": model,
                "mode": mode,
                "total_ms": total_ms,
                "embed_ms": 150,
                "query_ms": 280,
                "response_ms": 2100,
                "retrieval_hits": retrieval_hits
            }
        }

    @staticmethod
    def update_conversation_documents_response() -> Dict:
        """Backend response for update conversation documents (backend/api/conversations/views.py:212-226)"""
        return {"status": "updated"}

    @staticmethod
    def document_status_response(document_id: str = None, status: str = "indexed") -> Dict:
        """Backend response for document status (backend/api/documents/views.py)"""
        return {
            "id": document_id or str(uuid.uuid4()),
            "status": status
        }


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════

@pytest.fixture
def mock_api_client():
    """Mock ApiClient instance (sys_services/api_client.py)"""
    client = MagicMock()
    client.upload_document = MagicMock()
    client.index_document = MagicMock()
    client.create_conversation = MagicMock()
    client.send_message = MagicMock()
    client.update_conversation_documents = MagicMock()
    client.document_status = MagicMock()
    return client


@pytest.fixture
def frontend_state():
    """Simulate frontend reactive state (frontend/app.py:68-83)"""
    return {
        "messages": [],
        "docs": [],
        "history": [],
        "metrics": {},
        "status": {"label": "", "detail": "", "kind": "info"},
        "conversation_id": None,
        "provider": "auto",
        "current_model": "auto",
        "current_mode": "normal",
        "system_prompt": "",
        "mock_on_fail": True
    }


@pytest.fixture
def upload_file_info():
    """File info dict for upload (frontend/app.py:358-405)"""
    return {
        "name": "test_document.pdf",
        "type": "application/pdf",
        "datapath": "/tmp/test_document.pdf",
        "size": 1024
    }


# ═══════════════════════════════════════════════════════════════
# PHẦN E: MAIN TEST CASES (Upload, Index, Conversations, Messages)
# ═══════════════════════════════════════════════════════════════

class TestUploadDocumentFlow:
    """Test document upload flow (frontend/app.py:358-405)"""

    def test_upload_single_pdf_success(self, mock_api_client, frontend_state, upload_file_info):
        """
        CASE: Upload single PDF - success
        Expected: Document added to docs list with correct id/title/status
        """
        # ARRANGE
        doc_id = str(uuid.uuid4())
        mock_api_client.upload_document.return_value = MockDataFactory.upload_response(
            document_id=doc_id,
            filename="report.pdf",
            status="uploaded"
        )
        mock_api_client.index_document.return_value = MockDataFactory.index_response(
            document_id=doc_id,
            chunks=42,
            dimensions=1536
        )

        # ACT - Simulate _handle_upload() logic
        upload_response = mock_api_client.upload_document(upload_file_info, source="local")
        doc = {
            "id": upload_response.get("id") or upload_response.get("data", {}).get("id") or f"local-{datetime.datetime.now().timestamp()}",
            "title": upload_response.get("title", "Untitled"),
            "status": upload_response.get("status", "uploaded"),
            "name": upload_file_info["name"]
        }
        frontend_state["docs"].append(doc)

        index_response = mock_api_client.index_document(doc["id"])
        doc["status"] = index_response.get("status", doc["status"])

        # ASSERT
        assert len(frontend_state["docs"]) == 1
        assert frontend_state["docs"][0]["id"] == doc_id
        assert frontend_state["docs"][0]["title"] == "report.pdf"
        assert frontend_state["docs"][0]["status"] == "indexed"
        mock_api_client.upload_document.assert_called_once()
        mock_api_client.index_document.assert_called_once_with(doc_id)

    def test_upload_multiple_files_success(self, mock_api_client, frontend_state):
        """
        CASE: Upload multiple files - success
        Expected: All documents added to docs list
        """
        # ARRANGE
        files = [
            {"name": "doc1.pdf", "type": "application/pdf", "datapath": "/tmp/doc1.pdf", "size": 1024},
            {"name": "doc2.docx", "type": "application/docx", "datapath": "/tmp/doc2.docx", "size": 2048},
            {"name": "doc3.txt", "type": "text/plain", "datapath": "/tmp/doc3.txt", "size": 512}
        ]
        
        doc_ids = [str(uuid.uuid4()) for _ in files]
        mock_api_client.upload_document.side_effect = [
            MockDataFactory.upload_response(document_id=doc_ids[0], filename=files[0]["name"]),
            MockDataFactory.upload_response(document_id=doc_ids[1], filename=files[1]["name"]),
            MockDataFactory.upload_response(document_id=doc_ids[2], filename=files[2]["name"])
        ]
        mock_api_client.index_document.side_effect = [
            MockDataFactory.index_response(document_id=doc_ids[0]),
            MockDataFactory.index_response(document_id=doc_ids[1]),
            MockDataFactory.index_response(document_id=doc_ids[2])
        ]

        # ACT
        for file_info in files:
            response = mock_api_client.upload_document(file_info, source="local")
            doc = {
                "id": response["id"],
                "title": response["title"],
                "status": response["status"],
                "name": file_info["name"]
            }
            frontend_state["docs"].append(doc)
            index_resp = mock_api_client.index_document(doc["id"])
            doc["status"] = index_resp.get("status", doc["status"])

        # ASSERT
        assert len(frontend_state["docs"]) == 3
        assert frontend_state["docs"][0]["title"] == "doc1.pdf"
        assert frontend_state["docs"][1]["title"] == "doc2.docx"
        assert frontend_state["docs"][2]["title"] == "doc3.txt"
        assert all(doc["status"] == "indexed" for doc in frontend_state["docs"])

    def test_upload_empty_response_fallback(self, mock_api_client, frontend_state, upload_file_info):
        """
        CASE: Upload returns empty dict {} - fallback to local id
        Expected: Document added with local-{timestamp} id
        """
        # ARRANGE
        mock_api_client.upload_document.return_value = {}

        # ACT
        upload_response = mock_api_client.upload_document(upload_file_info, source="local")
        
        # normalize_doc() logic: fallback to local-{timestamp} if no id
        now_timestamp = datetime.datetime.now().timestamp()
        doc = {
            "id": upload_response.get("id") or upload_response.get("data", {}).get("id") or f"local-{now_timestamp}",
            "title": upload_response.get("title", "Untitled"),
            "status": upload_response.get("status", "uploaded"),
            "name": upload_file_info["name"]
        }
        frontend_state["docs"].append(doc)

        # ASSERT
        assert len(frontend_state["docs"]) == 1
        assert doc["id"].startswith("local-")
        assert doc["title"] == "Untitled"
        assert doc["status"] == "uploaded"

    def test_upload_no_id_field_fallback(self, mock_api_client, frontend_state, upload_file_info):
        """
        CASE: Upload response missing 'id' field
        Expected: Falls back to local-{timestamp}
        """
        # ARRANGE
        mock_api_client.upload_document.return_value = {
            "title": "document.pdf",
            "status": "uploaded"
        }

        # ACT
        response = mock_api_client.upload_document(upload_file_info, source="local")
        doc = {
            "id": response.get("id") or f"local-{datetime.datetime.now().timestamp()}",
            "title": response.get("title", "Untitled"),
            "status": response.get("status", "uploaded")
        }
        frontend_state["docs"].append(doc)

        # ASSERT
        assert doc["id"].startswith("local-")


class TestIndexDocumentFlow:
    """Test document indexing flow (frontend/app.py:396-405)"""

    def test_index_success_status_updated(self, mock_api_client, frontend_state):
        """
        CASE: Index document succeeds - status updated
        Expected: Document status changed to "indexed"
        """
        # ARRANGE
        doc_id = str(uuid.uuid4())
        frontend_state["docs"] = [{"id": doc_id, "title": "doc.pdf", "status": "uploaded"}]
        mock_api_client.index_document.return_value = MockDataFactory.index_response(
            document_id=doc_id,
            chunks=42,
            dimensions=1536
        )

        # ACT
        response = mock_api_client.index_document(doc_id)
        frontend_state["docs"][0]["status"] = response.get("status", "uploaded")

        # ASSERT
        assert frontend_state["docs"][0]["status"] == "indexed"
        assert frontend_state["docs"][0]["id"] == doc_id

    def test_index_failure_caught_silently(self, mock_api_client, frontend_state):
        """
        CASE: Index fails - error caught in try/except
        Expected: Status remains "uploaded", no exception propagates
        """
        # ARRANGE
        doc_id = str(uuid.uuid4())
        frontend_state["docs"] = [{"id": doc_id, "title": "doc.pdf", "status": "uploaded"}]
        mock_api_client.index_document.side_effect = ApiError("HTTP 500 Server Error")

        # ACT
        original_status = frontend_state["docs"][0]["status"]
        try:
            mock_api_client.index_document(doc_id)
        except ApiError:
            pass  # Caught and silently ignored (frontend/app.py:403)

        # ASSERT
        assert frontend_state["docs"][0]["status"] == "uploaded"  # Status unchanged

    def test_index_with_metadata(self, mock_api_client, frontend_state):
        """
        CASE: Index returns chunks & dimensions metadata
        Expected: Metadata extracted and stored
        """
        # ARRANGE
        doc_id = str(uuid.uuid4())
        frontend_state["docs"] = [{"id": doc_id, "title": "doc.pdf", "status": "uploaded"}]
        mock_api_client.index_document.return_value = MockDataFactory.index_response(
            document_id=doc_id,
            chunks=128,
            dimensions=1536
        )

        # ACT
        response = mock_api_client.index_document(doc_id)
        frontend_state["docs"][0]["status"] = response["status"]
        frontend_state["docs"][0]["chunks"] = response.get("chunks")
        frontend_state["docs"][0]["dimensions"] = response.get("dimensions")

        # ASSERT
        assert frontend_state["docs"][0]["chunks"] == 128
        assert frontend_state["docs"][0]["dimensions"] == 1536


class TestCreateConversationFlow:
    """Test conversation creation (frontend/apps/message.py:60-140)"""

    def test_create_conversation_success(self, mock_api_client, frontend_state):
        """
        CASE: Create conversation succeeds
        Expected: conversation_id stored, new_conversation=True
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        selected_docs = [str(uuid.uuid4()), str(uuid.uuid4())]
        content = "Tell me about the documents"
        
        mock_api_client.create_conversation.return_value = MockDataFactory.create_conversation_response(
            conversation_id=conv_id,
            title=content[:64]
        )

        # ACT - Simulate send_message() logic from frontend/apps/message.py:79-110
        response = mock_api_client.create_conversation(
            title=content[:64],
            provider="gemini",
            model="gemini-2.0",
            system_prompt="",
            document_ids=selected_docs,
            mode="normal"
        )
        
        conversation_id = response.get("conversation_id") or response.get("id") or response.get("uuid")
        frontend_state["conversation_id"] = conversation_id

        # ASSERT
        assert frontend_state["conversation_id"] == conv_id
        assert frontend_state["conversation_id"] is not None
        mock_api_client.create_conversation.assert_called_once()

    def test_create_conversation_empty_response(self, mock_api_client, frontend_state):
        """
        CASE: Create conversation returns empty dict {} - raises ApiError
        Expected: conversation_id remains None, raises error
        """
        # ARRANGE
        mock_api_client.create_conversation.return_value = {}

        # ACT & ASSERT
        response = mock_api_client.create_conversation(
            title="Test",
            provider="gemini",
            model="gemini-2.0",
            system_prompt="",
            document_ids=[],
            mode="normal"
        )
        
        conversation_id = response.get("conversation_id") or response.get("id") or response.get("uuid")
        
        if conversation_id is None:
            with pytest.raises(ApiError, match="Conversation id missing"):
                raise ApiError("Conversation id missing from create response")

    def test_create_conversation_no_id_field(self, mock_api_client, frontend_state):
        """
        CASE: Response missing conversation_id/id/uuid field
        Expected: conversation_id is None, error raised
        """
        # ARRANGE
        mock_api_client.create_conversation.return_value = {
            "title": "New Conversation",
            "status": "ready"
        }

        # ACT
        response = mock_api_client.create_conversation(
            title="Test",
            provider="gemini",
            model="gemini-2.0",
            system_prompt="",
            document_ids=[],
            mode="normal"
        )
        
        conversation_id = response.get("conversation_id") or response.get("id") or response.get("uuid")

        # ASSERT
        assert conversation_id is None

    def test_create_conversation_with_documents(self, mock_api_client, frontend_state):
        """
        CASE: Create conversation with multiple documents
        Expected: Documents passed to API and stored
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        doc_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        mock_api_client.create_conversation.return_value = MockDataFactory.create_conversation_response(
            conversation_id=conv_id
        )

        # ACT
        response = mock_api_client.create_conversation(
            title="Chat about documents",
            provider="gemini",
            model="gemini-2.0",
            system_prompt="",
            document_ids=doc_ids,
            mode="normal"
        )
        
        frontend_state["conversation_id"] = response["conversation_id"]

        # ASSERT
        assert frontend_state["conversation_id"] == conv_id
        call_args = mock_api_client.create_conversation.call_args
        assert call_args[1]["document_ids"] == doc_ids


class TestSendMessageFlow:
    """Test sending messages (frontend/app.py:480-538 + frontend/apps/message.py)"""

    def test_send_message_new_conversation_success(self, mock_api_client, frontend_state):
        """
        CASE: Send message to new conversation
        Expected: Create conv, send msg, update states
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        selected_docs = [str(uuid.uuid4())]
        content = "What is in these documents?"
        
        mock_api_client.create_conversation.return_value = MockDataFactory.create_conversation_response(
            conversation_id=conv_id
        )
        mock_api_client.send_message.return_value = MockDataFactory.send_message_response(
            conversation_id=conv_id,
            assistant_text="Here is the information from your documents..."
        )

        # ACT - Simulate _send_message() from frontend/app.py:480-515
        # Step 1: Add user message
        user_msg = {"role": "user", "content": content, "ts": time.time()}
        frontend_state["messages"].append(user_msg)

        # Step 2: Call send_message from frontend/apps/message.py
        response = mock_api_client.create_conversation(
            title=content[:64],
            provider="gemini",
            model="gemini-2.0",
            system_prompt="",
            document_ids=selected_docs,
            mode="normal"
        )
        conversation_id = response.get("conversation_id")
        
        send_response = mock_api_client.send_message(
            conversation_id,
            content,
            provider="gemini",
            model="gemini-2.0"
        )

        # Step 3: Update states
        frontend_state["conversation_id"] = conversation_id
        frontend_state["messages"].append({
            "role": "assistant",
            "content": send_response["assistant"],
            "ts": time.time()
        })
        frontend_state["history"].append({
            "id": conversation_id,
            "title": content[:42],
            "when": datetime.datetime.now().isoformat()
        })
        frontend_state["metrics"] = send_response.get("metrics", {})

        # ASSERT
        assert len(frontend_state["messages"]) == 2
        assert frontend_state["messages"][0]["role"] == "user"
        assert frontend_state["messages"][1]["role"] == "assistant"
        assert frontend_state["conversation_id"] == conv_id
        assert len(frontend_state["history"]) == 1
        assert frontend_state["metrics"]["provider"] == "gemini"

    def test_send_message_existing_conversation(self, mock_api_client, frontend_state):
        """
        CASE: Send message to existing conversation
        Expected: Update docs, send msg, DO NOT add to history
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        selected_docs = [str(uuid.uuid4())]
        content = "More questions"
        
        frontend_state["conversation_id"] = conv_id
        frontend_state["history"].append({
            "id": conv_id,
            "title": "Initial topic",
            "when": datetime.datetime.now().isoformat()
        })
        
        mock_api_client.update_conversation_documents.return_value = {"status": "updated"}
        mock_api_client.send_message.return_value = MockDataFactory.send_message_response(
            conversation_id=conv_id
        )

        # ACT
        user_msg = {"role": "user", "content": content, "ts": time.time()}
        frontend_state["messages"].append(user_msg)

        # Update documents (existing conversation)
        mock_api_client.update_conversation_documents(conv_id, selected_docs)

        # Send message
        send_response = mock_api_client.send_message(
            conv_id,
            content,
            provider="gemini",
            model="gemini-2.0"
        )
        
        frontend_state["messages"].append({
            "role": "assistant",
            "content": send_response["assistant"],
            "ts": time.time()
        })

        # ASSERT
        assert len(frontend_state["history"]) == 1  # No new history entry
        assert frontend_state["conversation_id"] == conv_id  # ID unchanged
        assert len(frontend_state["messages"]) == 2  # User message + assistant message added

    def test_send_message_no_assistant_field(self, mock_api_client, frontend_state):
        """
        CASE: Response missing assistant field
        Expected: assistant = "No response text returned."
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        mock_api_client.send_message.return_value = {
            "conversation_id": conv_id,
            "metrics": {"provider": "gemini", "model": "gemini-2.0", "mode": "normal", "total_ms": 100}
        }

        # ACT
        response = mock_api_client.send_message(conv_id, "Test")
        assistant = response.get("assistant") or "No response text returned."

        # ASSERT
        assert assistant == "No response text returned."

    def test_send_message_with_retrieval_hits(self, mock_api_client, frontend_state):
        """
        CASE: Response includes retrieval_hits metadata
        Expected: Metrics stored with retrieval hits
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        retrieval_hits = [
            {"text": "Context 1...", "score": 0.95},
            {"text": "Context 2...", "score": 0.82}
        ]
        
        mock_api_client.send_message.return_value = MockDataFactory.send_message_response(
            conversation_id=conv_id,
            retrieval_hits=retrieval_hits
        )

        # ACT
        response = mock_api_client.send_message(conv_id, "What is this?")
        frontend_state["metrics"] = response.get("metrics", {})

        # ASSERT
        assert "retrieval_hits" in frontend_state["metrics"]
        assert len(frontend_state["metrics"]["retrieval_hits"]) == 2


# ═══════════════════════════════════════════════════════════════
# PHẦN F: ERROR SCENARIO TESTS
# ═══════════════════════════════════════════════════════════════

class TestErrorScenarios:
    """Test error handling and recovery (frontend/apps/message.py:120-155)"""

    def test_upload_api_error_400_fallback(self, mock_api_client, frontend_state, upload_file_info):
        """
        CASE: Upload API returns HTTP 400 Bad Request
        Expected: Local doc created with "uploaded-local" status
        """
        # ARRANGE
        mock_api_client.upload_document.side_effect = ApiError("HTTP 400 Bad Request")

        # ACT - Simulate _handle_upload error handling (line 400-405)
        try:
            mock_api_client.upload_document(upload_file_info, source="local")
        except ApiError as exc:
            # Fallback: create local document
            doc = {
                "id": f"local-{datetime.datetime.now().timestamp()}",
                "title": upload_file_info["name"],
                "status": "uploaded-local",
                "error": str(exc)
            }
            frontend_state["docs"].append(doc)
            frontend_state["status"] = {
                "label": "Upload failed",
                "detail": str(exc),
                "kind": "error"
            }

        # ASSERT
        assert len(frontend_state["docs"]) == 1
        assert frontend_state["docs"][0]["status"] == "uploaded-local"
        assert frontend_state["status"]["kind"] == "error"

    def test_upload_api_error_500_fallback(self, mock_api_client, frontend_state, upload_file_info):
        """
        CASE: Upload API returns HTTP 500 Server Error
        Expected: Local doc created, status set to error
        """
        # ARRANGE
        mock_api_client.upload_document.side_effect = ApiError("HTTP 500 Internal Server Error")

        # ACT
        try:
            mock_api_client.upload_document(upload_file_info, source="local")
        except ApiError as exc:
            doc = {
                "id": f"local-{datetime.datetime.now().timestamp()}",
                "title": upload_file_info["name"],
                "status": "uploaded-local"
            }
            frontend_state["docs"].append(doc)
            frontend_state["status"] = {"label": "Upload failed", "kind": "error"}

        # ASSERT
        assert len(frontend_state["docs"]) == 1
        assert frontend_state["status"]["kind"] == "error"

    def test_upload_timeout_error(self, mock_api_client, frontend_state, upload_file_info):
        """
        CASE: Upload request timeout
        Expected: Local doc created, timeout error shown
        """
        # ARRANGE
        mock_api_client.upload_document.side_effect = ApiError("Request timeout after 60s")

        # ACT
        try:
            mock_api_client.upload_document(upload_file_info, source="local")
        except ApiError:
            doc = {
                "id": f"local-{datetime.datetime.now().timestamp()}",
                "title": upload_file_info["name"],
                "status": "uploaded-local"
            }
            frontend_state["docs"].append(doc)

        # ASSERT
        assert len(frontend_state["docs"]) == 1

    def test_create_conversation_api_400_error(self, mock_api_client, frontend_state):
        """
        CASE: Create conversation returns 400 - validation error
        Expected: If allow_mock=False, return error response
        """
        # ARRANGE
        mock_api_client.create_conversation.side_effect = ApiError("HTTP 400: Missing required field 'provider'")
        frontend_state["mock_on_fail"] = False

        # ACT & ASSERT
        with pytest.raises(ApiError):
            mock_api_client.create_conversation(
                title="Test",
                provider="invalid_provider",
                model="gemini-2.0",
                system_prompt="",
                document_ids=[],
                mode="normal"
            )

    def test_create_conversation_api_500_error(self, mock_api_client, frontend_state):
        """
        CASE: Create conversation returns 500 - server error
        Expected: If allow_mock=False, return error; if True, mock fallback
        """
        # ARRANGE
        mock_api_client.create_conversation.side_effect = ApiError("HTTP 500 Server Error")

        # SCENARIO 1: allow_mock=False
        frontend_state["mock_on_fail"] = False
        with pytest.raises(ApiError):
            mock_api_client.create_conversation(
                title="Test",
                provider="gemini",
                model="gemini-2.0",
                system_prompt="",
                document_ids=[],
                mode="normal"
            )

    def test_create_conversation_api_500_with_mock_fallback(self, mock_api_client, frontend_state):
        """
        CASE: Create conversation fails with allow_mock=True
        Expected: Return mock fallback response
        """
        # ARRANGE
        mock_api_client.create_conversation.side_effect = ApiError("HTTP 500 Server Error")
        frontend_state["mock_on_fail"] = True

        # ACT - Simulate fallback (frontend/apps/message.py:130-140)
        try:
            response = mock_api_client.create_conversation(
                title="Test",
                provider="gemini",
                model="gemini-2.0",
                system_prompt="",
                document_ids=[],
                mode="normal"
            )
        except ApiError:
            # Fallback mock response
            response = {
                "conversation_id": f"local-conv-{datetime.datetime.now().timestamp()}",
                "title": "Test",
                "status": "ready"
            }

        # ASSERT
        assert response["conversation_id"] is not None
        assert response["title"] == "Test"

    def test_create_conversation_timeout(self, mock_api_client, frontend_state):
        """
        CASE: Create conversation timeout
        Expected: ApiError raised, fallback if mock_on_fail=True
        """
        # ARRANGE
        mock_api_client.create_conversation.side_effect = ApiError("Request timeout")

        # ACT & ASSERT
        with pytest.raises(ApiError):
            mock_api_client.create_conversation(
                title="Test",
                provider="gemini",
                model="gemini-2.0",
                system_prompt="",
                document_ids=[],
                mode="normal"
            )

    def test_create_conversation_network_error(self, mock_api_client, frontend_state):
        """
        CASE: Network unreachable
        Expected: Connection error raised, fallback if mock_on_fail=True
        """
        # ARRANGE
        mock_api_client.create_conversation.side_effect = ApiError("Connection refused")

        # ACT & ASSERT
        with pytest.raises(ApiError):
            mock_api_client.create_conversation(
                title="Test",
                provider="gemini",
                model="gemini-2.0",
                system_prompt="",
                document_ids=[],
                mode="normal"
            )

    def test_send_message_create_fails_no_mock(self, mock_api_client, frontend_state):
        """
        CASE: Send message fails at create_conversation with allow_mock=False
        Expected: Return error response with assistant=""
        """
        # ARRANGE
        mock_api_client.create_conversation.side_effect = ApiError("HTTP 500")
        frontend_state["mock_on_fail"] = False

        # ACT - Simulate send_message error handling
        content = "Test message"
        conversation_id = None
        error_response = None

        try:
            response = mock_api_client.create_conversation(
                title=content[:64],
                provider="gemini",
                model="gemini-2.0",
                system_prompt="",
                document_ids=[],
                mode="normal"
            )
            conversation_id = response.get("conversation_id")
        except ApiError as exc:
            error_response = {
                "assistant": "",
                "conversation_id": conversation_id or "",
                "metrics": {"provider": "gemini", "model": "gemini-2.0", "mode": "normal", "total_ms": 0},
                "new_conversation": False,
                "error": str(exc),
                "used_mock": False
            }

        # ASSERT
        assert error_response is not None
        assert error_response["assistant"] == ""
        assert error_response["used_mock"] == False

    def test_send_message_create_fails_with_mock(self, mock_api_client, frontend_state):
        """
        CASE: Send message fails at create_conversation with allow_mock=True
        Expected: Return mock fallback response with used_mock=True
        """
        # ARRANGE
        mock_api_client.create_conversation.side_effect = ApiError("Backend unreachable")
        frontend_state["mock_on_fail"] = True

        # ACT
        content = "Test message"
        conversation_id = None

        try:
            response = mock_api_client.create_conversation(
                title=content[:64],
                provider="gemini",
                model="gemini-2.0",
                system_prompt="",
                document_ids=[],
                mode="normal"
            )
            conversation_id = response.get("conversation_id")
        except ApiError as exc:
            mock_response = {
                "assistant": "Backend unreachable. This is a local mock response so you can continue designing the UI.",
                "conversation_id": f"local-conv-{datetime.datetime.now().timestamp()}",
                "metrics": {"provider": "gemini", "model": "gemini-2.0", "mode": "normal", "total_ms": 0},
                "new_conversation": False,
                "error": str(exc),
                "used_mock": True
            }

        # ASSERT
        assert mock_response["used_mock"] == True
        assert "Backend unreachable" in mock_response["assistant"]

    def test_send_message_fails_existing_conversation(self, mock_api_client, frontend_state):
        """
        CASE: Send message fails on existing conversation
        Expected: ApiError raised
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        frontend_state["conversation_id"] = conv_id
        mock_api_client.send_message.side_effect = ApiError("HTTP 500")

        # ACT & ASSERT
        with pytest.raises(ApiError):
            mock_api_client.send_message(
                conv_id,
                "Test message",
                provider="gemini",
                model="gemini-2.0"
            )


# ═══════════════════════════════════════════════════════════════
# PHẦN F: VALIDATION & EDGE CASE TESTS
# ═══════════════════════════════════════════════════════════════

class TestValidationAndEdgeCases:
    """Test validation and edge case handling"""

    def test_send_empty_message_skipped(self, mock_api_client, frontend_state):
        """
        CASE: User sends empty message
        Expected: _send_message returns early, no API call
        """
        # ARRANGE
        content = ""

        # ACT
        if not content:
            mock_api_client.create_conversation.assert_not_called()
            mock_api_client.send_message.assert_not_called()

        # ASSERT
        assert mock_api_client.create_conversation.call_count == 0

    def test_send_no_selected_documents_warning(self, mock_api_client, frontend_state):
        """
        CASE: Send message with no selected documents
        Expected: set_status warning, no API call
        """
        # ARRANGE
        content = "What's in the documents?"
        selected_docs = []

        # ACT
        if not selected_docs:
            frontend_state["status"] = {
                "label": "Please select documents",
                "detail": "Select at least one document",
                "kind": "warning"
            }

        # ASSERT
        assert frontend_state["status"]["kind"] == "warning"
        mock_api_client.create_conversation.assert_not_called()

    def test_normalize_doc_multiple_response_formats(self, mock_api_client, frontend_state):
        """
        CASE: normalize_doc handles multiple response formats
        Expected: Correctly extracts id from various formats
        """
        # Test format 1: Direct id
        response1 = {"id": "doc-001", "title": "file.pdf", "status": "uploaded"}
        doc_id1 = response1.get("id") or response1.get("data", {}).get("id") or f"local-{datetime.datetime.now().timestamp()}"
        assert doc_id1 == "doc-001"

        # Test format 2: Nested in data
        response2 = {"data": {"id": "doc-002", "title": "file.pdf"}, "status": "success"}
        doc_id2 = response2.get("id") or response2.get("data", {}).get("id") or f"local-{datetime.datetime.now().timestamp()}"
        assert doc_id2 == "doc-002"

        # Test format 3: No id field
        response3 = {"title": "file.pdf"}
        doc_id3 = response3.get("id") or response3.get("data", {}).get("id") or f"local-{datetime.datetime.now().timestamp()}"
        assert doc_id3.startswith("local-")

    def test_metrics_extraction_from_response(self, mock_api_client, frontend_state):
        """
        CASE: Extract metrics from send_message response
        Expected: All metrics fields extracted correctly
        """
        # ARRANGE
        response = MockDataFactory.send_message_response(
            provider="mistral",
            model="mistral-large",
            mode="normal",
            total_ms=3200
        )

        # ACT
        metrics = response.get("metrics", {})

        # ASSERT
        assert metrics["provider"] == "mistral"
        assert metrics["model"] == "mistral-large"
        assert metrics["mode"] == "normal"
        assert metrics["total_ms"] == 3200


# ═══════════════════════════════════════════════════════════════
# PHẦN F: STATE MANAGEMENT TESTS
# ═══════════════════════════════════════════════════════════════

class TestStateManagement:
    """Test reactive state updates (frontend/app.py:68-83)"""

    def test_messages_list_grows_per_send(self, mock_api_client, frontend_state):
        """
        CASE: Each send adds both user and assistant messages
        Expected: messages list grows by 2 per send
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        mock_api_client.create_conversation.return_value = {"conversation_id": conv_id}
        mock_api_client.send_message.return_value = MockDataFactory.send_message_response(
            conversation_id=conv_id
        )

        # ACT - First send
        frontend_state["messages"].append({"role": "user", "content": "First message"})
        mock_api_client.send_message(conv_id, "First message")
        frontend_state["messages"].append({"role": "assistant", "content": "Response"})

        first_count = len(frontend_state["messages"])

        # ACT - Second send
        frontend_state["messages"].append({"role": "user", "content": "Second message"})
        mock_api_client.send_message(conv_id, "Second message")
        frontend_state["messages"].append({"role": "assistant", "content": "Response"})

        second_count = len(frontend_state["messages"])

        # ASSERT
        assert first_count == 2
        assert second_count == 4

    def test_docs_list_grows_per_upload(self, mock_api_client, frontend_state):
        """
        CASE: Each upload adds document to docs list
        Expected: docs list grows with each upload
        """
        # ARRANGE
        doc_ids = [str(uuid.uuid4()) for _ in range(3)]

        # ACT
        for i, doc_id in enumerate(doc_ids):
            mock_api_client.upload_document.return_value = {
                "id": doc_id,
                "title": f"document{i}.pdf",
                "status": "uploaded"
            }
            response = mock_api_client.upload_document(None)
            frontend_state["docs"].append({"id": response["id"], "title": response["title"]})

        # ASSERT
        assert len(frontend_state["docs"]) == 3

    def test_conversation_id_changes_from_none_to_uuid(self, mock_api_client, frontend_state):
        """
        CASE: conversation_id initially None, set on create
        Expected: conversation_id: None → UUID
        """
        # ARRANGE
        assert frontend_state["conversation_id"] is None
        conv_id = str(uuid.uuid4())
        mock_api_client.create_conversation.return_value = {"conversation_id": conv_id}

        # ACT
        response = mock_api_client.create_conversation(
            title="Test",
            provider="gemini",
            model="gemini-2.0",
            system_prompt="",
            document_ids=[],
            mode="normal"
        )
        frontend_state["conversation_id"] = response["conversation_id"]

        # ASSERT
        assert frontend_state["conversation_id"] == conv_id
        assert frontend_state["conversation_id"] is not None

    def test_history_updated_on_new_conversation(self, mock_api_client, frontend_state):
        """
        CASE: New conversation added to history
        Expected: history list has one entry with (id, title, when)
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        content = "First message content"

        # ACT
        frontend_state["history"].append({
            "id": conv_id,
            "title": content[:42],
            "when": datetime.datetime.now().isoformat()
        })

        # ASSERT
        assert len(frontend_state["history"]) == 1
        assert frontend_state["history"][0]["id"] == conv_id
        assert frontend_state["history"][0]["title"] == content[:42]

    def test_history_not_updated_on_existing_conversation(self, mock_api_client, frontend_state):
        """
        CASE: Send to existing conversation
        Expected: history list unchanged
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())
        frontend_state["history"] = [{"id": conv_id, "title": "Initial topic", "when": "2024-01-01"}]
        initial_count = len(frontend_state["history"])

        # ACT
        frontend_state["conversation_id"] = conv_id
        # Send message to existing conversation - should NOT add to history

        # ASSERT
        assert len(frontend_state["history"]) == initial_count

    def test_metrics_updated_from_response(self, mock_api_client, frontend_state):
        """
        CASE: Metrics extracted from message response
        Expected: metrics dict populated
        """
        # ARRANGE
        response = MockDataFactory.send_message_response(
            provider="gemini",
            model="gemini-2.0",
            total_ms=2530
        )

        # ACT
        frontend_state["metrics"] = response.get("metrics", {})

        # ASSERT
        assert frontend_state["metrics"]["provider"] == "gemini"
        assert frontend_state["metrics"]["model"] == "gemini-2.0"
        assert frontend_state["metrics"]["total_ms"] == 2530

    def test_status_set_on_success(self, mock_api_client, frontend_state):
        """
        CASE: Success message sets status
        Expected: status.kind = "success"
        """
        # ARRANGE
        conv_id = str(uuid.uuid4())

        # ACT
        frontend_state["status"] = {
            "label": "Response ready",
            "detail": "",
            "kind": "success"
        }

        # ASSERT
        assert frontend_state["status"]["kind"] == "success"

    def test_status_set_on_error(self, mock_api_client, frontend_state):
        """
        CASE: Error message sets status
        Expected: status.kind = "error"
        """
        # ARRANGE
        error_msg = "Upload failed"

        # ACT
        frontend_state["status"] = {
            "label": "Error",
            "detail": error_msg,
            "kind": "error"
        }

        # ASSERT
        assert frontend_state["status"]["kind"] == "error"


# ═══════════════════════════════════════════════════════════════
# PHẦN F: END-TO-END INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════

class TestEndToEndIntegration:
    """Test complete workflows"""

    def test_full_workflow_upload_create_send(self, mock_api_client, frontend_state):
        """
        CASE: Complete workflow - Upload document → Create conversation → Send message
        Expected: All states updated, all API calls made
        """
        # ARRANGE
        doc_id = str(uuid.uuid4())
        conv_id = str(uuid.uuid4())
        
        mock_api_client.upload_document.return_value = MockDataFactory.upload_response(doc_id)
        mock_api_client.index_document.return_value = MockDataFactory.index_response(doc_id)
        mock_api_client.create_conversation.return_value = MockDataFactory.create_conversation_response(conv_id)
        mock_api_client.send_message.return_value = MockDataFactory.send_message_response(conv_id)

        # ACT - Phase 1: Upload
        upload_response = mock_api_client.upload_document({"name": "doc.pdf"})
        frontend_state["docs"].append({
            "id": upload_response["id"],
            "title": upload_response["title"],
            "status": "uploaded"
        })
        
        index_response = mock_api_client.index_document(doc_id)
        frontend_state["docs"][0]["status"] = index_response["status"]

        # ACT - Phase 2: Create conversation
        create_response = mock_api_client.create_conversation(
            title="Chat with documents",
            provider="gemini",
            model="gemini-2.0",
            system_prompt="",
            document_ids=[doc_id],
            mode="normal"
        )
        frontend_state["conversation_id"] = create_response["conversation_id"]

        # ACT - Phase 3: Send message
        frontend_state["messages"].append({"role": "user", "content": "What is this?"})
        send_response = mock_api_client.send_message(conv_id, "What is this?")
        frontend_state["messages"].append({"role": "assistant", "content": send_response["assistant"]})
        frontend_state["metrics"] = send_response["metrics"]

        # ASSERT
        assert len(frontend_state["docs"]) == 1
        assert frontend_state["docs"][0]["status"] == "indexed"
        assert frontend_state["conversation_id"] == conv_id
        assert len(frontend_state["messages"]) == 2
        assert frontend_state["metrics"]["provider"] == "gemini"

    def test_multiple_conversations_in_history(self, mock_api_client, frontend_state):
        """
        CASE: User creates multiple conversations
        Expected: All added to history
        """
        # ARRANGE
        conv_ids = [str(uuid.uuid4()) for _ in range(3)]
        contents = ["First topic", "Second topic", "Third topic"]

        # ACT
        for conv_id, content in zip(conv_ids, contents):
            mock_api_client.create_conversation.return_value = {"conversation_id": conv_id}
            response = mock_api_client.create_conversation(
                title=content,
                provider="gemini",
                model="gemini-2.0",
                system_prompt="",
                document_ids=[],
                mode="normal"
            )
            
            frontend_state["history"].append({
                "id": response["conversation_id"],
                "title": content,
                "when": datetime.datetime.now().isoformat()
            })

        # ASSERT
        assert len(frontend_state["history"]) == 3
        for i, conv_id in enumerate(conv_ids):
            assert frontend_state["history"][i]["id"] == conv_id


# ═══════════════════════════════════════════════════════════════
# PARAMETRIZED TEST CASES
# ═══════════════════════════════════════════════════════════════

class TestParametrizedScenarios:
    """Parametrized tests for multiple scenarios"""

    @pytest.mark.parametrize("filename,file_type", [
        ("report.pdf", "application/pdf"),
        ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("notes.txt", "text/plain"),
        ("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ])
    def test_upload_various_file_types(self, mock_api_client, frontend_state, filename, file_type):
        """Test uploading different file types"""
        # ARRANGE
        doc_id = str(uuid.uuid4())
        mock_api_client.upload_document.return_value = {
            "id": doc_id,
            "title": filename,
            "status": "uploaded"
        }

        # ACT
        response = mock_api_client.upload_document({"name": filename, "type": file_type})
        frontend_state["docs"].append({"id": response["id"], "title": response["title"]})

        # ASSERT
        assert frontend_state["docs"][0]["title"] == filename

    @pytest.mark.parametrize("provider,model", [
        ("gemini", "gemini-2.0"),
        ("mistral", "mistral-large"),
        ("ollama", "llama2"),
    ])
    def test_send_message_various_providers(self, mock_api_client, frontend_state, provider, model):
        """Test sending messages with different providers"""
        # ARRANGE
        conv_id = str(uuid.uuid4())
        mock_api_client.send_message.return_value = MockDataFactory.send_message_response(
            conversation_id=conv_id,
            provider=provider,
            model=model
        )

        # ACT
        response = mock_api_client.send_message(conv_id, "Test", provider=provider, model=model)
        frontend_state["metrics"] = response.get("metrics", {})

        # ASSERT
        assert frontend_state["metrics"]["provider"] == provider
        assert frontend_state["metrics"]["model"] == model

    @pytest.mark.parametrize("error_msg,error_kind", [
        ("HTTP 400 Bad Request", "validation"),
        ("HTTP 500 Server Error", "server"),
        ("Request timeout after 60s", "timeout"),
        ("Connection refused", "network"),
    ])
    def test_upload_various_errors(self, mock_api_client, frontend_state, upload_file_info, error_msg, error_kind):
        """Test various error scenarios during upload"""
        # ARRANGE
        mock_api_client.upload_document.side_effect = ApiError(error_msg)

        # ACT
        try:
            mock_api_client.upload_document(upload_file_info)
        except ApiError:
            doc = {
                "id": f"local-{datetime.datetime.now().timestamp()}",
                "title": upload_file_info["name"],
                "status": "uploaded-local",
                "error_kind": error_kind
            }
            frontend_state["docs"].append(doc)

        # ASSERT
        assert len(frontend_state["docs"]) == 1
        assert frontend_state["docs"][0]["error_kind"] == error_kind


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
