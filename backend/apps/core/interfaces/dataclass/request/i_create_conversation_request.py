
from dataclasses import dataclass, field
from pathlib import Path

from backend.apps.core.enums.e_provider_name import EProviderName


@dataclass
class ICreateConversationRequest: #using when upload files, this request will create a conversation for the files, and the conversation will be used to chat with the files
    provider: EProviderName
    model_name: str
    conversation_id: str
    document_urls: list[str] = field(default_factory=list) #* OPTIONAL (REQUIRED IF document_paths is empty), using when upload files, this is the list of file urls to be uploaded, and the files will be used to chat with the conversation
    document_paths: list[Path] = field(default_factory=list) #* OPTIONAL (REQUIRED IF document_urls is empty), using when upload files, this is the list of file paths to be uploaded, and the files will be used to chat with the conversation
    type: str = "normal" or "graph" #* the type of pipeline execute, for example: normal (base rag), graph (graph rag)
