from dataclasses import dataclass

@dataclass
class IJobManagerResponse:
    conversation_id: str
    documents_count: int
    status: str
    job_id: str