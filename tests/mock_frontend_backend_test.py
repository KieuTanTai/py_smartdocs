"""
Mock Test: Frontend ↔ Backend Integration
==========================================
Test toàn bộ luồng Frontend gọi Backend qua ApiClient → Django REST API.

Cách chạy:
    # Bước 1: Chạy backend server (terminal 1)
    python manage.py runserver 8000

    # Bước 2: Chạy test (terminal 2)
    python -m tests.mock_frontend_backend_test

    # Hoặc chỉ test một flow:
    python -m tests.mock_frontend_backend_test --flow health
    python -m tests.mock_frontend_backend_test --flow documents
    python -m tests.mock_frontend_backend_test --flow conversations
    python -m tests.mock_frontend_backend_test --flow messages
    python -m tests.mock_frontend_backend_test --flow full
"""

import sys
import os
import io
import time
import json
import argparse
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Fix Windows console encoding for emoji/Unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ──────────────────────────────────────────────────────────────
# Setup Django (cần cho trường hợp test trực tiếp qua Django ORM)
# ──────────────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")
import django
django.setup()

from sys_services.api_client import ApiClient, ApiError

# ──────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────
BACKEND_URL = os.getenv("SMARTDOCS_API_BASE_URL", "http://localhost:8000")
CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# Logging Helpers
# ──────────────────────────────────────────────────────────────
_SEPARATOR = "═" * 80
_SUB_SEP = "─" * 60


class TestResult:
    """Lưu kết quả từng test case."""
    def __init__(self, name: str, passed: bool, detail: str = "", response: Any = None):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.response = response
        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        return f"[{self.timestamp}] {status} | {self.name}\n  → {self.detail}"


def log_section(title: str):
    print(f"\n{_SEPARATOR}")
    print(f"  🧪 {title}")
    print(f"{_SEPARATOR}")


def log_step(step: str, response: Any = None):
    print(f"\n  ▸ {step}")
    if response is not None:
        print(f"    Response: {json.dumps(response, indent=2, ensure_ascii=False, default=str)[:500]}")


# ──────────────────────────────────────────────────────────────
# Test Suites
# ──────────────────────────────────────────────────────────────
results: list[TestResult] = []


def test_health(api: ApiClient) -> TestResult:
    """Test 1: Health Check - Frontend gọi GET /api/health/"""
    log_section("Test 1: Health Check")
    try:
        resp = api.health()
        log_step("GET /api/health/", resp)
        passed = resp.get("status") == "ok"
        return TestResult("Health Check", passed, f"Status: {resp.get('status')}", resp)
    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Health Check", False, str(e))


def test_document_upload(api: ApiClient) -> tuple[TestResult, Optional[str]]:
    """Test 2: Upload Document - Frontend upload file qua POST /api/documents/upload/"""
    log_section("Test 2: Document Upload")

    # Tạo file test PDF giả
    test_file = OUTPUT_DIR / "test_document.txt"
    test_content = """
    Báo cáo tài chính năm 2024
    ==========================
    
    Tổng doanh thu: 150,000,000,000 VND
    Chi phí hoạt động: 95,000,000,000 VND
    Lợi nhuận ròng: 55,000,000,000 VND
    
    Công ty ABC có kết quả kinh doanh tích cực trong năm 2024.
    Doanh thu tăng 15% so với cùng kỳ năm trước.
    Chi phí được kiểm soát tốt, tỷ lệ chi phí/doanh thu giảm từ 68% xuống 63%.
    
    Ban Giám đốc đánh giá cao nỗ lực của toàn bộ nhân viên
    trong việc đạt được các mục tiêu kinh doanh đề ra.
    """
    test_file.write_text(test_content, encoding="utf-8")

    try:
        file_info = {
            "name": "test_document.txt",
            "datapath": str(test_file),
            "type": "text/plain",
        }
        resp = api.upload_document(file_info, source="local")
        log_step("POST /api/documents/upload/", resp)
        doc_id = resp.get("id") or resp.get("document_id")
        passed = doc_id is not None
        return (
            TestResult("Document Upload", passed, f"Document ID: {doc_id}", resp),
            doc_id,
        )
    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Document Upload", False, str(e)), None


def test_document_index(api: ApiClient, doc_id: str) -> TestResult:
    """Test 3: Index Document - Backend xử lý và index nội dung"""
    log_section("Test 3: Document Index")
    try:
        resp = api.index_document(doc_id)
        log_step(f"POST /api/documents/{doc_id}/index/", resp)
        status = resp.get("status")
        passed = status in ("indexed", "processing", "completed")
        return TestResult("Document Index", passed, f"Status: {status}", resp)
    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Document Index", False, str(e))


def test_document_status(api: ApiClient, doc_id: str) -> TestResult:
    """Test 4: Check Document Status"""
    log_section("Test 4: Document Status")
    try:
        resp = api.document_status(doc_id)
        log_step(f"GET /api/documents/{doc_id}/status/", resp)
        passed = resp.get("id") is not None or resp.get("status") is not None
        return TestResult("Document Status", passed, f"Status: {resp.get('status')}", resp)
    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Document Status", False, str(e))


def test_create_conversation(api: ApiClient, doc_ids: list[str]) -> tuple[TestResult, Optional[str]]:
    """Test 5: Create Conversation - Frontend tạo conversation mới kèm documents"""
    log_section("Test 5: Create Conversation")
    try:
        resp = api.create_conversation(
            title="Test Conversation - Mock Test",
            provider="auto",
            model="auto",
            system_prompt="Bạn là trợ lý AI hữu ích, trả lời bằng tiếng Việt.",
            document_ids=doc_ids,
            mode="normal",
        )
        log_step("POST /api/conversations/", resp)
        conv_id = resp.get("conversation_id") or resp.get("id")
        passed = conv_id is not None
        return (
            TestResult("Create Conversation", passed, f"Conversation ID: {conv_id}", resp),
            conv_id,
        )
    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Create Conversation", False, str(e)), None


def test_send_message(api: ApiClient, conv_id: str, message: str) -> tuple[TestResult, Dict]:
    """Test 6: Send Message - Frontend gửi tin nhắn, Backend gọi LLM và trả kết quả"""
    log_section(f"Test 6: Send Message → '{message}'")
    try:
        resp = api.send_message(conv_id, message)
        log_step(f"POST /api/conversations/{conv_id}/messages/", resp)

        assistant_text = resp.get("assistant") or resp.get("content") or resp.get("message") or ""
        used_mock = resp.get("used_mock", False)
        metrics = resp.get("metrics", {})

        print(f"\n  📨 User: {message}")
        print(f"  🤖 Assistant: {assistant_text[:300]}...")
        print(f"  📊 Metrics: provider={metrics.get('provider')}, model={metrics.get('model')}, "
              f"latency={metrics.get('total_ms')}ms")
        if used_mock:
            print("  ⚠️  Đã dùng mock response (LLM không khả dụng)")

        passed = len(assistant_text) > 0
        return (
            TestResult("Send Message", passed, f"Response length: {len(assistant_text)} chars, mock={used_mock}", resp),
            resp,
        )
    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Send Message", False, str(e)), {}


def test_list_conversations(api: ApiClient) -> TestResult:
    """Test 7: List Conversations - Frontend load danh sách conversations"""
    log_section("Test 7: List Conversations")
    try:
        resp = api.list_conversations()
        log_step("GET /api/conversations/", resp)
        if isinstance(resp, list):
            count = len(resp)
        elif isinstance(resp, dict):
            count = len(resp.get("results", resp.get("data", [])))
        else:
            count = 0
        passed = True  # Chỉ cần không lỗi
        return TestResult("List Conversations", passed, f"Found {count} conversations", resp)
    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("List Conversations", False, str(e))


def test_update_conversation_docs(api: ApiClient, conv_id: str, doc_ids: list[str]) -> TestResult:
    """Test 8: Update Documents cho Conversation"""
    log_section("Test 8: Update Conversation Documents")
    try:
        resp = api.update_conversation_documents(conv_id, doc_ids)
        log_step(f"PATCH /api/conversations/{conv_id}/documents/", resp)
        passed = resp.get("status") == "updated" or "error" not in resp
        return TestResult("Update Conv Documents", passed, f"Response: {resp}", resp)
    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Update Conv Documents", False, str(e))


def test_multi_turn_conversation(api: ApiClient, conv_id: str) -> list[TestResult]:
    """Test 9: Multi-turn Conversation - Gửi nhiều tin nhắn liên tiếp"""
    log_section("Test 9: Multi-turn Conversation")
    questions = [
        "Tổng doanh thu năm 2024 là bao nhiêu?",
        "Lợi nhuận ròng là bao nhiêu?",
        "Doanh thu tăng bao nhiêu phần trăm so với năm trước?",
    ]
    turn_results = []
    for i, q in enumerate(questions, 1):
        print(f"\n  --- Turn {i}/{len(questions)} ---")
        result, resp = test_send_message(api, conv_id, q)
        result.name = f"Multi-turn #{i}: {q[:30]}..."
        turn_results.append(result)
        time.sleep(0.5)  # Nhẹ nhàng giữa các request
    return turn_results


# ──────────────────────────────────────────────────────────────
# Full Integration Flow
# ──────────────────────────────────────────────────────────────
def run_full_flow(api: ApiClient):
    """Chạy toàn bộ luồng Frontend ↔ Backend từ đầu đến cuối."""
    global results

    # 1. Health Check
    results.append(test_health(api))

    # 2. Upload Document
    upload_result, doc_id = test_document_upload(api)
    results.append(upload_result)
    if not doc_id:
        print("\n⛔ Không upload được document, dừng test.")
        return

    # 3. Index Document
    results.append(test_document_index(api, doc_id))

    # 4. Check Document Status
    results.append(test_document_status(api, doc_id))

    # 5. Create Conversation
    conv_result, conv_id = test_create_conversation(api, [doc_id])
    results.append(conv_result)
    if not conv_id:
        print("\n⛔ Không tạo được conversation, dừng test.")
        return

    # 6. Send Single Message
    msg_result, msg_resp = test_send_message(api, conv_id, "Tóm tắt nội dung tài liệu này")
    results.append(msg_result)

    # 7. List Conversations
    results.append(test_list_conversations(api))

    # 8. Update Conversation Documents
    results.append(test_update_conversation_docs(api, conv_id, [doc_id]))

    # 9. Multi-turn
    turn_results = test_multi_turn_conversation(api, conv_id)
    results.extend(turn_results)


def run_single_flow(api: ApiClient, flow: str):
    """Chạy một flow cụ thể."""
    global results
    if flow == "health":
        results.append(test_health(api))
    elif flow == "documents":
        upload_result, doc_id = test_document_upload(api)
        results.append(upload_result)
        if doc_id:
            results.append(test_document_index(api, doc_id))
            results.append(test_document_status(api, doc_id))
    elif flow == "conversations":
        conv_result, conv_id = test_create_conversation(api, [])
        results.append(conv_result)
        if conv_id:
            results.append(test_list_conversations(api))
    elif flow == "messages":
        # Tạo nhanh conversation rồi gửi message
        upload_result, doc_id = test_document_upload(api)
        results.append(upload_result)
        doc_ids = [doc_id] if doc_id else []
        conv_result, conv_id = test_create_conversation(api, doc_ids)
        results.append(conv_result)
        if conv_id:
            msg_result, _ = test_send_message(api, conv_id, "Xin chào, hãy giới thiệu về mình")
            results.append(msg_result)
    elif flow == "full":
        run_full_flow(api)
    else:
        print(f"❌ Unknown flow: {flow}. Chọn: health, documents, conversations, messages, full")
        return


# ──────────────────────────────────────────────────────────────
# Report
# ──────────────────────────────────────────────────────────────
def print_report():
    print(f"\n\n{'═' * 80}")
    print("  📋 BÁO CÁO KẾT QUẢ TEST")
    print(f"{'═' * 80}")

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)

    for r in results:
        print(f"  {r}")

    print(f"\n{_SUB_SEP}")
    print(f"  Tổng cộng: {total} tests | ✅ Passed: {passed} | ❌ Failed: {failed}")
    if failed == 0:
        print("  🎉 TẤT CẢ TEST ĐỀU PASSED!")
    else:
        print(f"  ⚠️  Có {failed} test FAILED - kiểm tra lại backend.")
    print(f"{_SUB_SEP}\n")

    # Save to file
    report_file = OUTPUT_DIR / "mock_test_results.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"Mock Test Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'=' * 60}\n")
        f.write(f"Backend URL: {BACKEND_URL}\n\n")
        for r in results:
            f.write(f"{r}\n")
        f.write(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}\n")
    print(f"  📄 Report saved to: {report_file}")


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock test Frontend ↔ Backend")
    parser.add_argument(
        "--flow",
        default="full",
        choices=["health", "documents", "conversations", "messages", "full"],
        help="Chọn flow test (default: full)",
    )
    parser.add_argument(
        "--url",
        default=BACKEND_URL,
        help=f"Backend URL (default: {BACKEND_URL})",
    )
    args = parser.parse_args()

    print(f"\n🚀 Bắt đầu Mock Test - Backend URL: {args.url}")
    print(f"   Flow: {args.flow}")
    print(f"   Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    api = ApiClient(base_url=args.url, timeout=30.0)

    run_single_flow(api, args.flow)
    print_report()
