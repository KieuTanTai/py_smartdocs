
from dataclasses import dataclass, field
from pathlib import Path
import uuid

from faiss import Embedding

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName


@dataclass
class ICreateConversationRequest: #using when upload files, this request will create a conversation for the files, and the conversation will be used to chat with the files
    provider: EProviderName
    model_name: str
    document_urls: list[str] = field(default_factory=list) #* OPTIONAL (REQUIRED IF document_paths is empty), using when upload files, this is the list of file urls to be uploaded, and the files will be used to chat with the conversation
    document_paths: list[Path] = field(default_factory=list) #* OPTIONAL (REQUIRED IF document_urls is empty), using when upload files, this is the list of file paths to be uploaded, and the files will be used to chat with the conversation
    type: EPipelineType = field(default=EPipelineType.BASE)
    conversation_id: uuid.UUID | None = field(default=None)
    file_name: str = field(default="")
    embedding_model_name: str = 'gemini-3.1-flash-lite'
    
@dataclass
class IGetConversationRequest:
    conversation_id: uuid.UUID | None = field(default=None)
    
@dataclass
class IGetMessageByConversationRequest:
    conversation_id: uuid.UUID | None = field(default=None)
    
@dataclass 
class ISendMessageRequest:
    user_input: str
    provider_name: EProviderName
    model_name: str
    pipeline_type: EPipelineType = field(default= EPipelineType.BASE)
    conversation_id: uuid.UUID | None = field(default=None)
