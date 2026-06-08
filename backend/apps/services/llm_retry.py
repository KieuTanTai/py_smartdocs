"""
LLM client wrapper with retry and circuit-breaker protection.
Automatically retries failed calls and falls back to alternate providers
when a provider is experiencing issues.
"""
from __future__ import annotations

import threading
import time
import traceback
from typing import Optional

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER


# ── Circuit breaker state (per provider) ─────────────────────────────────────

class _CircuitBreaker:
    """
    Simple per-provider circuit breaker.
    After MAX_FAILURES consecutive failures on a provider, that provider is
    marked "open" (bypassed) for COOLDOWN_SECONDS before it is retried again.
    """

    MAX_FAILURES = 3
    COOLDOWN_SECONDS = 30

    def __init__(self) -> None:
        self._failures: dict[str, int] = {}
        self._last_failure: dict[str, float] = {}
        self._lock = threading.Lock()

    def record_failure(self, provider: str) -> None:
        with self._lock:
            self._failures[provider] = self._failures.get(provider, 0) + 1
            self._last_failure[provider] = time.time()
            DEFAULT_LOGGER.warning(
                f"Circuit breaker: provider={provider} "
                f"has {self._failures[provider]} consecutive failures.",
                source="_CircuitBreaker",
            )

    def record_success(self, provider: str) -> None:
        with self._lock:
            self._failures[provider] = 0

    def is_open(self, provider: str) -> bool:
        with self._lock:
            failures = self._failures.get(provider, 0)
            if failures < self.MAX_FAILURES:
                return False
            # Check cooldown
            last = self._last_failure.get(provider, 0)
            if time.time() - last >= self.COOLDOWN_SECONDS:
                # Cooldown elapsed; allow one probe
                self._failures[provider] = 0
                return False
            return True

    def available_providers(self, preferred: str) -> list[str]:
        """Return provider list: preferred first, then others (excluding open ones)."""
        all_providers = [p.value for p in EProviderName]
        ordered = [preferred] + [p for p in all_providers if p != preferred]
        return [p for p in ordered if not self.is_open(p)]


_circuit_breaker = _CircuitBreaker()


# ── Retry + CircuitBreaker wrapper ────────────────────────────────────────────

def call_llm_with_resilience(
    provider_name: str,
    model_name: str,
    prompt: str,
    max_retries: int = 2,
) -> tuple[str, str]:
    """
    Call LLM with:
      - Automatic retry (up to max_retries) on transient errors
      - Circuit breaker to skip providers that are failing repeatedly
      - Automatic fallback to alternate providers

    Returns:
        (answer_text, actual_provider_used)

    Raises:
        RuntimeError: if ALL providers fail after retries
    """
    factory = LLMProviderFactory(DEFAULT_CONFIG_PROVIDER, DEFAULT_LOGGER)
    providers_to_try = _circuit_breaker.available_providers(provider_name)
    last_error: str = ""

    for attempt_provider in providers_to_try:
        if attempt_provider == provider_name and provider_name not in providers_to_try:
            attempt_provider = provider_name  # Fallback from preferred

        try:
            llm_client = factory.get_provider(EProviderName(attempt_provider))
            req = ICompletionRequest(
                provider=EProviderName(attempt_provider),
                model=model_name,
                prompt=prompt,
            )
            answer = llm_client.generate(req)
            _circuit_breaker.record_success(attempt_provider)
            return answer, attempt_provider

        except Exception as exc:
            DEFAULT_LOGGER.error(
                f"LLM call failed for provider={attempt_provider}: {exc}",
                source="call_llm_with_resilience",
            )
            _circuit_breaker.record_failure(attempt_provider)
            last_error = str(exc)
            continue

    raise RuntimeError(
        f"All LLM providers failed after retries. Last error: {last_error}"
    )
