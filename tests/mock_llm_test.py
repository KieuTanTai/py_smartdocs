"""
LLM Testing Guide & Mock Test
==============================
File test cho LLM providers: Gemini, Mistral, Ollama.
Bao gom mock mode (khong can API key) va real mode (can API key).

Cach chay:

1. TEST VOI MOCK (khong can API key):
   python -m tests.mock_llm_test --mode mock

2. TEST VOI LLM THAT (can API key trong .env):
   python -m tests.mock_llm_test --mode real
   python -m tests.mock_llm_test --mode real --provider gemini
   python -m tests.mock_llm_test --mode real --provider mistral
   python -m tests.mock_llm_test --mode real --provider ollama

3. TEST QUA BACKEND API (can chay backend server truoc):
   python -m tests.mock_llm_test --mode api
   python -m tests.mock_llm_test --mode api --url http://localhost:8000
"""

import os
import sys
import io
import time
import json
import asyncio
import argparse
import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Fix Windows console encoding for emoji/Unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")
import django
django.setup()

from backend.apps.core.interfaces.core.i_dataclass_transaction import (
    ICompletionRequest,
    ICompletionResponse,
    IEmbeddingResponse,
)
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from sys_services.enums.e_provider_name import EProviderName
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.api_client import ApiClient, ApiError

# Constants
CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BACKEND_URL = os.getenv("SMARTDOCS_API_BASE_URL", "http://localhost:8000")

# Test Data
SAMPLE_CONTEXT = [
    "Bao cao tai chinh nam 2024 - Cong ty ABC. "
    "Tong doanh thu: 150 ty VND (tang 15 phan tram so voi 2023). "
    "Chi phi hoat dong: 95 ty VND. "
    "Loi nhuan rong: 55 ty VND. "
    "Ty suat loi nhuan: 36.7 phan tram.",

    "Chien luoc phat trien 2025: "
    "Mo rong thi truong Dong Nam A. "
    "Dau tu R&D 20 ty VND. "
    "Tuyen dung 200 nhan su moi. "
    "Ra mat 3 san pham moi.",
]

TEST_QUESTIONS = [
    "Tong doanh thu nam 2024 la bao nhieu?",
    "Loi nhuan rong la bao nhieu?",
    "Chien luoc phat trien nam 2025 gom nhung gi?",
    "Cong ty du dinh dau tu bao nhieu cho R&D?",
]

SYSTEM_PROMPT = "Ban la tro ly AI chuyen phan tich tai lieu. Tra loi ngan gon, chinh xac dua tren context."


# Result Tracking
@dataclass
class LLMTestResult:
    provider: str
    model: str
    question: str
    answer: str = ""
    latency_ms: int = 0
    passed: bool = False
    error: str = ""
    mode: str = "mock"


all_results: list[LLMTestResult] = []
SEP = "=" * 70
SUB_SEP = "-" * 50


def build_rag_prompt(question: str, context_chunks: list[str], system_prompt: str = SYSTEM_PROMPT) -> str:
    """Xay dung prompt RAG giong cach backend lam trong gateway.py MessageListView."""
    context_text = "\n".join(context_chunks)
    prompt = (
        f"System prompt: {system_prompt}\n\n"
        f"Context from documents:\n{context_text}\n\n"
        f"User: {question}\n\nAssistant:"
    )
    return prompt


# =====================================================================
# MODE 1: MOCK TEST - Khong can API key
# =====================================================================
def mock_llm_response(question: str, context: list[str]) -> str:
    """Tao mock response dua tren keyword matching (giong logic gateway.py)."""
    combined = " ".join(context).lower()
    question_lower = question.lower()

    if "doanh thu" in question_lower:
        return "[MOCK] Tong doanh thu nam 2024 la 150 ty VND, tang 15% so voi nam 2023."
    elif "loi nhuan" in question_lower:
        return "[MOCK] Loi nhuan rong la 55 ty VND, ty suat loi nhuan dat 36.7%."
    elif "chien luoc" in question_lower or "phat trien" in question_lower:
        return ("[MOCK] Chien luoc phat trien 2025 gom: Mo rong thi truong Dong Nam A, "
                "Dau tu R&D 20 ty VND, Tuyen dung 200 nhan su moi, Ra mat 3 san pham moi.")
    elif "r&d" in question_lower or "dau tu" in question_lower:
        return "[MOCK] Cong ty du dinh dau tu 20 ty VND cho R&D trong nam 2025."
    else:
        return f"[MOCK] Day la mock response cho cau hoi: {question}"


def run_mock_tests():
    """Chay test voi mock responses - khong can API key."""
    print(f"\n{SEP}")
    print("  MODE: MOCK - Test luong xu ly, khong can API key")
    print(f"{SEP}\n")

    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"  [{i}/{len(TEST_QUESTIONS)}] Q: {question}")

        # Build prompt (test prompt building logic)
        prompt = build_rag_prompt(question, SAMPLE_CONTEXT)
        print(f"  Prompt length: {len(prompt)} chars")

        # Mock response
        start = time.time()
        answer = mock_llm_response(question, SAMPLE_CONTEXT)
        latency = int((time.time() - start) * 1000)

        print(f"  A: {answer}")
        print(f"  Latency: {latency}ms")
        print(f"  {SUB_SEP}")

        all_results.append(LLMTestResult(
            provider="mock",
            model="mock-v1",
            question=question,
            answer=answer,
            latency_ms=latency,
            passed=len(answer) > 0,
            mode="mock",
        ))


# =====================================================================
# MODE 2: REAL TEST - Goi LLM that
# =====================================================================
PROVIDER_MODELS = {
    "gemini": {
        "enum": EProviderName.GEMINI,
        "model_env": "GEMINI_MODEL",
        "model_default": "gemini-2.5-flash",
        "embedding_model_env": "GEMINI_EMBEDDING_MODEL",
        "embedding_default": "gemini-embedding-2",
    },
    "mistral": {
        "enum": EProviderName.MISTRAL,
        "model_env": "MISTRAL_MODEL",
        "model_default": "mistral-large-latest",
        "embedding_model_env": "MISTRAL_EMBEDDING_MODEL",
        "embedding_default": "mistral-embed",
    },
    "ollama": {
        "enum": EProviderName.OLLAMA,
        "model_env": "OLLAMA_MODEL",
        "model_default": "qwen2.5:1.5b-instruct",
        "embedding_model_env": "OLLAMA_EMBEDDING_MODEL",
        "embedding_default": "qwen3-embedding",
    },
}


def test_real_provider(provider_name: str):
    """Test 1 provider that: generate + embedding."""
    config = PROVIDER_MODELS.get(provider_name)
    if not config:
        print(f"  Unknown provider: {provider_name}")
        return

    model = os.getenv(config["model_env"], config["model_default"])
    embed_model = os.getenv(config["embedding_model_env"], config["embedding_default"])

    print(f"\n  --- Provider: {provider_name.upper()} ---")
    print(f"  Generate model: {model}")
    print(f"  Embedding model: {embed_model}")

    factory = LLMProviderFactory(config_provider=DEFAULT_CONFIG_PROVIDER, logger=DEFAULT_LOGGER)

    # Test Generate
    print(f"\n  [Generate Test]")
    for i, question in enumerate(TEST_QUESTIONS[:2], 1):
        prompt = build_rag_prompt(question, SAMPLE_CONTEXT)
        print(f"    [{i}] Q: {question}")

        try:
            client = factory.get_provider(config["enum"])
            request = ICompletionRequest(
                provider=config["enum"],
                model=model,
                prompt=prompt,
            )
            start = time.time()
            answer = client.generate(request)
            latency = int((time.time() - start) * 1000)

            print(f"    A: {answer[:200]}...")
            print(f"    Latency: {latency}ms")

            all_results.append(LLMTestResult(
                provider=provider_name,
                model=model,
                question=question,
                answer=answer,
                latency_ms=latency,
                passed=len(answer) > 0,
                mode="real",
            ))
        except Exception as e:
            print(f"    ERROR: {e}")
            all_results.append(LLMTestResult(
                provider=provider_name,
                model=model,
                question=question,
                error=str(e),
                passed=False,
                mode="real",
            ))

    # Test Embedding
    print(f"\n  [Embedding Test]")
    try:
        client = factory.get_provider(config["enum"])
        embed_request = ICompletionRequest(
            provider=config["enum"],
            model=embed_model,
            prompt=SAMPLE_CONTEXT[0],
        )
        start = time.time()
        embed_result = client.embedding(embed_request)
        latency = int((time.time() - start) * 1000)

        print(f"    Embedding dimensions: {embed_result.dimensions}")
        print(f"    Embedding shape: {embed_result.shape}")
        print(f"    First 5 values: {embed_result.embedding[:5]}")
        print(f"    Latency: {latency}ms")

        all_results.append(LLMTestResult(
            provider=provider_name,
            model=embed_model,
            question="[Embedding Test]",
            answer=f"dims={embed_result.dimensions}, shape={embed_result.shape}",
            latency_ms=latency,
            passed=embed_result.dimensions > 0,
            mode="real",
        ))
    except Exception as e:
        print(f"    Embedding ERROR: {e}")
        all_results.append(LLMTestResult(
            provider=provider_name,
            model=embed_model,
            question="[Embedding Test]",
            error=str(e),
            passed=False,
            mode="real",
        ))


def run_real_tests(provider: Optional[str] = None):
    """Chay test voi LLM that."""
    print(f"\n{SEP}")
    print("  MODE: REAL - Goi LLM provider that")
    print(f"{SEP}")

    providers = [provider] if provider else ["gemini", "mistral", "ollama"]
    for p in providers:
        test_real_provider(p)


# =====================================================================
# MODE 3: API TEST - Qua Backend REST API
# =====================================================================
def run_api_tests(backend_url: str):
    """Test LLM qua Backend API (end-to-end)."""
    print(f"\n{SEP}")
    print(f"  MODE: API - Test qua Backend ({backend_url})")
    print(f"{SEP}\n")

    api = ApiClient(base_url=backend_url, timeout=60.0)

    # 1. Health check
    print("  [1] Health check...")
    try:
        resp = api.health()
        print(f"  Backend status: {resp.get('status')}")
    except Exception as e:
        print(f"  Backend KHONG KHA DUNG: {e}")
        print("  Hay chay: python manage.py runserver 8000")
        return

    # 2. Upload test document
    print("\n  [2] Upload test document...")
    test_file = OUTPUT_DIR / "api_test_doc.txt"
    test_file.write_text("\n".join(SAMPLE_CONTEXT), encoding="utf-8")

    try:
        file_info = {
            "name": "api_test_doc.txt",
            "datapath": str(test_file),
            "type": "text/plain",
        }
        upload_resp = api.upload_document(file_info, source="local")
        doc_id = upload_resp.get("id") or upload_resp.get("document_id")
        print(f"  Document uploaded: {doc_id}")

        # Index document
        index_resp = api.index_document(doc_id)
        print(f"  Document indexed: {index_resp.get('status')}")
    except Exception as e:
        print(f"  Upload/Index error: {e}")
        doc_id = None

    # 3. Create conversation and send messages
    print("\n  [3] Create conversation...")
    doc_ids = [doc_id] if doc_id else []
    try:
        conv_resp = api.create_conversation(
            title="LLM API Test",
            provider="auto",
            model="auto",
            system_prompt=SYSTEM_PROMPT,
            document_ids=doc_ids,
            mode="normal",
        )
        conv_id = conv_resp.get("conversation_id") or conv_resp.get("id")
        print(f"  Conversation created: {conv_id}")
    except Exception as e:
        print(f"  Create conversation error: {e}")
        return

    # 4. Send test messages
    print(f"\n  [4] Sending {len(TEST_QUESTIONS)} test messages...")
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n  --- Message {i}/{len(TEST_QUESTIONS)} ---")
        print(f"  Q: {question}")

        try:
            start = time.time()
            resp = api.send_message(conv_id, question)
            latency = int((time.time() - start) * 1000)

            answer = resp.get("assistant") or resp.get("content") or resp.get("message") or ""
            used_mock = resp.get("used_mock", False)
            metrics = resp.get("metrics", {})

            print(f"  A: {answer[:200]}...")
            print(f"  Provider: {metrics.get('provider', 'unknown')}")
            print(f"  Model: {metrics.get('model', 'unknown')}")
            print(f"  Latency: {latency}ms")
            if used_mock:
                print("  WARNING: Used mock response (LLM not available)")

            all_results.append(LLMTestResult(
                provider=metrics.get("provider", "api"),
                model=metrics.get("model", "auto"),
                question=question,
                answer=answer,
                latency_ms=latency,
                passed=len(answer) > 0,
                mode="api",
            ))
        except Exception as e:
            print(f"  ERROR: {e}")
            all_results.append(LLMTestResult(
                provider="api",
                model="auto",
                question=question,
                error=str(e),
                passed=False,
                mode="api",
            ))

        time.sleep(0.5)


# =====================================================================
# Report
# =====================================================================
def print_report():
    print(f"\n\n{SEP}")
    print("  BAO CAO KET QUA TEST LLM")
    print(f"{SEP}")

    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)
    total = len(all_results)

    for r in all_results:
        status = "PASSED" if r.passed else "FAILED"
        error_info = f" | Error: {r.error}" if r.error else ""
        print(f"  [{status}] [{r.mode}] {r.provider}/{r.model} | {r.question[:40]}... | {r.latency_ms}ms{error_info}")

    print(f"\n{SUB_SEP}")
    print(f"  Total: {total} | Passed: {passed} | Failed: {failed}")
    if failed == 0 and total > 0:
        print("  TAT CA TEST DEU PASSED!")
    elif failed > 0:
        print(f"  Co {failed} test FAILED - kiem tra lai config/API key.")
    print(f"{SUB_SEP}\n")

    # Save report
    report_file = OUTPUT_DIR / "llm_test_results.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"LLM Test Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'=' * 60}\n\n")
        for r in all_results:
            status = "PASSED" if r.passed else "FAILED"
            f.write(f"[{status}] [{r.mode}] {r.provider}/{r.model}\n")
            f.write(f"  Question: {r.question}\n")
            if r.answer:
                f.write(f"  Answer: {r.answer[:300]}\n")
            if r.error:
                f.write(f"  Error: {r.error}\n")
            f.write(f"  Latency: {r.latency_ms}ms\n\n")
        f.write(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}\n")
    print(f"  Report saved to: {report_file}")


# =====================================================================
# Main
# =====================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LLM Test - Mock / Real / API")
    parser.add_argument(
        "--mode",
        default="mock",
        choices=["mock", "real", "api"],
        help="Test mode: mock (no API key), real (direct LLM), api (via backend)",
    )
    parser.add_argument(
        "--provider",
        default=None,
        choices=["gemini", "mistral", "ollama"],
        help="Specific provider to test (real mode only)",
    )
    parser.add_argument(
        "--url",
        default=BACKEND_URL,
        help=f"Backend URL for api mode (default: {BACKEND_URL})",
    )
    args = parser.parse_args()

    print(f"\nBat dau LLM Test")
    print(f"  Mode: {args.mode}")
    print(f"  Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if args.mode == "mock":
        run_mock_tests()
    elif args.mode == "real":
        run_real_tests(args.provider)
    elif args.mode == "api":
        run_api_tests(args.url)

    print_report()
