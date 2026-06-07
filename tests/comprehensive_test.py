"""
Comprehensive integration test suite for py_smartdocs backend.

Tests cover:
1. API health check
2. Document CRUD (upload, list, detail, delete)
3. Document indexing with FAISS
4. Conversation CRUD
5. Message sending with RAG (keyword fallback since no docs indexed)
6. Providers endpoint
7. LLM providers (Gemini, Mistral, Ollama)
8. FAISS vector store

Run from project root:
    python -c "exec(open('tests/comprehensive_test.py').read())"
"""
import sys
import os
import time
import tempfile
import json
from pathlib import Path

# Fix stdout encoding for Windows console
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Fix paths so Django can find 'app' and 'backend'
_ROOT = r"D:\DAPYT\py_smartdocs"
os.chdir(_ROOT)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

# Setup Django
import django
django.setup()

import httpx
import numpy as np
from rest_framework.test import APIClient

BASE_URL = "http://127.0.0.1:8000"
import requests

# Use requests client to hit the running server (avoids Django test client issues)
_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})

# For multipart uploads (document upload)
_multipart_session = requests.Session()

from rest_framework.test import APIClient
# Keep APIClient for reference, but use requests for actual testing
client = _session
multipart_client = _multipart_session

RESULTS: list[dict] = []


def log(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {name}" + (f" - {detail}" if detail else ""))
    RESULTS.append({"name": name, "passed": passed, "detail": detail})


def run_test(name: str):
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print("=" * 60)


# ─── TEST 1: Health Check ────────────────────────────────────────────────────
run_test("TEST 1: Health Check")
try:
    resp = client.get(BASE_URL + "/api/health/")
    log("GET /api/health/", resp.status_code == 200, f"status={resp.status_code}")
    data = resp.json()
    log("  Response has 'status'", "status" in data)
    log("  Response has 'detail'", "detail" in data)
except Exception as e:
    log("GET /api/health/", False, str(e)[:100])

# ─── TEST 2: Providers Endpoint ───────────────────────────────────────────────
run_test("TEST 2: Providers Endpoint")
try:
    resp = client.get(BASE_URL + "/api/providers/")
    log("GET /api/providers/", resp.status_code == 200, f"status={resp.status_code}")
    data = resp.json()
    log("  Has 'providers' key", "providers" in data)
    log("  Has at least 1 provider", len(data.get("providers", [])) >= 1)
    for p in data.get("providers", []):
        log(f"  Provider: {p.get('name')}", True)
        log(f"    Has 'models'", "models" in p)
        log(f"    Has 'embed_model'", "embed_model" in p)
except Exception as e:
    log("GET /api/providers/", False, str(e)[:100])

# ─── TEST 3: Document Upload ──────────────────────────────────────────────────
run_test("TEST 3: Document Upload")
test_doc_id = None
try:
    # Create a small test text file
    content = b"Hello World! This is a test document for vector search.\n" * 10
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(content)
        temp_path = f.name

    with open(temp_path, "rb") as f:
        resp = multipart_client.post(
            BASE_URL + "/api/documents/upload/",
            data={"source": "local"},
            files={"file": ("test_doc.txt", f, "text/plain")},
        )
    os.unlink(temp_path)

    log("POST /api/documents/upload/", resp.status_code in [200, 201], f"status={resp.status_code}")
    data = resp.json()
    log("  Has 'id'", "id" in data)
    log("  Has 'title'", "title" in data)
    log("  Has 'status'", "status" in data)
    test_doc_id = data.get("id")
    log("  Doc ID is not None", test_doc_id is not None)
except Exception as e:
    log("POST /api/documents/upload/", False, str(e)[:100])

# ─── TEST 4: Document List ─────────────────────────────────────────────────────
run_test("TEST 4: Document List")
try:
    resp = client.get(BASE_URL + "/api/documents/")
    log("GET /api/documents/", resp.status_code == 200, f"status={resp.status_code}")
    data = resp.json()
    log("  Response is list", isinstance(data, list))
    log("  Has at least 1 doc", len(data) >= 1)
    for doc in data:
        log(f"  Doc: {doc.get('title', '?')}", True)
        log(f"    Has 'id'", "id" in doc)
        log(f"    Has 'status'", "status" in doc)
except Exception as e:
    log("GET /api/documents/", False, str(e)[:100])

# ─── TEST 5: Document Detail ───────────────────────────────────────────────────
run_test("TEST 5: Document Detail")
if test_doc_id:
    try:
        resp = client.get(f"{BASE_URL}/api/documents/{test_doc_id}/")
        log(f"GET /api/documents/{test_doc_id}/", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.json()
        log("  Has 'id'", "id" in data)
        log("  Has 'status'", "status" in data)
    except Exception as e:
        log("GET /api/documents/{id}/", False, str(e)[:100])
else:
    log("GET /api/documents/{id}/", False, "Skipped - no doc ID")

# ─── TEST 6: Document Index (FAISS Vector Pipeline) ───────────────────────────
run_test("TEST 6: Document Index (FAISS Vector Pipeline)")
if test_doc_id:
    try:
        resp = client.post(f"{BASE_URL}/api/documents/{test_doc_id}/index/")
        log(f"POST /api/documents/{test_doc_id}/index/", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.json()
        log("  Has 'id'", "id" in data)
        log("  Has 'status' = indexed", data.get("status") == "indexed")
        log("  Has 'chunks' >= 1", (data.get("chunks", 0)) >= 1)
        log("  Has 'dimensions' > 0", (data.get("dimensions", 0)) > 0)
    except Exception as e:
        log("POST /api/documents/{id}/index/", False, str(e)[:100])
else:
    log("POST /api/documents/{id}/index/", False, "Skipped - no doc ID")

# ─── TEST 7: Conversation CRUD ────────────────────────────────────────────────
run_test("TEST 7: Conversation CRUD")
test_conv_id = None
try:
    # Create
    resp = client.post(BASE_URL + "/api/conversations/", json={})
    log("POST /api/conversations/ (create)", resp.status_code == 201, f"status={resp.status_code}")
    data = resp.json()
    log("  Has 'conversation_id'", "conversation_id" in data)
    test_conv_id = data.get("conversation_id")
    log("  Has 'title'", "title" in data)
    log("  Has 'status'", "status" in data)

    # List
    resp = client.get(BASE_URL + "/api/conversations/")
    log("GET /api/conversations/", resp.status_code == 200, f"status={resp.status_code}")
    data = resp.json()
    log("  Response is list", isinstance(data, list))
    log("  Has at least 1 conv", len(data) >= 1)

    # Detail
    if test_conv_id:
        resp = client.get(f"{BASE_URL}/api/conversations/{test_conv_id}/")
        log(f"GET /api/conversations/{test_conv_id}/", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.json()
        log("  Has 'id'", "id" in data)
        log("  Has 'title'", "title" in data)

    # Attach doc
    if test_conv_id and test_doc_id:
        resp = client.patch(
            f"{BASE_URL}/api/conversations/{test_conv_id}/documents/",
            json={"document_ids": [test_doc_id]},
        )
        log(f"PATCH /api/conversations/{test_conv_id}/documents/", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.json()
        log("  Has 'status' = updated", data.get("status") == "updated")

except Exception as e:
    log("Conversation CRUD", False, str(e)[:100])

# ─── TEST 8: Message Send (RAG with Keyword Fallback) ────────────────────────
run_test("TEST 8: Message Send with RAG")
if test_conv_id:
    try:
        resp = client.post(
            f"{BASE_URL}/api/conversations/{test_conv_id}/messages/",
            json={"content": "What is this document about?", "model": "qwen2.5:1.5b-instruct"},
        )
        log(f"POST /api/conversations/{test_conv_id}/messages/", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.json()
        log("  Has 'assistant'", "assistant" in data)
        log("  Has 'metrics'", "metrics" in data)
        log("  Has 'conversation_id'", "conversation_id" in data)
        metrics = data.get("metrics", {})
        log("  Metrics has 'provider'", "provider" in metrics)
        log("  Metrics has 'total_ms' > 0", metrics.get("total_ms", 0) > 0)
        log("  Assistant response not empty", len(data.get("assistant", "")) > 0)
        log("  used_mock is False", data.get("used_mock") == False)
    except Exception as e:
        log("POST messages/", False, str(e)[:100])
else:
    log("POST messages/", False, "Skipped - no conv ID")

# ─── TEST 9: Message List ────────────────────────────────────────────────────
run_test("TEST 9: Message List")
if test_conv_id:
    try:
        resp = client.get(f"{BASE_URL}/api/conversations/{test_conv_id}/messages/")
        log(f"GET /api/conversations/{test_conv_id}/messages/", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.json()
        log("  Response is list", isinstance(data, list))
        log("  Has messages", len(data) >= 2)  # bootstrap + user + assistant = 3
        roles = [m.get("role") for m in data]
        log("  Has user message", "user" in roles)
        log("  Has assistant message", "assistant" in roles)
    except Exception as e:
        log("GET messages/", False, str(e)[:100])
else:
    log("GET messages/", False, "Skipped - no conv ID")

# ─── TEST 10: LLM Provider Tests ─────────────────────────────────────────────
run_test("TEST 10: LLM Provider Tests")

from backend.apps.llm.gemini import GeminiClient
from backend.apps.llm.mistral import MistralClient
from backend.apps.llm.ollama import OllamaClient
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER

# Gemini
try:
    config = DEFAULT_CONFIG_PROVIDER.get_gemini_config()
    gemini = GeminiClient(api_key=config["api_key"], timeout=config["timeout_seconds"], logger=DEFAULT_LOGGER)
    req = ICompletionRequest(provider=EProviderName.GEMINI, model="gemini-3.1-flash-lite", prompt="Say hello.")
    result = gemini.generate(req)
    log("Gemini generate()", len(result) > 0, result[:50])
except Exception as e:
    log("Gemini generate()", False, str(e)[:80])

# Gemini embedding
try:
    req = ICompletionRequest(provider=EProviderName.GEMINI, model="gemini-embedding-2", prompt="Test")
    result = gemini.embedding(req)
    log("Gemini embedding()", result.dimensions > 0, f"dims={result.dimensions}")
except Exception as e:
    log("Gemini embedding()", False, str(e)[:80])

# Mistral
try:
    config = DEFAULT_CONFIG_PROVIDER.get_mistral_config()
    mistral = MistralClient(api_key=config["api_key"], timeout=config["timeout_seconds"], logger=DEFAULT_LOGGER)
    req = ICompletionRequest(provider=EProviderName.MISTRAL, model="mistral-large-latest", prompt="Say hello.")
    result = mistral.generate(req)
    log("Mistral generate()", len(result) > 0, result[:50])
except Exception as e:
    log("Mistral generate()", False, str(e)[:80])

# Ollama
try:
    config = DEFAULT_CONFIG_PROVIDER.get_ollama_config()
    ollama = OllamaClient(base_url=config["base_url"], timeout=config["timeout_seconds"], logger=DEFAULT_LOGGER)
    req = ICompletionRequest(provider=EProviderName.OLLAMA, model="qwen2.5:1.5b-instruct", prompt="Say hello.")
    result = ollama.generate(req)
    log("Ollama generate()", len(result) > 0, result[:50])
except Exception as e:
    log("Ollama generate()", False, str(e)[:80])

# ─── TEST 11: FAISS Vector Store ──────────────────────────────────────────────
run_test("TEST 11: FAISS Vector Store")

from backend.apps.services.rag_base.locate.locate_service import LocateService
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from sys_services.system_dirs import METADATA_DIR

try:
    locate = LocateService(metadata_dir=METADATA_DIR, logger=DEFAULT_LOGGER)
    faiss = locate.get_vector_store(EBackendStorageName.FAISS)
    log("FAISS service created", True)

    # Create test vectors
    vectors = np.array([[1.0, 0.5, 0.2], [0.1, 1.0, 0.3], [0.2, 0.3, 1.0]], dtype=np.float32)
    test_id = "integration-test-001"

    index = faiss.create_index(vectors)
    log("FAISS index created", True)

    upsert = faiss.upsert(index, test_id)
    log("FAISS upsert()", upsert.is_success)

    query = np.array([[0.9, 0.6, 0.3]], dtype=np.float32)
    search = faiss.search(index, test_id, query, limit=2)
    log("FAISS search()", len(search.indices) >= 1)
    log("  Has distances", len(search.distances) >= 1)
    log("  Has indices", len(search.indices) >= 1)

    loaded = faiss.load(test_id)
    log("FAISS load()", loaded.is_success)

    deleted = faiss.delete(test_id)
    log("FAISS delete()", deleted.is_success)

except Exception as e:
    import traceback
    traceback.print_exc()
    log("FAISS Vector Store", False, str(e)[:100])

# ─── TEST 12: Document Delete ────────────────────────────────────────────────
run_test("TEST 12: Document Delete")
if test_doc_id:
    try:
        resp = client.delete(f"{BASE_URL}/api/documents/{test_doc_id}/")
        log(f"DELETE /api/documents/{test_doc_id}/", resp.status_code == 200, f"status={resp.status_code}")
        data = resp.json()
        log("  Has 'status' = deleted", data.get("status") == "deleted")
    except Exception as e:
        log("DELETE /api/documents/{id}/", False, str(e)[:100])
else:
    log("DELETE /api/documents/{id}/", False, "Skipped - no doc ID")

# ─── TEST 13: Delete Conversation ───────────────────────────────────────────
run_test("TEST 13: Conversation Delete")
if test_conv_id:
    try:
        # Remove from DB directly (no dedicated delete endpoint exists)
        from backend.apps.services.chat.models import ConversationModel
        ConversationModel.objects.filter(pk=test_conv_id).delete()
        log("Conversation deleted from DB", True)
    except Exception as e:
        log("Conversation delete", False, str(e)[:100])

# ─── SUMMARY ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  SUMMARY")
print("=" * 60)
total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["passed"])
failed = sum(1 for r in RESULTS if not r["passed"])
print(f"  Total:  {total}")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Rate:   {100*passed/max(total,1):.1f}%")
print("=" * 60)

if failed > 0:
    print("\n  FAILED TESTS:")
    for r in RESULTS:
        if not r["passed"]:
            print(f"  - {r['name']}: {r['detail']}")

print()
