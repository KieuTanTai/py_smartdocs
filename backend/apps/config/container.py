from pathlib import Path
from dependency_injector import containers, providers
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
from sys_services.interfaces.i_config import IConfigProvider
from sys_services.interfaces.i_logging import ILogger
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
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

    config_provider = providers.Singleton(IConfigProvider, DEFAULT_CONFIG_PROVIDER)
    logger = providers.Singleton(ILogger, DEFAULT_LOGGER)

    # Storage
    llm_ocr_factory = providers.Factory(ILLMOCRFactory)
    llm_uploader = providers.Factory(ILLMUploader, logger=logger)
    file_storage = providers.Factory(
        IFileStorage,
        storage_dir=METADATA_DIR,
        uploader=llm_uploader,
        logger=logger,
    )

    # Extract
    extract_content_service = providers.Factory(
        IExtractContent,
        factory=llm_ocr_factory,
        storage=file_storage,
        logger=logger,
    )

    # Locate
    locate_service = providers.Factory(
        ILocateService,
        metadata_dir=config_provider.provided.get("faiss_metadata_dir"),
        faiss_service=providers.Factory(FaissService, logger=logger),
        logger=logger,
    )
