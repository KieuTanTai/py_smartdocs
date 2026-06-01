from dataclasses import dataclass, field

import numpy as np

from sys_services.enums.e_provider_name import EProviderName


@dataclass
class ICompletionRequest:
    provider: EProviderName
    model: str
    prompt: str
    context_hits: list[dict] = field(default_factory=list)


@dataclass
class IEmbeddingResponse:
    embedding: np.ndarray
    shape: tuple
    dimensions: int

@dataclass
class ICompletionResponse:
    provider: EProviderName
    model: str
    content: str
    latency_ms: float = 0


@dataclass
class ICompletionInfo:
    provider: EProviderName
    model: str
    capabilities: list[str]
