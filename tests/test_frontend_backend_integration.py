"""
Frontend-Backend Integration Tests
Test frontend và backend có kết nối qua lại với nhau không
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings.local')

import django
django.setup()

from django.test import TestCase, Client
from django.conf import settings
from rest_framework.test import APIClient
from backend.apps.services.chat.models import ConversationModel, DocumentModel, MessageModel


class TestFrontendBackendAPI(TestCase):
    """Test các API endpoints hoạt động đúng"""
    
    def setUp(self):
        """Setup test client"""
        self.client = APIClient()
        self.api_base = "http://localhost:8000/api"
        
    def test_01_health_endpoint(self):
        """Test health check endpoint"""
        print("\n✓ Test 1: Health Endpoint")
        try:
            response = self.client.get('/api/health/')
            print(f"  Status: {response.status_code}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            print(f"  Response: {data}")
            assert data['status'] == 'healthy'
            print("  ✓ PASS: Health endpoint working")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            return False
    
    def test_02_providers_endpoint(self):
        """Test providers list endpoint"""
        print("\n✓ Test 2: Providers Endpoint")
        try:
            response = self.client.get('/api/providers/')
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  Providers count: {data.get('count', 0)}")
                print(f"  Response: {data}")
            else:
                print(f"  Error: {response.json()}")
            print("  ✓ PASS: Providers endpoint responding")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            return False
    
    def test_03_create_conversation(self):
        """Test create conversation endpoint"""
        print("\n✓ Test 3: Create Conversation")
        try:
            payload = {
                "title": "Test Conversation",
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "document_ids": []
            }
            response = self.client.post('/api/conversations/', payload, format='json')
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            assert response.status_code == 201, f"Expected 201, got {response.status_code}"
            assert 'conversation_id' in data
            self.conversation_id = data['conversation_id']
            print(f"  ✓ PASS: Created conversation {self.conversation_id}")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            return False
    
    def test_04_list_conversations(self):
        """Test list conversations endpoint"""
        print("\n✓ Test 4: List Conversations")
        try:
            response = self.client.get('/api/conversations/')
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Count: {len(data)}")
            print(f"  Conversations: {json.dumps(data[:2], indent=2) if data else '[]'}")
            assert response.status_code == 200
            print("  ✓ PASS: List conversations working")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            return False
    
    def test_05_send_message(self):
        """Test send message endpoint"""
        print("\n✓ Test 5: Send Message to Conversation")
        try:
            # Create conversation first
            conv_data = {
                "title": "Message Test",
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "document_ids": []
            }
            conv_response = self.client.post('/api/conversations/', conv_data, format='json')
            conv_id = conv_response.json()['conversation_id']
            
            # Send message
            msg_data = {
                "content": "Hello, what is this about?",
                "provider": "gemini",
                "model": "gemini-2.5-flash"
            }
            response = self.client.post(
                f'/api/conversations/{conv_id}/messages/',
                msg_data,
                format='json'
            )
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Response keys: {list(data.keys())}")
            if 'assistant' in data:
                print(f"  Assistant response: {data['assistant'][:100]}...")
            print(f"  Metrics: {data.get('metrics', {})}")
            assert response.status_code == 200
            print("  ✓ PASS: Message sent and response received")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_06_list_messages(self):
        """Test list messages endpoint"""
        print("\n✓ Test 6: List Messages")
        try:
            # Create conversation
            conv_data = {
                "title": "Messages List Test",
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "document_ids": []
            }
            conv_response = self.client.post('/api/conversations/', conv_data, format='json')
            conv_id = conv_response.json()['conversation_id']
            
            # Send message
            msg_data = {"content": "Test message", "provider": "gemini", "model": "gemini-2.5-flash"}
            self.client.post(f'/api/conversations/{conv_id}/messages/', msg_data, format='json')
            
            # List messages
            response = self.client.get(f'/api/conversations/{conv_id}/messages/')
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Message count: {len(data)}")
            for i, msg in enumerate(data[:2]):
                print(f"    [{i}] {msg.get('role')}: {msg.get('content', '')[:50]}...")
            assert response.status_code == 200
            print("  ✓ PASS: List messages working")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            return False
    
    def test_07_document_upload(self):
        """Test document upload endpoint"""
        print("\n✓ Test 7: Document Upload")
        try:
            # Create a test file
            test_file_path = Path(settings.MEDIA_ROOT) / "test_document.txt"
            test_file_path.parent.mkdir(parents=True, exist_ok=True)
            test_file_path.write_text("This is a test document for RAG system testing.")
            
            with open(test_file_path, 'rb') as f:
                response = self.client.post(
                    '/api/documents/upload/',
                    {'file': f},
                    format='multipart'
                )
            
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)}")
            assert response.status_code == 201
            assert 'id' in data
            self.document_id = data['id']
            print(f"  ✓ PASS: Document uploaded {self.document_id}")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            return False
    
    def test_08_list_documents(self):
        """Test list documents endpoint"""
        print("\n✓ Test 8: List Documents")
        try:
            response = self.client.get('/api/documents/')
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Documents count: {len(data)}")
            for i, doc in enumerate(data[:2]):
                print(f"    [{i}] {doc.get('title')} - Status: {doc.get('status')}")
            assert response.status_code == 200
            print("  ✓ PASS: List documents working")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            return False
    
    def test_09_get_document_status(self):
        """Test get document status endpoint"""
        print("\n✓ Test 9: Get Document Status")
        try:
            # Create document first
            test_file_path = Path(settings.MEDIA_ROOT) / "status_test.txt"
            test_file_path.parent.mkdir(parents=True, exist_ok=True)
            test_file_path.write_text("Status test document")
            
            with open(test_file_path, 'rb') as f:
                upload_response = self.client.post(
                    '/api/documents/upload/',
                    {'file': f},
                    format='multipart'
                )
            
            doc_id = upload_response.json()['id']
            
            # Get status
            response = self.client.get(f'/api/documents/{doc_id}/status/')
            print(f"  Status: {response.status_code}")
            data = response.json()
            print(f"  Document status: {data.get('status')}")
            assert response.status_code == 200
            print("  ✓ PASS: Get document status working")
            return True
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            return False


class TestDataFlow(TestCase):
    """Test end-to-end data flows"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_01_upload_to_conversation_flow(self):
        """Test complete flow: Upload → List → Add to Conversation"""
        print("\n=== Test: Upload to Conversation Flow ===")
        
        try:
            # Step 1: Upload document
            print("\n1. Uploading document...")
            test_file = Path(settings.MEDIA_ROOT) / "flow_test.txt"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("Document for flow testing")
            
            with open(test_file, 'rb') as f:
                doc_response = self.client.post(
                    '/api/documents/upload/',
                    {'file': f},
                    format='multipart'
                )
            
            assert doc_response.status_code == 201
            doc_id = doc_response.json()['id']
            print(f"   ✓ Document uploaded: {doc_id}")
            
            # Step 2: Create conversation
            print("\n2. Creating conversation...")
            conv_response = self.client.post(
                '/api/conversations/',
                {
                    "title": "Flow Test",
                    "provider": "gemini",
                    "model": "gemini-2.5-flash",
                    "document_ids": [doc_id]
                },
                format='json'
            )
            assert conv_response.status_code == 201
            conv_id = conv_response.json()['conversation_id']
            print(f"   ✓ Conversation created: {conv_id}")
            
            # Step 3: Send message
            print("\n3. Sending message...")
            msg_response = self.client.post(
                f'/api/conversations/{conv_id}/messages/',
                {
                    "content": "What is in this document?",
                    "provider": "gemini",
                    "model": "gemini-2.5-flash"
                },
                format='json'
            )
            assert msg_response.status_code == 200
            print(f"   ✓ Message sent, response received")
            print(f"   ✓ Total metrics: {msg_response.json().get('metrics', {})}")
            
            print("\n✓ PASS: Complete flow successful")
            return True
            
        except Exception as e:
            print(f"\n✗ FAIL: {e}")
            import traceback
            traceback.print_exc()
            return False


class TestFrontendAPICall(TestCase):
    """Test simulating frontend API calls"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_frontend_call_sequence(self):
        """Simulate typical frontend call sequence"""
        print("\n=== Test: Frontend Call Sequence ===")
        
        # 1. Check health
        print("\n1. Health check...")
        health = self.client.get('/api/health/')
        assert health.status_code == 200
        print("   ✓ Backend is healthy")
        
        # 2. Get providers
        print("\n2. Fetch available providers...")
        providers = self.client.get('/api/providers/')
        print(f"   ✓ Got {providers.json().get('count', 0)} providers")
        
        # 3. List existing conversations
        print("\n3. List conversations...")
        convs = self.client.get('/api/conversations/')
        print(f"   ✓ Got {len(convs.json())} conversations")
        
        # 4. Create new conversation
        print("\n4. Create new conversation...")
        new_conv = self.client.post(
            '/api/conversations/',
            {
                "title": "Frontend Test Session",
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "document_ids": []
            },
            format='json'
        )
        conv_id = new_conv.json()['conversation_id']
        print(f"   ✓ Created conversation: {conv_id}")
        
        # 5. Send initial message
        print("\n5. Send initial message...")
        msg = self.client.post(
            f'/api/conversations/{conv_id}/messages/',
            {
                "content": "Hello! What can you do?",
                "provider": "gemini",
                "model": "gemini-2.5-flash"
            },
            format='json'
        )
        print(f"   ✓ Got response (latency: {msg.json().get('metrics', {}).get('total_ms', 0)}ms)")
        
        # 6. Get message history
        print("\n6. Get message history...")
        history = self.client.get(f'/api/conversations/{conv_id}/messages/')
        print(f"   ✓ Got {len(history.json())} messages")
        
        print("\n✓ PASS: Frontend-like call sequence successful")
        return True


def run_integration_tests():
    """Run all integration tests"""
    from django.test.utils import get_runner
    from django.conf import settings
    
    print("\n" + "="*70)
    print("FRONTEND-BACKEND INTEGRATION TESTS")
    print("="*70)
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2, interactive=True, keepdb=False)
    
    # Run tests
    failures = test_runner.run_tests([
        "tests.test_frontend_backend_integration.TestFrontendBackendAPI",
        "tests.test_frontend_backend_integration.TestDataFlow",
        "tests.test_frontend_backend_integration.TestFrontendAPICall",
    ])
    
    print("\n" + "="*70)
    if failures:
        print(f"FAILED: {failures} test(s) failed")
    else:
        print("SUCCESS: All tests passed!")
    print("="*70)
    
    return failures == 0


if __name__ == '__main__':
    import django
    django.setup()
    run_integration_tests()
