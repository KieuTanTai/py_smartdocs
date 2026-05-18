from dataclasses import dataclass, field

@dataclass
class TimeExecuteAnalysis:
    provider: str
    model: str
    prompt_length: int
    response_length: int
    elapsed_ms: float
    success: bool
    error_message: str = field(default="")