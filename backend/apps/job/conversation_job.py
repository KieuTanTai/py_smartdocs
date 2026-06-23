from pathlib import Path
from typing import Any, cast
import uuid

# Import Interfaces
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.cache.i_cache_param_value import ICacheParam
from backend.apps.core.interfaces.dataclass.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.dataclass.response.i_conversation_job_response import IConversationJobResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IConversationRelationshipResponse, IconversationDocumentGetResponse
from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse
from backend.apps.core.interfaces.dataclass.response.i_vector_db_response import IVectorDBLoadResponse
from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from backend.apps.core.interfaces.llm.i_llm_provider_factory import ILLMProviderFactory
from backend.apps.core.interfaces.services.cache.i_cache_service import ICacheService
from backend.apps.core.interfaces.services.cache.i_memory_pool import IMemoryPool
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_cache_database import IConversationCacheDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_database import IConversationDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_file_database import IConversationFileDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import IDatabaseProvider
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import IDocumentDatabase
from backend.apps.core.interfaces.services.rag_base.database.i_message_database import IMessageDatabase
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.services.rag_base.search.i_hybrid_search_service import IHybridSearchService
from backend.apps.interfaces.job.i_conversation_job import IConversationJob
from backend.apps.services.chat.models import ConversationCacheModel, ConversationFilesModel, ConversationModel, DocumentModel, MessageModel
from backend.apps.utils.get_instance_model_database import get_instance_model_database

class ConversationJob(IConversationJob):

    def __init__(self, llm_provider_factory: ILLMProviderFactory, 
                 llm_prompt_structure: ILLMPromptStructure, config_provider: IConfigProvider, 
                 database_provider: IDatabaseProvider,
                 locate_service: ILocateService,
                 cache_session: IConnectCacheSession,
                 memory_pool: IMemoryPool,
                 logger: ILogger, hybrid_search_service: IHybridSearchService | None = None):
        self.llm_provider_factory = llm_provider_factory
        self.llm_prompt_structure = llm_prompt_structure
        self.config_provider = config_provider
        self.database_provider = database_provider
        self.logger = logger
        self.cache_session = cache_session
        self.hybrid_search_service = hybrid_search_service
        self.locate_service = locate_service
        self.memory_pool = memory_pool
        self.document_database: IDocumentDatabase = cast(IDocumentDatabase, self.database_provider.get_model_service(DocumentModel))
        self.conversation_files_database: IConversationFileDatabase = cast(IConversationFileDatabase, self.database_provider.get_model_service(ConversationFilesModel))
        self.message_database: IMessageDatabase = cast(IMessageDatabase, self.database_provider.get_model_service(MessageModel))
        self.conversation_database: IConversationDatabase = cast(IConversationDatabase, self.database_provider.get_model_service(ConversationModel))
        self.conversation_cache_database: IConversationCacheDatabase = cast(IConversationCacheDatabase, self.database_provider.get_model_service(ConversationModel))

    def check_documents_ready(self, conversation_key:uuid.UUID, file_caller: str = "") -> bool:
        try:
            existed = self.document_database.get_by_id(conversation_key)
            self.logger.info(
                f"Checked document readiness for conversation {conversation_key}: {'Ready' if existed and existed.documents_status.lower().strip() == 'indexed' else 'Not Ready'}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.check_documents_ready.__name__,
            )
            if not existed or not existed.documents_status.lower().strip() == "indexed":
                return False
            return True
        except Exception as e:
            self.logger.error(
                f"Error checking document readiness for conversation {conversation_key}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.check_documents_ready.__name__,
            )
            return False

    def create_init_conversation(self, conversation_title: str = "Initial Conversation", file_caller: str = "") -> ConversationModel:
        try:
            conversation = self.conversation_database.create_conversation(conversation_title=conversation_title)
            self.logger.info(
                f"Created initial conversation with ID {conversation.conversations_id}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.create_init_conversation.__name__,
            )
            return conversation

        except Exception as e:
            self.logger.error(
                f"Error creating initial conversation: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.create_init_conversation.__name__,
            )
            raise ValueError("Failed to create initial conversation")

    def check_existed_conversation(self, conversation_id: uuid.UUID, file_caller: str = "") -> ConversationModel | None:
        try:
            existed = self.conversation_database.get_by_id(conversation_id)
            self.logger.info(
                f"Checked existence of conversation {conversation_id}: {'Exists' if existed else 'Does Not Exist'}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.check_existed_conversation.__name__,
            )
            return existed
        except Exception as e:
            self.logger.error(
                f"Error checking existence of conversation {conversation_id}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.check_existed_conversation.__name__,
            )
            return None

    def generate_bootstrap_message(self, conversation: ConversationModel, provider: EProviderName, model_name: str, summarize: str = "", file_caller: str = "") -> IConversationJobResponse:
        files = self.__get_conversation_files(conversation)
        if not files:
            self.logger.warning(
                f"No files found for conversation {conversation.conversations_id} when generating bootstrap message.",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.generate_bootstrap_message.__name__,
            )
            raise FileNotFoundError(f"No files found for conversation {conversation.conversations_id } when generating bootstrap message.")
        assistant_response = None
        if summarize.strip() == "":
            summarize = self.llm_prompt_structure.build_init_processed_prompt("say hi to user")
            assistant_response = self.__generate_assistant_response(summarize, provider, model_name)
        self.logger.info(
            f"Generated bootstrap message for conversation {conversation.conversations_id} with provider {provider} and model {model_name}.\n now save the message to database.",
            source=Path(__file__).name,
            call_by=file_caller,
            method_call=self.generate_bootstrap_message.__name__,
        )
        return IConversationJobResponse(
            conversation_id=str(conversation.conversations_id),
            status=True,
            message_model=self.__save_message(conversation, False, assistant_response.content if assistant_response else summarize),
            generate_response=assistant_response
        )

    #! NOTE: DONT USE THIS NOW
    def remove_conversation(self, conversation_id: str, file_caller: str = "") -> int:
        try:
            removed_count = self.conversation_database.delete(conversation_id)
            self.logger.info(
                f"Removed conversation {conversation_id}. Removed records count: {removed_count}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.remove_conversation.__name__,
            )
            return removed_count
        except Exception as e:
            self.logger.error(
                f"Error removing conversation {conversation_id}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.remove_conversation.__name__,
            )
        return 0

    def change_title_document(self, conversation_id: str, new_title: str, file_caller: str = "") -> ConversationModel:
        try:
            updated_count = self.conversation_database.update_title(conversation_id, new_title)
            self.logger.info(
                f"Renamed conversation {conversation_id} to '{new_title}'. Updated records count: {updated_count}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.change_title_document.__name__,
            )
            return updated_count
        except Exception as e:
            self.logger.error(
                f"Error renaming conversation {conversation_id} to '{new_title}': {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.change_title_document.__name__,
            )
            raise ValueError(f"Failed to rename conversation {conversation_id} to '{new_title}'")

    def get_all_conversations(self, user_id: str = "", file_caller: str = "") -> list[ConversationModel]:
        try:
            conversations = self.conversation_database.get_all()
            self.logger.info(
                f"Retrieved {len(conversations)} conversations for user_id: {user_id}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.get_all_conversations.__name__,
            )
            return [conversation for conversation in conversations if conversation.conversations_id is not None]
        except Exception as e:
            self.logger.error(
                f"Error retrieving conversations for user_id: {user_id}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.get_all_conversations.__name__,
            )
            return []

    def check_conversation_is_valid(self, conversation: ConversationModel, file_caller: str = "") -> IConversationRelationshipResponse:
        try:
            if conversation is None:
                self.logger.warning(
                    f"Conversation {conversation_id} not found when checking validity.",
                    source=Path(__file__).name,
                    call_by=file_caller,
                    method_call=self.check_conversation_is_valid.__name__,
                )
                raise ValueError(f"Conversation {conversation_id} not found.")
            conversation_id = conversation.conversations_id

            cache = self.conversation_cache_database.get_by_conversation(conversation)
            document = self.document_database.get_by_conversation(conversation)
            files = self.__get_conversation_files(conversation) if conversation else []

            is_valid = cache is not None and document is not None and len(files) > 0
            self.logger.info(
                f"Checked validity of conversation {conversation_id}: {'Valid' if is_valid else 'Invalid'}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.check_conversation_is_valid.__name__,
            )
            if is_valid:
                return IConversationRelationshipResponse(
                    conversation,
                    cache=cache,
                    faiss_document=document,
                    conversation_files=files
                )
            else:
                self.logger.warning(
                    f"Conversation {conversation_id} is not valid. Cache: {'Exists' if cache else 'Missing'}, Document: {'Exists' if document else 'Missing'}, Files: {len(files)} found.",
                    source=Path(__file__).name,
                    call_by=file_caller,
                    method_call=self.check_conversation_is_valid.__name__,
                )
                raise ValueError(f"Conversation {conversation_id} is not valid. Cache: {'Exists' if cache else 'Missing'}, Document: {'Exists' if document else 'Missing'}, Files: {len(files)} found.")
        except Exception as e:
            self.logger.error(
                f"Error checking validity of conversation {conversation.conversations_id}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.check_conversation_is_valid.__name__,
            )
            raise ValueError(f"Conversation {conversation.conversations_id} is not valid.")

    def load_cache(self, conversation: ConversationModel, file_caller: str = "") -> ICacheParam | None:
        try:
            if not conversation:
                self.logger.warning(
                    f"Cannot load cache for conversation {conversation.conversations_id if conversation else 'Unknown'}: Missing conversation or cache.",
                    source=Path(__file__).name,
                    call_by=file_caller,
                    method_call=self.load_cache.__name__,
                )
                return None

            self.logger.info(
                f"Loading cache for conversation {conversation.conversations_id}.",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.load_cache.__name__,
            )
            
            service = cast(ICacheService, self.cache_session.connect(file_caller))
            service.clear(file_caller)
            cache_param = service.load_from_file(conversation.conversations_id, file_caller)
            if not cache_param:
                self.logger.warning(
                    f"Failed to load cache for conversation {conversation.conversations_id}. Cache file may be missing or corrupted.",
                    source=Path(__file__).name,
                    call_by=file_caller,
                    method_call=self.load_cache.__name__,
                )
                return None
            self.logger.info(
                f"Successfully loaded cache for conversation {conversation.conversations_id}.",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.load_cache.__name__,
            )
            return cache_param
        except Exception as e:
            self.logger.error(
                f"Error loading cache for conversation {conversation.conversations_id if conversation else 'Unknown'}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.load_cache.__name__,
            )
            return None

    def load_faiss_index(self, conversation: ConversationModel, file_caller: str = "") -> IVectorDBLoadResponse | None:
        try:
            if not conversation:
                self.logger.warning(
                    f"Cannot load FAISS index for conversation {conversation.conversations_id if conversation else 'Unknown'}: Missing conversation or FAISS document.",
                    source=Path(__file__).name,
                    call_by=file_caller,
                    method_call=self.load_faiss_index.__name__,
                )
                return None

            self.logger.info(
                f"Loading FAISS index for conversation {conversation.conversations_id}.",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.load_faiss_index.__name__,
            )

            service = cast(IVectorStoreService, self.locate_service.get_vector_store(EBackendStorageName.FAISS))
            response = service.load(conversation.conversations_id)

            if response.index and response.is_success:
                self.logger.info(
                    f"Successfully loaded FAISS index for conversation {conversation.conversations_id}.",
                    source=Path(__file__).name,
                    call_by=file_caller,
                    method_call=self.load_faiss_index.__name__,
                )
                self.memory_pool.add_to_pool(conversation.conversations_id, response.index, file_caller)
            else:
                self.logger.warning(
                    f"Failed to load FAISS index for conversation {conversation.conversations_id}.",
                    source=Path(__file__).name,
                    call_by=file_caller,
                    method_call=self.load_faiss_index.__name__,
                )
            return response
        except Exception as e:
            self.logger.error(
                f"Error loading FAISS index for conversation {conversation.conversations_id if conversation else 'Unknown'}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.load_faiss_index.__name__,
            )
            return None
        
    def load_messages(self, conversation: ConversationModel, file_caller: str = "") -> list[MessageModel]:
        try:
            if not conversation:
                self.logger.warning(
                    f"Cannot load messages for conversation {conversation.conversations_id if conversation else 'Unknown'}: Missing conversation.",
                    source=Path(__file__).name,
                    call_by=file_caller,
                    method_call=self.load_messages.__name__,
                )
                return []

            self.logger.info(
                f"Loading messages for conversation {conversation.conversations_id}.",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.load_messages.__name__,
            )

            messages = self.message_database.get_by_conversation(conversation)
            self.logger.info(
                f"Successfully loaded {len(messages)} messages for conversation {conversation.conversations_id}.",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.load_messages.__name__,
            )
            return [message for message in messages if message.messages_id is not None]
        except Exception as e:
            self.logger.error(
                f"Error loading messages for conversation {conversation.conversations_id if conversation else 'Unknown'}: {str(e)}",
                source=Path(__file__).name,
                call_by=file_caller,
                method_call=self.load_messages.__name__,
            )
            return []

    # PRIVATE METHODS

    def __generate_assistant_response(self, prompt: str, provider: EProviderName, model_name: str) -> IGenerateResponse:
        self.logger.info(
            f"Generating assistant response with provider {provider} and model {model_name}. Prompt length: {len(prompt)}",
            source=Path(__file__).name,
            call_by=Path(__file__).name,
            method_call=self.__generate_assistant_response.__name__,
        )
        llm_client = self.llm_provider_factory.get_provider(provider)
        self.logger.info(
            f"Using LLM client {llm_client.__class__.__name__} for provider {provider} and model {model_name}.",
            source=Path(__file__).name,
            call_by=Path(__file__).name,
            method_call=self.__generate_assistant_response.__name__,
        )
        return llm_client.generate(ICompletionRequest(provider=provider, model=model_name, prompt=prompt, context_hits=[]))

    def __save_message(self, conversation: ConversationModel, is_user_send: bool, content: str) -> MessageModel:
        self.logger.info(
            f"Saving message for conversation {conversation.conversations_id}. User sent: {is_user_send}. Content length: {len(content)}",
            source=Path(__file__).name,
            call_by=Path(__file__).name,
            method_call=self.__save_message.__name__,
        )
        response = self.message_database.create_message(conversation, content, is_user_send)
        return response

    def __get_conversation_files(
        self, conversation: ConversationModel
    ) -> list[ConversationFilesModel]:
        try:
            files = self.conversation_files_database.get_by_conversation(conversation)
            self.logger.info(
                f"Retrieved {len(files)} conversation files for conversation {conversation.conversations_id}",
                source=Path(__file__).name,
                call_by=Path(__file__).name,
                method_call=self.__get_conversation_files.__name__,
            )
            return [file for file in files if file.conversation_files_id is not None]
        except Exception as e:
            self.logger.error(
                f"Error retrieving documents for conversation {conversation.conversations_id}: {str(e)}",
                source=Path(__file__).name,
                call_by=Path(__file__).name,
                method_call=self.__get_conversation_files.__name__,
            )
            return []
