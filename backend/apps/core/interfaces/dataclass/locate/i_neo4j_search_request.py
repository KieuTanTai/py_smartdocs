from dataclasses import dataclass

@dataclass
class INeo4jSearchRequest:
    query_text: str
    top_k: int
    # conversation_id: str
    # document_ids: list[str]