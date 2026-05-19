from dataclasses import dataclass, field


@dataclass
class ICompletionRequest:
    provider: str
    model: str
    prompt: str
    context_hits: list[dict] = field(default_factory=list)


@dataclass
class ICompletionResponse:
    provider: str
    model: str
    content: str
    latency_ms: float = 0


@dataclass
class ICompletionInfo:
    provider: str
    model: str
    capabilities: list[str]
