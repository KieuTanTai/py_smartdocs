from pathlib import Path
from backend.apps.application.conversations.application import ConversationApplication
from backend.apps.application.document.application import DocumentApplication
from backend.apps.application.messages.application import MessageApplication
from backend.apps.interfaces.application.document.i_document_application import IDocumentApplication
from dependency_injector import containers, providers
import redis
from backend.apps.core.chunk.chunker import Chunker
from backend.apps.core.normalize.normalize import Normalize
from backend.apps.llm.llm_prompt_structure import LLMPromptStructure
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.job.message_job import MessageJob
from backend.apps.job.delete_job import DeleteJob
from backend.apps.job.conversation_job import ConversationJob
from backend.apps.job.upload_job import UploadJob
from backend.apps.tasks.upload_tasks import UploadTask
from backend.apps.tasks.message_tasks import MessageTask
from backend.apps.tasks.delete_task import DeleteTask
from backend.apps.tasks.conversation_tasks import ConversationTask
from backend.apps.services.cache.memory_pool import FaissMemoryPool
from backend.apps.services.cache.radis_cache_service import RedisCacheService
from backend.apps.services.cache.redis_cache_session import RedisCacheSession
from backend.apps.services.database.database_provider import DatabaseProvider
from backend.apps.services.rag_base.locate.neo4j.neo4j_node_labels_config import Neo4jNodeLabelsConfig
from backend.apps.services.rag_base.locate.neo4j.neo4j_session import Neo4jSession
from backend.apps.services.rag_base.storage.storage_service import FileStorageService
from backend.apps.core.interfaces.services.rag_base.storage.i_storage import IFileStorage
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_ocr_factory import ILLMOCRFactory
from backend.apps.core.interfaces.llm.llm_ocr.i_llm_uploader import ILLMUploader
from backend.apps.core.interfaces.services.rag_base.extract.i_extract_content import (
    IExtractContent,
)
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import (
    ILocateService,
)
from backend.apps.llm.llm_ocr.llm_ocr_factory import LLMOCRFactory
from backend.apps.llm.llm_ocr.mistral_uploader import MistralUploader
from backend.apps.services.rag_base.extract.extract_content_service import (
    ExtractContentService,
)
from backend.apps.services.rag_base.locate.faiss_service import FaissService
from backend.apps.services.rag_base.search.hybrid_search_service import HybridSearchService
from backend.apps.services.rag_base.locate.locate_service import LocateService
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.application.run_application import RunApplication
from backend.apps.tasks.upload_tasks import UploadTask
from sys_services.log_pool import LogPool
from sys_services.logging import Logger
from sys_services.read_config.config_provider import EnvConfigProvider
from sys_services.time_counter import TimeCounter
from sys_services.system_dirs import LOGS_DIR, METADATA_DIR
from sys_services.time_counter import TimeCounter


class BackendContainer(containers.DeclarativeContainer):
    """
    Backend dependency injection container. It provides singleton and factory providers for all core components of the backend, including configuration, logging, storage, extraction, and vector store services.
        - config_provider: Singleton provider for configuration management.
        - logger: Singleton provider for logging.
        - llm_ocr_factory: Factory provider for creating OCR extractors based on different providers.
        - llm_uploader: Factory provider for creating file uploaders for OCR processing.
        - file_storage: Factory provider for file storage service, which handles saving files and integrates with OCR factory and uploader.
        - extract_content_service: Factory provider for content extraction service, which uses the OCR factory and file storage to extract content from files.
        - extractor: Factory provider for the main extractor component, which uses the content extraction service.
        - locate_service: Factory provider for the locate service, which provides vector store operations and uses the FaissService as the default vector store backend.
    auto wires dependencies between components, ensuring that each service receives the necessary dependencies when instantiated.
    This container centralizes the configuration of all backend services and promotes modularity and testability.
    """

    config_provider = providers.Singleton(EnvConfigProvider)
    logger = providers.Singleton(Logger, LOGS_DIR)
    log_pool = providers.Singleton(LogPool, LOGS_DIR)
    llm_prompt_structure = providers.Singleton(LLMPromptStructure)
    llm_provider_factory = providers.Singleton(
        LLMProviderFactory,
        config_provider=config_provider,
        logger=log_pool,
    )
    database_provider = providers.Singleton(DatabaseProvider, logger=log_pool)
    #* singleton memory pool for faiss index, to avoid create multiple index for the same conversation, and to improve the performance of locate service by caching the index in memory. 
    #* The pool is a dictionary with conversation_id as key and faiss index as value. 
    #*The pool provides methods to add, get, remove and clear index in the pool, and it also logs the operations for debugging and monitoring purposes.
    memory_pool = providers.Singleton(FaissMemoryPool, logger=log_pool) 

    # Storage
    llm_ocr_factory = providers.Singleton(LLMOCRFactory, config_provider=config_provider, logger=log_pool)
    llm_uploader = providers.Factory(MistralUploader, logger=log_pool)
    file_storage = providers.Factory(
        FileStorageService,
        storage_dir=METADATA_DIR,
        uploader=llm_uploader,
        logger=log_pool,
    )

    # Extract
    extract_content_service = providers.Factory(
        ExtractContentService,
        factory=llm_ocr_factory,
        storage=file_storage,
        logger=log_pool,
    )
    
    time_counter = providers.Factory(TimeCounter)

    # Normalize
    normalize = providers.Singleton(Normalize, logger=log_pool)

    # Chunking
    chunker = providers.Singleton(Chunker, logger=log_pool)

    # Caching
    cache_session = providers.Factory(
        RedisCacheSession,
        config_provider=config_provider,
        metadata_dir=METADATA_DIR,
        logger=log_pool,
    )

    # Locate
    locate_service = providers.Factory(
        LocateService,
        metadata_dir=METADATA_DIR,
        logger=log_pool,
    )

    neo4j_node_labels_config = providers.Singleton(Neo4jNodeLabelsConfig, logger=log_pool)

    neo4j_session = providers.Factory(
        Neo4jSession,
        config_provider=config_provider,
        metadata_dir=providers.Object(METADATA_DIR),
        node_labels_config=neo4j_node_labels_config,
        logger=log_pool
    )

    neo4j_service = providers.Factory(
        lambda session: session.connect(file_caller="DI_Container"),
        session=neo4j_session
    )

    # Search
    hybrid_search_service = providers.Factory(
        HybridSearchService,
        locate_service=locate_service,
        logger=log_pool
    )

    upload_job = providers.Factory(
        UploadJob,
        extract_service=extract_content_service,
        normalize=normalize,
        chunker=chunker,
        cache_session=cache_session,
        llm_provider_factory=llm_provider_factory,
        locate_service=locate_service,
        config_provider=config_provider,
        logger=log_pool,
        database_provider=database_provider,
        session_provider=neo4j_session,
        llm_prompt_structure=llm_prompt_structure
    )

    time_counter = providers.Factory(TimeCounter)
    
    delete_job = providers.Factory(
        DeleteJob,
        locate_service=locate_service,
        neo4j_service=neo4j_service,
        cache_session=cache_session,
        logger=log_pool,
        storage_service=file_storage,
        time_counter=time_counter
    )

    message_job = providers.Factory(
        MessageJob,
        llm_provider_factory=llm_provider_factory,
        config_provider=config_provider,
        prompt_structure=llm_prompt_structure,
        locate_service=locate_service,
        cache_session=cache_session,
        logger=log_pool,
        hybrid_search_service=hybrid_search_service,
        extract_service=extract_content_service,
        database_provider=database_provider,
        neo4j_service=neo4j_service
    )

    conversation_job = providers.Factory(
        ConversationJob,
        llm_provider_factory=llm_provider_factory,
        llm_prompt_structure=llm_prompt_structure,
        config_provider=config_provider,
        database_provider=database_provider,
        locate_service=locate_service,
        cache_session=cache_session,
        memory_pool=memory_pool,
        logger=log_pool,
        hybrid_search_service=hybrid_search_service
    )
    
    upload_task = providers.Factory(
        UploadTask,
        upload_job=upload_job,
        memory_pool=memory_pool,
        database_provider=database_provider,
        logger=log_pool,
        time_counter=time_counter
    )

    message_task = providers.Factory(
        MessageTask,
        message_job=message_job,
        logger=log_pool,
        time_counter=time_counter
    )

    delete_task = providers.Factory(
        DeleteTask,
        delete_job=delete_job,
        logger=log_pool,
        time_counter=time_counter
    )

    conversation_task = providers.Factory(
        ConversationTask,
        conversation_job=conversation_job,
        memory_pool=memory_pool,
        logger=log_pool,
        time_counter=time_counter
    )

    run_application = providers.Factory(
        RunApplication,
        upload_task=upload_task,
        message_job=message_job,
        delete_job=delete_job,
        database_provider=database_provider,
        logger=log_pool
    )

    document_application = providers.Factory(
        DocumentApplication,
        upload_task=upload_task,
        cache_session=cache_session,
        database_provider=database_provider,
        logger=log_pool,
        time_counter=time_counter
    )

    message_application = providers.Factory(
        MessageApplication,
        message_task=message_task,
        logger=log_pool
    )

    conversation_application = providers.Factory(
        ConversationApplication,
        conversation_task=conversation_task,
        logger=log_pool
    )
