"""
Test requests to all 3 LLM providers: Gemini, Mistral, and Ollama
"""

import asyncio

from backend.apps.interfaces.conversation.i_completion import (
    ICompletionRequest,
    ICompletionResponse,
)
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.read_config.read_ollama_config import OLLAMA_CONFIG

# Test prompt
TEST_PROMPT = "What is the capital of France? Answer in one sentence."

# Track results
results = {
    "gemini": ICompletionResponse,
    "mistral": ICompletionResponse,
    "ollama": ICompletionResponse,
}

errors = {
    "gemini": str,
    "mistral": str,
    "ollama": str,
}


async def test_gemini() -> int:
    """Test Gemini LLM"""
    print("\n" + "=" * 60)
    print("Testing Gemini LLM")
    print("=" * 60)
    try:
        client = LLMProviderFactory("gemini").get_provider()

        request = ICompletionRequest(
            provider="gemini",
            model=GEMINI_EMBEDDING_CONFIG["model"],
            prompt=TEST_PROMPT,
        )

        print(f"Model: {request.model}")
        print(f"Prompt: {request.prompt}")
        print("\nSending request...")

        response = await client.generate(request)

        print(f"\n✓ Response received successfully")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(
            f"Content: {response.content[:100]}..."
            if len(response.content) > 100
            else f"Content: {response.content}"
        )
        print(f"Latency: {response.latency_ms}ms")

        results["gemini"] = response  # type: ignore
        return 1
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"\n✗ {error_msg}")
        return 0


async def test_mistral() -> int:
    """Test Mistral LLM"""
    print("\n" + "=" * 60)
    print("Testing Mistral LLM")
    print("=" * 60)
    try:
        client = LLMProviderFactory("mistral").get_provider()

        request = ICompletionRequest(
            provider="mistral",
            model=MISTRAL_CONFIG["model"],
            prompt=TEST_PROMPT,
        )

        print(f"Model: {request.model}")
        print(f"Prompt: {request.prompt}")
        print("\nSending request...")

        response = await client.generate(request)

        print(f"\n✓ Response received successfully")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(
            f"Content: {response.content[:100]}..."
            if len(response.content) > 100
            else f"Content: {response.content}"
        )
        print(f"Latency: {response.latency_ms}ms")

        results["mistral"] = response  # type: ignore
        return 1

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"\n✗ {error_msg}")
        return 0


async def test_ollama() -> int:
    """Test Ollama LLM"""
    print("\n" + "=" * 60)
    print("Testing Ollama LLM")
    print("=" * 60)
    try:
        client = LLMProviderFactory("ollama").get_provider()

        request = ICompletionRequest(
            provider="ollama",
            model=OLLAMA_CONFIG["model"],
            prompt=TEST_PROMPT,
        )

        print(f"Model: {request.model}")
        print(f"Base URL: {OLLAMA_CONFIG['base_url']}")
        print(f"Prompt: {request.prompt}")
        print("\nSending request...")

        response = await client.generate(request)

        print(f"\n✓ Response received successfully")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
        print(
            f"Content: {response.content[:100]}..."
            if len(response.content) > 100
            else f"Content: {response.content}"
        )
        print(f"Latency: {response.latency_ms}ms")

        results["ollama"] = response  # type: ignore
        return 1
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"\n✗ {error_msg}")
        errors["ollama"] = error_msg  # type: ignore
        return 0


async def run_all_tests():
    """Run all LLM tests in parallel"""
    print("\n" + "=" * 60)
    print("LLM Backend Test Suite")
    print("=" * 60)
    print(f"Test Prompt: {TEST_PROMPT}")

    successful = 0
    failed = 0
    # Run all tests concurrently
    test_results = await asyncio.gather(
        test_gemini(),
        test_mistral(),
        test_ollama(),
    )

    successful = sum(1 for r in test_results if r == 1)
    failed = sum(1 for r in test_results if r == 0)

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    print(f"\nSuccessful: {successful}/3")
    print(f"Failed: {failed}/3")

    if successful > 0:
        print("\n✓ Successful Responses:")
        latencies = []
        for provider, response in results.items():
            if response is not None:
                print(f"  - {provider}: {response.latency_ms}ms")
                latencies.append(response.latency_ms)

        if latencies:
            print(f"\nLatency Statistics:")
            # Get providers with valid responses
            valid_providers = [p for p, r in results.items() if r is not None]

            # Find fastest and slowest
            fastest_provider = min(valid_providers, key=lambda p: results[p].latency_ms)
            slowest_provider = max(valid_providers, key=lambda p: results[p].latency_ms)

            print("fastest object:", results[fastest_provider].content)
            print("slowest object:", results[slowest_provider].content)
            print(
                f"  Fastest: {results[fastest_provider].latency_ms}ms ({results[fastest_provider].provider})"
            )
            print(
                f"  Slowest: {results[slowest_provider].latency_ms}ms ({results[slowest_provider].provider})"
            )
            print(f"  Average: {sum(latencies) / len(latencies):.0f}ms")

    if failed > 0:
        print("\n✗ Failed Responses:")
        for provider, error in errors.items():
            if error is not None:
                print(f"  - {provider}: {error}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
