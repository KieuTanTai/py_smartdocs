from pathlib import Path
from dependency_injector import containers, providers
import redis
from backend.apps.core.chunk.chunker import Chunker
from backend.apps.core.normalize.normalize import Normalize
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.job.message_job import MessageJob
from backend.apps.job.conversation_job import ConversationJob
from backend.apps.job.upload_job import UploadJob
from backend.apps.services.cache.radis_cache_service import RedisCacheService
from backend.apps.services.cache.redis_cache_session import RedisCacheSession
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
from backend.apps.services.rag_base.locate.locate_service import LocateService
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.logging import Logger
from sys_services.read_config.config_provider import EnvConfigProvider
from sys_services.system_dirs import METADATA_DIR


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
    logger = providers.Singleton(Logger)

    # Storage
    llm_ocr_factory = providers.Factory(LLMOCRFactory, config_provider=config_provider, logger=logger)
    llm_uploader = providers.Factory(MistralUploader, logger=logger)
    file_storage = providers.Factory(
        FileStorageService,
        storage_dir=METADATA_DIR,
        uploader=llm_uploader,
        logger=logger,
    )

    # Extract
    extract_content_service = providers.Factory(
        ExtractContentService,
        factory=llm_ocr_factory,
        storage=file_storage,
        logger=logger,
    )

    # Normalize
    normalize = providers.Singleton(Normalize, logger=logger)

    # Chunking
    chunker = providers.Singleton(Chunker, logger=logger)

    # Caching
    cache_service = providers.Factory(
        RedisCacheSession,
        config_provider=config_provider,
        metadata_dir=METADATA_DIR,
        logger=logger,
    )

    llm_provider_factory = providers.Factory(
        LLMProviderFactory,
        config_provider=config_provider,
        logger=logger,
    )

    # Locate
    locate_service = providers.Factory(
        LocateService,
        metadata_dir=METADATA_DIR,
        logger=logger,
    )

    upload_job = providers.Factory(
        UploadJob,
        extract_service=extract_content_service,
        normalize=normalize,
        chunker=chunker,
        cache_session=cache_service,
        llm_provider_factory=llm_provider_factory,
        locate_service=locate_service,
        config_provider=config_provider,
        logger=logger,
    )

    message_job = providers.Factory(
        MessageJob,
        llm_provider_factory=llm_provider_factory,
        config_provider=config_provider,
        locate_service=locate_service,
        cache_session=cache_service,
        logger=logger,
    )

    conversation_job = providers.Factory(
        ConversationJob,
        llm_provider_factory=llm_provider_factory,
        config_provider=config_provider,
        logger=logger,
    )
