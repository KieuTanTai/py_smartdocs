from dataclasses import dataclass
from mistralai.client.types import (
    OptionalNullable,
    UNSET,
)

@dataclass
class IExtractResponse:
    """Data class for the response of the extract step in the upload pipeline."""
    document_id: str
    extracted_text: str
    model: str 
    page_processed: int
    doc_size_bytes: OptionalNullable[int] = UNSET
