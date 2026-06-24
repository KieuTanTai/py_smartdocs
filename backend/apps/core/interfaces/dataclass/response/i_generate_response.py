from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

@dataclass
class IGenerateResponseMetadata:
    done: Optional[bool] = None
    'True if response is complete, otherwise False. Useful for streaming to detect the final response.'

    done_reason: Optional[str] = None
    'Reason for completion. Only present when done is True.'

    total_duration: Optional[int] = None
    'Total duration in nanoseconds.'

    load_duration: Optional[int] = None
    'Load duration in nanoseconds.'

    prompt_tokens: Optional[int] = None
    'Number of tokens evaluated in the prompt.'

    prompt_eval_duration: Optional[int] = None
    'Duration of evaluating the prompt in nanoseconds.'

    completion_tokens: Optional[int] = None
    'Number of tokens evaluated in inference.'

    total_tokens: Optional[int] = None
    'Total number of tokens evaluated (prompt + completion).'

@dataclass
class IGenerateResponse:
    content: str
    model_name: str
    metadata: Optional[IGenerateResponseMetadata] = None
    created_at: Optional[str] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
