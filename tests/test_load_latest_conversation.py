"""
Edge Case Test: Load Latest Conversation on Page Load
=====================================================
Tests the behavior of loading the most recent conversation when the page loads.

Cách chạy:
    # Bước 1: Chạy backend server (terminal 1)
    python manage.py runserver 8000

    # Bước 2: Chạy test (terminal 2)
    python -m tests.test_load_latest_conversation
"""

import sys
import os
import io
import time
import json
import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Fix Windows console encoding for emoji/Unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ──────────────────────────────────────────────────────────────
# Setup Django
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
# Helpers
# ──────────────────────────────────────────────────────────────
_SEPARATOR = "═" * 80
_SUB_SEP = "─" * 60


class TestResult:
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


results: list[TestResult] = []


# ──────────────────────────────────────────────────────────────
# Test Cases
# ──────────────────────────────────────────────────────────────


def test_load_latest_conversation_when_exists(api: ApiClient) -> TestResult:
    """
    Edge Case 1: Khi có conversations trong DB, page load phải lấy được
    conversation gần nhất (đầu tiên trong danh sách sorted by created_at desc).
    """
    log_section("Test 1: Load Latest Conversation — When Conversations Exist")

    try:
        # Step 1: Tạo 2 conversations để đảm bảo có data
        log_step("Creating conversation #1 (older)")
        conv1 = api.create_conversation(
            title="Older Conversation",
            provider="auto",
            model="auto",
            system_prompt="",
            document_ids=[],
            mode="normal",
        )
        conv1_id = conv1.get("conversation_id") or conv1.get("id")
        log_step(f"Created conv #1: {conv1_id}", conv1)

        time.sleep(0.5)  # Đảm bảo timestamp khác nhau

        log_step("Creating conversation #2 (newer)")
        conv2 = api.create_conversation(
            title="Newer Conversation",
            provider="auto",
            model="auto",
            system_prompt="",
            document_ids=[],
            mode="normal",
        )
        conv2_id = conv2.get("conversation_id") or conv2.get("id")
        log_step(f"Created conv #2: {conv2_id}", conv2)

        # Step 2: Simulate page load — GET /api/conversations/ (sorted desc)
        log_step("Simulating page load: GET /api/conversations/")
        resp = api.list_conversations()
        log_step("Conversations list", resp)

        # Normalize response format
        if isinstance(resp, list):
            conversations = resp
        elif isinstance(resp, dict):
            conversations = resp.get("results", resp.get("data", []))
        else:
            conversations = []

        if not conversations:
            return TestResult(
                "Load Latest Conversation (exists)",
                False,
                "No conversations returned from API"
            )

        # Step 3: Verify first item is the newest conversation
        latest = conversations[0]
        latest_id = str(latest.get("id") or latest.get("conversation_id"))

        log_step(f"Latest conversation ID: {latest_id}")
        log_step(f"Expected (newest): {conv2_id}")

        passed = latest_id == str(conv2_id)
        detail = (
            f"Latest ID={latest_id}, expected={conv2_id}. "
            f"Total conversations: {len(conversations)}"
        )
        if not passed:
            detail += " — ORDER INCORRECT! Newest should be first."

        return TestResult("Load Latest Conversation (exists)", passed, detail, resp)

    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Load Latest Conversation (exists)", False, str(e))


def test_load_latest_conversation_when_empty(api: ApiClient) -> TestResult:
    """
    Edge Case 2: Khi không có conversations (hoặc DB trống), page load
    phải trả về danh sách rỗng mà không crash.
    
    Note: Trong thực tế DB có thể có data từ test trước, nên test này
    chỉ verify rằng API trả về list hợp lệ (không error).
    """
    log_section("Test 2: Load Latest Conversation — API Returns Valid Response")

    try:
        log_step("GET /api/conversations/ — checking response is valid")
        resp = api.list_conversations()
        log_step("Response", resp)

        # Verify response format is valid (list or dict with data)
        if isinstance(resp, list):
            passed = True
            detail = f"Got valid list with {len(resp)} conversations"
        elif isinstance(resp, dict):
            items = resp.get("results", resp.get("data", []))
            passed = isinstance(items, list)
            detail = f"Got valid dict response with {len(items)} conversations"
        else:
            passed = False
            detail = f"Unexpected response type: {type(resp)}"

        return TestResult("Load Conversations (valid response)", passed, detail, resp)

    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Load Conversations (valid response)", False, str(e))


def test_latest_conversation_has_messages(api: ApiClient) -> TestResult:
    """
    Edge Case 3: Khi load conversation gần nhất, messages phải được
    load đúng (ít nhất có bootstrap message).
    """
    log_section("Test 3: Latest Conversation Has Messages")

    try:
        # Step 1: Tạo conversation mới
        log_step("Creating a new conversation")
        conv = api.create_conversation(
            title="Test Messages Load",
            provider="auto",
            model="auto",
            system_prompt="",
            document_ids=[],
            mode="normal",
        )
        conv_id = conv.get("conversation_id") or conv.get("id")
        log_step(f"Created conversation: {conv_id}", conv)

        if not conv_id:
            return TestResult(
                "Latest Conversation Has Messages",
                False,
                "Failed to create conversation"
            )

        # Step 2: Simulate page load — get conversations list
        log_step("GET /api/conversations/")
        convs = api.list_conversations()
        if isinstance(convs, list):
            conversations = convs
        elif isinstance(convs, dict):
            conversations = convs.get("results", convs.get("data", []))
        else:
            conversations = []

        if not conversations:
            return TestResult(
                "Latest Conversation Has Messages",
                False,
                "No conversations found"
            )

        latest_id = str(conversations[0].get("id") or conversations[0].get("conversation_id"))
        log_step(f"Latest conversation: {latest_id}")

        # Step 3: Load messages for the latest conversation
        log_step(f"GET /api/conversations/{latest_id}/messages/")
        try:
            msgs_resp = api._request("GET", f"/api/conversations/{latest_id}/messages/")
            log_step("Messages response", msgs_resp)

            if isinstance(msgs_resp, list):
                messages = msgs_resp
            elif isinstance(msgs_resp, dict):
                messages = msgs_resp.get("results", msgs_resp.get("data", []))
            else:
                messages = []

            passed = len(messages) > 0
            detail = f"Found {len(messages)} messages for conversation {latest_id}"
            if passed:
                first_msg = messages[0]
                detail += f"\n  First message role: {first_msg.get('role')}"
                detail += f"\n  Content preview: {str(first_msg.get('content', ''))[:100]}..."
            else:
                detail += " — Expected at least a bootstrap message"

            return TestResult("Latest Conversation Has Messages", passed, detail, msgs_resp)

        except ApiError as e:
            return TestResult("Latest Conversation Has Messages", False, f"Failed to load messages: {e}")

    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Latest Conversation Has Messages", False, str(e))


def test_conversation_ordering_consistency(api: ApiClient) -> TestResult:
    """
    Edge Case 4: Tạo nhiều conversations liên tiếp, verify ordering
    luôn nhất quán (newest first).
    """
    log_section("Test 4: Conversation Ordering Consistency")

    try:
        created_ids = []
        for i in range(3):
            conv = api.create_conversation(
                title=f"Ordering Test #{i+1}",
                provider="auto",
                model="auto",
                system_prompt="",
                document_ids=[],
                mode="normal",
            )
            cid = conv.get("conversation_id") or conv.get("id")
            created_ids.append(str(cid))
            log_step(f"Created conversation #{i+1}: {cid}")
            time.sleep(0.3)

        # Get list
        log_step("GET /api/conversations/")
        resp = api.list_conversations()
        if isinstance(resp, list):
            conversations = resp
        elif isinstance(resp, dict):
            conversations = resp.get("results", resp.get("data", []))
        else:
            conversations = []

        list_ids = [str(c.get("id") or c.get("conversation_id")) for c in conversations]

        # The last created should be first in list
        expected_first = created_ids[-1]
        actual_first = list_ids[0] if list_ids else None

        passed = actual_first == expected_first
        detail = f"Expected first={expected_first}, actual first={actual_first}"

        if not passed:
            # Check if our IDs are even in the list
            found = [cid for cid in created_ids if cid in list_ids]
            detail += f"\n  Created IDs found in list: {len(found)}/{len(created_ids)}"

        return TestResult("Conversation Ordering Consistency", passed, detail, resp)

    except Exception as e:
        log_step(f"FAILED: {e}")
        return TestResult("Conversation Ordering Consistency", False, str(e))


# ──────────────────────────────────────────────────────────────
# Report
# ──────────────────────────────────────────────────────────────
def print_report():
    print(f"\n\n{'═' * 80}")
    print("  📋 BÁO CÁO KẾT QUẢ TEST — EDGE CASE: LOAD LATEST CONVERSATION")
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
        print(f"  ⚠️  Có {failed} test FAILED.")
    print(f"{_SUB_SEP}\n")

    # Save to file
    report_file = OUTPUT_DIR / "edge_case_latest_conversation_results.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"Edge Case Test Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
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
    print(f"\n🚀 Edge Case Test: Load Latest Conversation")
    print(f"   Backend URL: {BACKEND_URL}")
    print(f"   Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    api = ApiClient(base_url=BACKEND_URL, timeout=30.0)

    # Run all edge case tests
    results.append(test_load_latest_conversation_when_empty(api))
    results.append(test_load_latest_conversation_when_exists(api))
    results.append(test_latest_conversation_has_messages(api))
    results.append(test_conversation_ordering_consistency(api))

    print_report()
