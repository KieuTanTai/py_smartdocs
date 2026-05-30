"""
Test requests to all 3 LLM providers: Gemini, Mistral, and Ollama
"""

import asyncio
import datetime
from pathlib import Path
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.services.chat.i_completion import (
    ICompletionRequest,
    ICompletionResponse,
    IEmbeddingResponse,
)
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from sys_services.enums.e_provider_name import EProviderName
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.read_config.read_ollama_config import OLLAMA_CONFIG

# Test prompt
TEST_PROMPT = "What is the capital of France? Answer in one sentence."
FACTORY = LLMProviderFactory(config_provider=DEFAULT_CONFIG_PROVIDER, logger=DEFAULT_LOGGER)
CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"

# Track results
embed_results = {
    "gemini": None,
    "mistral": None,
    "ollama": None,
}

generate_results = {
    "gemini": "",
    "mistral": "",
    "ollama": "",
}

models = {
    "gemini": GEMINI_EMBEDDING_CONFIG["model"],
    "gemini_embedding": GEMINI_EMBEDDING_CONFIG["embedding_model"],
    "mistral": MISTRAL_CONFIG["model"],
    "mistral_embedding": MISTRAL_CONFIG["embedding_model"],
    "ollama": OLLAMA_CONFIG["model"],
    "ollama_embedding": OLLAMA_CONFIG["embedding_model"],
}

errors = {
    "gemini": "",
    "mistral": "",
    "ollama": "",
}

def test_gemini():
    try:
        gemini_client = FACTORY.get_provider(EProviderName.GEMINI)
        request = ICompletionRequest(provider=EProviderName.GEMINI, model=models["gemini"], prompt=TEST_PROMPT)
        embed_request = ICompletionRequest(provider=EProviderName.GEMINI, model=models["gemini_embedding"], prompt=TEST_PROMPT)
        generate_results["gemini"] = gemini_client.generate(request)
        embed_results["gemini"] = gemini_client.embedding(embed_request)

    except Exception as e:
        errors["gemini"] = str(e)

def test_mistral():
    try:
        mistral_client = FACTORY.get_provider(EProviderName.MISTRAL)
        request = ICompletionRequest(provider=EProviderName.MISTRAL, model=models["mistral"], prompt=TEST_PROMPT)
        embed_request = ICompletionRequest(provider=EProviderName.MISTRAL, model=models["mistral_embedding"], prompt=TEST_PROMPT)
        generate_results["mistral"] = mistral_client.generate(request)
        embed_results["mistral"] = mistral_client.embedding(embed_request)
    except Exception as e:
        errors["mistral"] = str(e)

def test_ollama():
    try:
        ollama_client = FACTORY.get_provider(EProviderName.OLLAMA)
        request = ICompletionRequest(provider=EProviderName.OLLAMA, model=models["ollama"], prompt=TEST_PROMPT)
        embed_request = ICompletionRequest(provider=EProviderName.OLLAMA, model=models["ollama_embedding"], prompt=TEST_PROMPT)
        generate_results["ollama"] = ollama_client.generate(request)
        embed_results["ollama"] = ollama_client.embedding(embed_request)
    except Exception as e:
        errors["ollama"] = str(e)

async def run_all_tests():
    await asyncio.gather(
        asyncio.to_thread(test_gemini),
        asyncio.to_thread(test_mistral),
        asyncio.to_thread(test_ollama),
    )

def save_results(name: str, result: str, embedding_result: str = "", error: str = ""):
    _separator = "─" * 80
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(OUTPUT_DIR / "llm_test_results.txt", "a") as f:
        # Write separator for readability
        f.write(f"{_separator}\n")

        # Write header with timestamp and type
        f.write(f"[{timestamp}] [{name}]\n")

        # Write message with proper indentation
        f.write(f"Result:\n  {result}\n")

        #write embedding result if provided
        if embedding_result:
            f.write(f"Embedding Result:\n  {embedding_result}\n")

        # Write error if provided
        if error:
            f.write(f"Error:\n  {error}\n")

        # Write end marker
        f.write(f"{_separator}\n")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
    for provider in generate_results.keys():
        save_results(
            name=provider.capitalize(),
            result=generate_results[provider],
            embedding_result=str(embed_results[provider]),
            error=errors[provider],
        )
