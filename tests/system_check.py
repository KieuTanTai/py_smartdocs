"""
System Check - py_smartdocs integration test suite.

Tests everything in one run:
1. All LLM providers (Gemini, Mistral, Ollama) - generate + embeddings
2. Mistral OCR with UPLOAD_FILES mode
3. Document upload pipeline (frontend API client → Django backend)
4. Document indexing with FAISS
5. Frontend-backend connectivity

Run with both servers running:
    Backend:  python manage.py runserver 8000
    Frontend: python -m shiny run --app-dir frontend --port 8001

    Then: python -c "exec(open('tests/system_check.py').read())"
"""

import sys
import os

# Fix stdout encoding for Windows console
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

_ROOT = r"D:\DAPYT\py_smartdocs"
os.chdir(_ROOT)
sys.path.insert(0, _ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

# Setup Django first
import django
django.setup()

# ── Imports ──────────────────────────────────────────────────────────────────
import time
import tempfile
import traceback
import httpx
from pathlib import Path

from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from backend.apps.llm.gemini import GeminiClient
from backend.apps.llm.mistral import MistralClient
from backend.apps.llm.ollama import OllamaClient
from backend.apps.llm.llm_ocr.mistral_ocr import MistralLLMOCR
from backend.apps.llm.llm_ocr.mistral_uploader import MistralUploader
from backend.apps.services.rag_base.storage.storage_service import FileStorageService
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.services.rag_base.locate.locate_service import LocateService
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from sys_services.system_dirs import METADATA_DIR

import numpy as np

# ── Test Runner ──────────────────────────────────────────────────────────────
RESULTS: list[dict] = []


def log(name: str, passed: bool, detail: str = ""):
    status = "PASS" if passed else "FAIL"
    prefix = "  " if "  " in name else ""
    print(f"{prefix}[{status}] {name}" + (f" - {detail}" if detail else ""))
    RESULTS.append({"name": name, "passed": passed, "detail": str(detail)[:120]})


def section(name: str):
    print(f"\n{'=' * 70}")
    print(f"  {name}")
    print("=" * 70)


# ════════════════════════════════════════════════════════════════════════════
#  PART 1 — LLM PROVIDERS
# ════════════════════════════════════════════════════════════════════════════
section("PART 1 — LLM PROVIDERS")

# ── 1.1 Gemini ──────────────────────────────────────────────────────────────
section("  1.1 Gemini")
try:
    config = DEFAULT_CONFIG_PROVIDER.get_gemini_config()
    log("  Config loaded", True, f"api_key set={bool(config.get('api_key'))}")
    gemini = GeminiClient(
        api_key=config["api_key"],
        timeout=config["timeout_seconds"],
        logger=DEFAULT_LOGGER,
    )
    log("  GeminiClient created", True)
except Exception as e:
    log("  GeminiClient init", False, e)
    gemini = None

if gemini:
    try:
        req = ICompletionRequest(
            provider=EProviderName.GEMINI,
            model="gemini-3.1-flash-lite",
            prompt="Reply with exactly one word: hello",
        )
        result = gemini.generate(req)
        log("  generate()", len(result.strip()) > 0, result[:60].strip())
    except Exception as e:
        log("  generate()", False, e)

    try:
        req = ICompletionRequest(
            provider=EProviderName.GEMINI,
            model="gemini-embedding-2",
            prompt="vector search document",
        )
        emb = gemini.embedding(req)
        log("  embedding()", emb.dimensions > 0, f"dims={emb.dimensions}, shape={emb.shape}")
    except Exception as e:
        log("  embedding()", False, e)

    try:
        ok = gemini.is_available("gemini-3.1-flash-lite")
        log("  is_available()", ok, "available" if ok else "unavailable")
    except Exception as e:
        log("  is_available()", False, e)

# ── 1.2 Mistral ─────────────────────────────────────────────────────────────
section("  1.2 Mistral")
try:
    config = DEFAULT_CONFIG_PROVIDER.get_mistral_config()
    log("  Config loaded", True, f"api_key set={bool(config.get('api_key'))}")
    mistral = MistralClient(
        api_key=config["api_key"],
        timeout=config["timeout_seconds"],
        logger=DEFAULT_LOGGER,
    )
    log("  MistralClient created", True)
except Exception as e:
    log("  MistralClient init", False, e)
    mistral = None

if mistral:
    try:
        req = ICompletionRequest(
            provider=EProviderName.MISTRAL,
            model="mistral-large-latest",
            prompt="Reply with exactly one word: hello",
        )
        result = mistral.generate(req)
        log("  generate()", len(result.strip()) > 0, result[:60].strip())
    except Exception as e:
        log("  generate()", False, e)

    try:
        req = ICompletionRequest(
            provider=EProviderName.MISTRAL,
            model="mistral-embed",
            prompt="vector search document",
        )
        emb = mistral.embedding(req)
        log("  embedding()", emb.dimensions > 0, f"dims={emb.dimensions}, shape={emb.shape}")
    except Exception as e:
        log("  embedding()", False, e)

    try:
        ok = mistral.is_available("mistral-large-latest")
        log("  is_available()", ok, "available" if ok else "unavailable")
    except Exception as e:
        log("  is_available()", False, e)

# ── 1.3 Ollama ──────────────────────────────────────────────────────────────
section("  1.3 Ollama")
try:
    config = DEFAULT_CONFIG_PROVIDER.get_ollama_config()
    log("  Config loaded", True, f"base_url={config.get('base_url')}")
    ollama = OllamaClient(
        base_url=config["base_url"],
        timeout=config["timeout_seconds"],
        logger=DEFAULT_LOGGER,
    )
    log("  OllamaClient created", True)
except Exception as e:
    log("  OllamaClient init", False, e)
    ollama = None

if ollama:
    try:
        req = ICompletionRequest(
            provider=EProviderName.OLLAMA,
            model="qwen2.5:1.5b-instruct",
            prompt="Reply with exactly one word: hello",
        )
        result = ollama.generate(req)
        log("  generate()", len(result.strip()) > 0, result[:60].strip())
    except Exception as e:
        log("  generate()", False, e)

    try:
        req = ICompletionRequest(
            provider=EProviderName.OLLAMA,
            model="qwen3-embedding",
            prompt="vector search document",
        )
        emb = ollama.embedding(req)
        log("  embedding()", emb.dimensions > 0, f"dims={emb.dimensions}, shape={emb.shape}")
    except Exception as e:
        log("  embedding()", False, e)

    try:
        ok = ollama.is_available("qwen2.5:1.5b-instruct")
        log("  is_available()", ok, "available" if ok else "unavailable")
    except Exception as e:
        log("  is_available()", False, e)


# ════════════════════════════════════════════════════════════════════════════
#  PART 2 — Mistral OCR (UPLOAD_FILES mode)
# ════════════════════════════════════════════════════════════════════════════
section("PART 2 — Mistral OCR (UPLOAD_FILES)")

try:
    m_cfg = DEFAULT_CONFIG_PROVIDER.get_mistral_config()
    ocr = MistralLLMOCR(
        api_key=m_cfg["api_key"],
        model=m_cfg.get("mistral_ocr_model", "mistral-ocr-latest"),
        provider_name=EProviderName.MISTRAL.value,
        timeout_seconds=m_cfg.get("mistral_timeout_seconds", 60),
        logger=DEFAULT_LOGGER,
    )
    log("  MistralLLMOCR created", True, f"model={m_cfg.get('mistral_ocr_model')}")

    # Build FileStorageService using MistralUploader
    uploader = MistralUploader(logger=DEFAULT_LOGGER)
    storage_dir = Path(METADATA_DIR).parent / "storage" / "media"
    storage_dir.mkdir(parents=True, exist_ok=True)
    storage = FileStorageService(
        storage_dir=storage_dir,
        uploader=uploader,
        logger=DEFAULT_LOGGER,
    )
    log("  FileStorageService created", True)

    # Create temp test file
    test_content = b"SmartDocs System Check\nThis is a test document for OCR processing.\nLine three of the document."
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    # Upload to Mistral via FileStorageService
    file_resp = storage.save_file(file_path=temp_path)
    file_id = getattr(file_resp, "id", None)
    log("  storage.save_file()", bool(file_id), f"id={file_id}")

    if file_id:
        ocr_text = ocr.process_ocr(file_resp)
        log("  OCR process_ocr()", len(ocr_text.strip()) > 0, ocr_text[:80].strip())
    else:
        log("  OCR process_ocr()", False, "save_file returned no id")

    temp_path.unlink(missing_ok=True)

except Exception as e:
    traceback.print_exc()
    log("  Mistral OCR", False, e)


# ════════════════════════════════════════════════════════════════════════════
#  PART 3 — FRONTEND → BACKEND (via httpx, simulating Shiny frontend)
# ════════════════════════════════════════════════════════════════════════════
section("PART 3 — FRONTEND → BACKEND (API Client Simulation)")

BASE_URL = "http://127.0.0.1:8000"

# ── 3.1 Backend Health ──────────────────────────────────────────────────────
section("  3.1 Backend Health")
try:
    resp = httpx.get(f"{BASE_URL}/api/health/", timeout=10)
    log("  GET /api/health/", resp.status_code == 200, f"status={resp.status_code}")
    data = resp.json()
    log("  Response has status key", "status" in data)
    log("  Response has detail key", "detail" in data)
except Exception as e:
    log("  GET /api/health/", False, e)

# ── 3.2 Providers Endpoint ────────────────────────────────────────────────────
section("  3.2 Providers Endpoint")
try:
    resp = httpx.get(f"{BASE_URL}/api/providers/", timeout=10)
    log("  GET /api/providers/", resp.status_code == 200, f"status={resp.status_code}")
    data = resp.json()
    providers = data.get("providers", [])
    log("  Has providers list", len(providers) >= 1)
    for p in providers:
        log(f"    Provider: {p.get('name')}", True, f"model={p.get('model')}, embed={p.get('embed_model')}")
except Exception as e:
    log("  GET /api/providers/", False, e)

# ── 3.3 Document Upload (multipart, no JSON Content-Type) ───────────────────
section("  3.3 Document Upload (multipart/form-data)")
upload_doc_id = None
try:
    test_content = b"Hello World! This is a test document for SmartDocs.\n" * 20
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(test_content)
        temp_path = f.name

    with open(temp_path, "rb") as f:
        files = {"file": ("test_system_check.txt", f, "text/plain")}
        data = {"source": "local"}
        # NOTE: do NOT set Content-Type header here — httpx must set multipart boundary
        resp = httpx.post(
            f"{BASE_URL}/api/documents/upload/",
            files=files,
            data=data,
            timeout=30,
        )

    os.unlink(temp_path)
    log("  POST /api/documents/upload/", resp.status_code in [200, 201], f"status={resp.status_code}")
    log("  Response body valid JSON", True, resp.text[:80])
    result = resp.json()
    upload_doc_id = result.get("id")
    log("  Has 'id'", upload_doc_id is not None, upload_doc_id)
    log("  Has 'title'", "title" in result)
    log("  Has 'status' = uploaded", result.get("status") == "uploaded")
except Exception as e:
    traceback.print_exc()
    log("  POST /api/documents/upload/", False, e)

# ── 3.4 Document Indexing ────────────────────────────────────────────────────
section("  3.4 Document Indexing (FAISS pipeline)")
indexed_doc_id = None
if upload_doc_id:
    try:
        resp = httpx.post(f"{BASE_URL}/api/documents/{upload_doc_id}/index/", timeout=60)
        log(f"  POST /api/documents/{upload_doc_id}/index/", resp.status_code == 200, f"status={resp.status_code}")
        result = resp.json()
        log("  Has 'id'", "id" in result)
        log("  status = indexed", result.get("status") == "indexed")
        log("  chunks >= 1", result.get("chunks", 0) >= 1)
        log("  dimensions > 0", result.get("dimensions", 0) > 0)
        indexed_doc_id = upload_doc_id
    except Exception as e:
        log(f"  POST /api/documents/{{id}}/index/", False, e)
else:
    log("  POST /api/documents/{{id}}/index/", False, "Skipped — no doc ID from upload")

# ── 3.5 Conversation + Message ────────────────────────────────────────────────
section("  3.5 Conversation + Message (RAG pipeline)")
test_conv_id = None
if indexed_doc_id:
    try:
        # Create conversation
        resp = httpx.post(f"{BASE_URL}/api/conversations/", json={}, timeout=10)
        log("  POST /api/conversations/ (create)", resp.status_code == 201, f"status={resp.status_code}")
        result = resp.json()
        test_conv_id = result.get("conversation_id")
        log("  Has conversation_id", test_conv_id is not None)

        # Attach document
        resp = httpx.patch(
            f"{BASE_URL}/api/conversations/{test_conv_id}/documents/",
            json={"document_ids": [indexed_doc_id]},
            timeout=10,
        )
        log("  PATCH conversation documents", resp.status_code == 200, f"status={resp.status_code}")

        # Send message (RAG)
        resp = httpx.post(
            f"{BASE_URL}/api/conversations/{test_conv_id}/messages/",
            json={"content": "What is this document about?", "model": "qwen2.5:1.5b-instruct"},
            timeout=60,
        )
        log("  POST conversation message", resp.status_code == 200, f"status={resp.status_code}")
        result = resp.json()
        log("  Has 'assistant' response", "assistant" in result)
        log("  Response not empty", len(result.get("assistant", "")) > 0)
        log("  used_mock = False", result.get("used_mock") == False)
        metrics = result.get("metrics", {})
        log("  Metrics has provider", "provider" in metrics)
        log("  total_ms > 0", metrics.get("total_ms", 0) > 0, f"{metrics.get('total_ms')}ms")

    except Exception as e:
        traceback.print_exc()
        log("  Conversation pipeline", False, e)
else:
    log("  Conversation pipeline", False, "Skipped — no indexed doc")


# ════════════════════════════════════════════════════════════════════════════
#  PART 4 — FRONTEND-BACKEND CONNECTIVITY (Shiny session endpoint)
# ════════════════════════════════════════════════════════════════════════════
section("PART 4 — FRONTEND-BACKEND CONNECTIVITY (Shiny session)")

FE_URL = "http://127.0.0.1:8001"
try:
    resp = httpx.get(f"{FE_URL}/", timeout=10)
    log("  Frontend HTTP 200", resp.status_code == 200, f"status={resp.status_code}")
    log("  Frontend serves HTML", "html" in resp.text.lower()[:200] or len(resp.text) > 100)
except Exception as e:
    log("  Frontend HTTP 200", False, e)

try:
    resp = httpx.get(f"{FE_URL}/css/app.css", timeout=10)
    log("  Frontend /css/app.css", resp.status_code == 200, f"status={resp.status_code}")
except Exception as e:
    log("  Frontend /css/app.css", False, e)

# ════════════════════════════════════════════════════════════════════════════
#  PART 5 — FAISS VECTOR STORE (direct)
# ════════════════════════════════════════════════════════════════════════════
section("PART 5 — FAISS Vector Store (direct)")

try:
    locate = LocateService(metadata_dir=METADATA_DIR, logger=DEFAULT_LOGGER)
    faiss = locate.get_vector_store(EBackendStorageName.FAISS)
    log("  FAISS service created", faiss is not None)

    vectors = np.array([[1.0, 0.5, 0.2], [0.1, 1.0, 0.3], [0.2, 0.3, 1.0]], dtype=np.float32)
    test_id = "syscheck-001"

    index = faiss.create_index(vectors)
    log("  create_index()", True, f"shape={vectors.shape}")

    upsert = faiss.upsert(index, test_id)
    log("  upsert()", upsert.is_success, upsert.message)

    query = np.array([[0.9, 0.6, 0.3]], dtype=np.float32)
    search = faiss.search(index, test_id, query, limit=2)
    log("  search()", len(search.indices) >= 1, f"hits={len(search.indices)}, dist={search.distances}")
    log("  search distances", len(search.distances) >= 1)
    log("  search indices", len(search.indices) >= 1)

    deleted = faiss.delete(test_id)
    log("  delete()", deleted.is_success, deleted.message)

except Exception as e:
    traceback.print_exc()
    log("  FAISS operations", False, e)


# ════════════════════════════════════════════════════════════════════════════
#  SUMMARY
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("  SUMMARY")
print("=" * 70)
total = len(RESULTS)
passed = sum(1 for r in RESULTS if r["passed"])
failed = total - passed
print(f"  Total:  {total}")
print(f"  Passed: {passed}")
print(f"  Failed: {failed}")
print(f"  Rate:   {100*passed/max(total,1):.1f}%")
print("=" * 70)

if failed > 0:
    print("\n  FAILED TESTS:")
    for r in RESULTS:
        if not r["passed"]:
            print(f"  - {r['name']}: {r['detail']}")

print()
