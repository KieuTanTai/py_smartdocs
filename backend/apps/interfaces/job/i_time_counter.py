from dataclasses import dataclass

@dataclass
class ITimeExecuteFileCounter:
    file_id: str
    extracted_time_ms: float
    ocr_time_ms: float
    normalization_time_ms: float
    chunking_time_ms: float
    embedding_time_ms: float
    confidentse_scores_time_ms: dict | None
    storage_time_ms: float
    total_time_ms: float

# prototype: this is a prototype interface for counting time of each step in the conversation flow, it can be extended to include more steps or more granular time measurements as needed
@dataclass
class ITimeConversationCounter:
    conversation_id: str
    llm_time_ms: float
    retrieval_time_ms: float
    other_time_ms: float
    total_time_ms: float