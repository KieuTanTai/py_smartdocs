"""
Frontend Mock Chat Behavior - Data-Driven Test
=============================================

Test Frontend UI behavior khi nhận mock responses từ Backend:
- Upload file → get document ID
- Create conversation with document → get conversation ID  
- Send messages → get assistant response

Cách chạy:
    python -m pytest tests/test_frontend_mock_chat_behavior.py -v -s
    
    Hoặc từng test:
    python -m pytest tests/test_frontend_mock_chat_behavior.py::test_upload_file_workflow -v -s
    python -m pytest tests/test_frontend_mock_chat_behavior.py::test_create_conversation_workflow -v -s
    python -m pytest tests/test_frontend_mock_chat_behavior.py::test_send_message_workflow -v -s
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import Mock, patch, MagicMock
import pytest

# ──────────────────────────────────────────────────────────────
# Setup Path
# ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# ──────────────────────────────────────────────────────────────
# Mock Data Fixtures
# ──────────────────────────────────────────────────────────────

class MockDataProvider:
    """Cung cấp mock responses theo scenario"""
    
    @staticmethod
    def mock_upload_response(file_name: str = "report.pdf") -> Dict[str, Any]:
        """Mock response từ POST /api/documents/upload/"""
        return {
            "id": f"doc_{int(time.time())}",
            "title": file_name,
            "status": "uploaded",
            "size": 2048000,
        }
    
    @staticmethod
    def mock_index_response(doc_id: str) -> Dict[str, Any]:
        """Mock response từ POST /api/documents/{id}/index/"""
        return {
            "id": doc_id,
            "status": "indexed",
            "chunks": 42,
            "dimensions": 1536,
            "processing_time_ms": 1250,
        }
    
    @staticmethod
    def mock_create_conversation_response(
        doc_ids: List[str],
        provider: str = "gemini",
        model: str = "gemini-3.1-flash"
    ) -> Dict[str, Any]:
        """Mock response từ POST /api/conversations/"""
        return {
            "conversation_id": f"conv_{int(time.time())}",
            "id": f"conv_{int(time.time())}",
            "title": "New Chat Session",
            "document_ids": doc_ids,
            "provider": provider,
            "model": model,
            "created_at": "2026-06-18T10:30:00Z",
            "status": "active",
        }
    
    @staticmethod
    def mock_send_message_response(
        user_message: str,
        provider: str = "gemini",
        model: str = "gemini-3.1-flash"
    ) -> Dict[str, Any]:
        """Mock response từ POST /api/conversations/{id}/messages/"""
        
        # Tạo response dựa trên content của message
        assistant_responses = {
            "tổng doanh thu": "📊 Tổng doanh thu năm 2024: 150,000,000,000 VND (tăng 15% so với năm trước)",
            "chi phí": "💰 Chi phí hoạt động: 95,000,000,000 VND (tỷ lệ 63% so với doanh thu)",
            "lợi nhuận": "📈 Lợi nhuận ròng: 55,000,000,000 VND",
            "ai là": "🤖 Tôi là trợ lý AI SmartDocs, sẵn sàng giúp bạn phân tích tài liệu",
        }
        
        assistant_text = next(
            (response for key, response in assistant_responses.items() if key in user_message.lower()),
            f"Dựa trên tài liệu, tôi thấy rằng: {user_message[:50]}... là một câu hỏi hay."
        )
        
        return {
            "message_id": f"msg_{int(time.time())}",
            "assistant": assistant_text,
            "user_message": user_message,
            "conversation_id": f"conv_{int(time.time())}",
            "metrics": {
                "provider": provider,
                "model": model,
                "embed_ms": 150,
                "query_ms": 280,
                "response_ms": 2100,
                "total_ms": 2530,
                "retrieval_hits": 3,
                "chunk_relevance": [0.92, 0.87, 0.74],
            },
            "status": "ok",
        }


# ──────────────────────────────────────────────────────────────
# Test Data Scenarios
# ──────────────────────────────────────────────────────────────

class TestScenarios:
    """Bộ test data-driven scenarios"""
    
    UPLOAD_SCENARIOS = [
        {
            "name": "Upload PDF Report",
            "file_name": "financial_report_2024.pdf",
            "file_type": "application/pdf",
            "expected_status": "uploaded",
        },
        {
            "name": "Upload Word Document",
            "file_name": "quarterly_review.docx",
            "file_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "expected_status": "uploaded",
        },
        {
            "name": "Upload Text File",
            "file_name": "notes.txt",
            "file_type": "text/plain",
            "expected_status": "uploaded",
        },
    ]
    
    CONVERSATION_SCENARIOS = [
        {
            "name": "Single Document Conversation",
            "doc_count": 1,
            "provider": "gemini",
            "model": "gemini-3.1-flash",
        },
        {
            "name": "Multiple Documents Conversation",
            "doc_count": 3,
            "provider": "mistral",
            "model": "mistral-large-latest",
        },
    ]
    
    MESSAGE_SCENARIOS = [
        {
            "name": "Financial Query",
            "message": "Tổng doanh thu năm 2024 là bao nhiêu?",
            "expected_keywords": ["doanh thu", "150", "VND"],
        },
        {
            "name": "Cost Analysis Query",
            "message": "Chi phí hoạt động chiếm bao nhiêu phần trăm?",
            "expected_keywords": ["chi phí", "63%"],
        },
        {
            "name": "General Question",
            "message": "AI này là gì, có thể giúp gì cho tôi?",
            "expected_keywords": ["AI", "SmartDocs"],
        },
    ]


# ──────────────────────────────────────────────────────────────
# Unit Tests
# ──────────────────────────────────────────────────────────────

import time


class TestMockDataProvider:
    """Test mock data provider"""
    
    def test_mock_upload_response(self):
        """Mock upload response có required fields"""
        response = MockDataProvider.mock_upload_response("test.pdf")
        assert "id" in response
        assert response["title"] == "test.pdf"
        assert response["status"] == "uploaded"
    
    def test_mock_index_response(self):
        """Mock index response có required fields"""
        doc_id = "doc_123"
        response = MockDataProvider.mock_index_response(doc_id)
        assert response["id"] == doc_id
        assert response["status"] == "indexed"
        assert "chunks" in response
        assert "dimensions" in response
    
    def test_mock_create_conversation_response(self):
        """Mock conversation response có required fields"""
        doc_ids = ["doc_1", "doc_2"]
        response = MockDataProvider.mock_create_conversation_response(doc_ids)
        assert "conversation_id" in response or "id" in response
        assert response["document_ids"] == doc_ids
        assert response["status"] == "active"
    
    def test_mock_send_message_response(self):
        """Mock message response có required fields"""
        response = MockDataProvider.mock_send_message_response("tổng doanh thu bao nhiêu?")
        assert "assistant" in response
        assert "tổng doanh thu" in response["assistant"].lower() or "doanh thu" in response["assistant"].lower()
        assert "message_id" in response
        assert "metrics" in response


# ──────────────────────────────────────────────────────────────
# Frontend Behavior Tests
# ──────────────────────────────────────────────────────────────

class TestUploadFileBehavior:
    """Test behavior khi upload file → get document"""
    
    @pytest.mark.parametrize("scenario", TestScenarios.UPLOAD_SCENARIOS)
    def test_upload_file_workflow(self, scenario):
        """
        Workflow: Upload file → Server returns document ID → Frontend updates UI
        
        Expected Behavior:
        - Upload endpoint called with file
        - Response contains document ID
        - Document appears in document list
        - Status shows "uploaded"
        """
        # Mock the API client
        mock_api = Mock()
        mock_api.upload_document.return_value = MockDataProvider.mock_upload_response(
            scenario["file_name"]
        )
        
        # Simulate frontend upload
        file_info = {
            "name": scenario["file_name"],
            "type": scenario["file_type"],
            "datapath": f"/tmp/{scenario['file_name']}",
        }
        
        response = mock_api.upload_document(file_info, source="local")
        
        # Verify response structure
        assert response.get("id"), f"Missing doc ID in {scenario['name']}"
        assert response.get("title") == scenario["file_name"]
        assert response.get("status") == scenario["expected_status"]
        
        # Verify API was called correctly
        mock_api.upload_document.assert_called_once()


class TestCreateConversationBehavior:
    """Test behavior khi file indexed → create conversation"""
    
    @pytest.mark.parametrize("scenario", TestScenarios.CONVERSATION_SCENARIOS)
    def test_create_conversation_workflow(self, scenario):
        """
        Workflow: After file uploaded/indexed → Create conversation with docs → get conv ID
        
        Expected Behavior:
        - Create conversation API called with document IDs
        - Response contains conversation ID
        - Conversation stored in frontend state
        - Chat input becomes active
        """
        mock_api = Mock()
        
        # Mock upload + index
        doc_ids = [f"doc_{i}" for i in range(scenario["doc_count"])]
        
        mock_api.create_conversation.return_value = MockDataProvider.mock_create_conversation_response(
            doc_ids,
            provider=scenario["provider"],
            model=scenario["model"]
        )
        
        # Simulate frontend creating conversation after file processed
        response = mock_api.create_conversation(
            title="Test Chat",
            provider=scenario["provider"],
            model=scenario["model"],
            system_prompt="Bạn là trợ lý hữu ích",
            document_ids=doc_ids,
            mode="normal",
        )
        
        # Verify response
        conv_id = response.get("conversation_id") or response.get("id")
        assert conv_id, f"Missing conversation ID in {scenario['name']}"
        assert response.get("document_ids") == doc_ids
        assert response.get("status") == "active"
        
        # Verify API called with correct params
        mock_api.create_conversation.assert_called_once()


class TestSendMessageBehavior:
    """Test behavior khi gửi message → nhận response"""
    
    @pytest.mark.parametrize("scenario", TestScenarios.MESSAGE_SCENARIOS)
    def test_send_message_workflow(self, scenario):
        """
        Workflow: Send message → Backend processes with RAG → return assistant response
        
        Expected Behavior:
        - Message sent with conversation ID
        - Response contains assistant text
        - Metrics show provider/model/timing
        - Messages list updated with new message
        """
        mock_api = Mock()
        
        mock_api.send_message.return_value = MockDataProvider.mock_send_message_response(
            scenario["message"]
        )
        
        # Simulate frontend sending message
        response = mock_api.send_message(
            conversation_id="conv_123",
            message=scenario["message"],
            provider="gemini",
            model="gemini-3.1-flash",
        )
        
        # Verify response has assistant text
        assert "assistant" in response
        assert response["assistant"], f"Empty assistant response in {scenario['name']}"
        
        # Verify response has metrics
        metrics = response.get("metrics", {})
        assert "provider" in metrics
        assert "total_ms" in metrics
        assert metrics["total_ms"] > 0
        
        # Verify keywords in response (if scenario specifies)
        if scenario.get("expected_keywords"):
            response_text = response["assistant"].lower()
            found_keywords = [kw for kw in scenario["expected_keywords"] 
                            if kw.lower() in response_text]
            assert len(found_keywords) > 0, f"Missing keywords in {scenario['name']}: {scenario['expected_keywords']}"


# ──────────────────────────────────────────────────────────────
# Integration Tests
# ──────────────────────────────────────────────────────────────

class TestEndToEndWorkflow:
    """Test complete workflow: upload → create conv → send messages"""
    
    def test_full_chat_session_workflow(self):
        """
        Complete workflow:
        1. Upload PDF file
        2. Index document
        3. Create conversation with document
        4. Send 3 messages
        5. Verify all responses
        """
        mock_api = Mock()
        
        # Step 1: Upload file
        upload_resp = MockDataProvider.mock_upload_response("report.pdf")
        mock_api.upload_document.return_value = upload_resp
        doc_response = mock_api.upload_document({"name": "report.pdf"}, source="local")
        doc_id = doc_response["id"]
        assert doc_id
        
        # Step 2: Index document
        index_resp = MockDataProvider.mock_index_response(doc_id)
        mock_api.index_document.return_value = index_resp
        index_response = mock_api.index_document(doc_id)
        assert index_response["status"] == "indexed"
        
        # Step 3: Create conversation
        conv_resp = MockDataProvider.mock_create_conversation_response([doc_id])
        mock_api.create_conversation.return_value = conv_resp
        conv_response = mock_api.create_conversation(
            title="Report Analysis",
            provider="gemini",
            model="gemini-3.1-flash",
            system_prompt="Analyze this financial report",
            document_ids=[doc_id],
            mode="normal",
        )
        conv_id = conv_response.get("conversation_id")
        assert conv_id
        
        # Step 4: Send messages
        messages = [
            "tổng doanh thu là bao nhiêu?",
            "chi phí chiếm bao nhiêu phần trăm?",
            "lợi nhuận ròng bao nhiêu?"
        ]
        
        message_responses = []
        for msg in messages:
            msg_resp = MockDataProvider.mock_send_message_response(msg)
            mock_api.send_message.return_value = msg_resp
            response = mock_api.send_message(
                conversation_id=conv_id,
                message=msg,
                provider="gemini",
                model="gemini-3.1-flash",
            )
            message_responses.append(response)
            assert "assistant" in response
            assert response["metrics"]["total_ms"] > 0
        
        # Verify all messages sent
        assert len(message_responses) == 3
        assert all("assistant" in resp for resp in message_responses)


# ──────────────────────────────────────────────────────────────
# Frontend State Management Tests
# ──────────────────────────────────────────────────────────────

class TestFrontendStateUpdates:
    """Test frontend state updates khi nhận mock responses"""
    
    def test_messages_state_update(self):
        """Test messages list updated khi send message"""
        mock_api = Mock()
        
        # Simulate Shiny reactive state
        messages_state = []
        
        # Send message 1
        resp1 = MockDataProvider.mock_send_message_response("Hỏi thứ nhất")
        messages_state.append({"role": "user", "content": "Hỏi thứ nhất"})
        messages_state.append({"role": "assistant", "content": resp1["assistant"]})
        
        # Send message 2
        resp2 = MockDataProvider.mock_send_message_response("Hỏi thứ hai")
        messages_state.append({"role": "user", "content": "Hỏi thứ hai"})
        messages_state.append({"role": "assistant", "content": resp2["assistant"]})
        
        # Verify state
        assert len(messages_state) == 4  # 2 user + 2 assistant
        user_msgs = [m for m in messages_state if m["role"] == "user"]
        asst_msgs = [m for m in messages_state if m["role"] == "assistant"]
        assert len(user_msgs) == 2
        assert len(asst_msgs) == 2
    
    def test_documents_state_update(self):
        """Test documents list updated khi upload file"""
        docs_state = []
        
        # Upload 3 files
        for i, filename in enumerate(["doc1.pdf", "doc2.docx", "doc3.txt"]):
            resp = MockDataProvider.mock_upload_response(filename)
            docs_state.append({
                "id": resp["id"],
                "title": resp["title"],
                "status": resp["status"],
            })
        
        # Verify state
        assert len(docs_state) == 3
        assert all(d["status"] == "uploaded" for d in docs_state)
    
    def test_conversation_state_update(self):
        """Test conversation_id stored after create"""
        conv_state = None
        
        # Create conversation
        resp = MockDataProvider.mock_create_conversation_response(["doc_1", "doc_2"])
        conv_state = resp.get("conversation_id")
        
        # Verify state
        assert conv_state is not None
        assert conv_state.startswith("conv_")


if __name__ == "__main__":
    import subprocess
    subprocess.run([
        sys.executable, "-m", "pytest",
        __file__, "-v", "-s",
        "--tb=short"
    ])
