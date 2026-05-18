from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class CompletionRequestInterface:
    provider: str
    model: str
    prompt: str
    context_hits: list[dict] = field(default_factory=list)


@dataclass
class CompletionResponseInterface:
    provider: str
    model: str
    content: str
    tokens_input: int = 0
    tokens_output: int = 0
    latency_ms: float = 0

@dataclass
class CompletionInfoInterface:
    provider: str
    model: str
    capabilities: list[str]

class LLMClient(Protocol):
    provider_name: str

    async def generate(self, request: CompletionRequestInterface) -> CompletionResponseInterface: ...
