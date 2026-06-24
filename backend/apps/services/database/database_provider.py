"""
Database provider.
Resolves database services by Django model type.
"""

from typing import Any, TypeVar, cast

from django.db.models import Model

from backend.apps.core.interfaces.services.rag_base.database.i_database_provider import (
    IDatabaseProvider,
)
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_database import (
    IConversationDatabase,
)
from backend.apps.core.interfaces.services.rag_base.database.i_conversation_file_database import (
    IConversationFileDatabase,
)
from backend.apps.core.interfaces.services.rag_base.database.i_document_database import (
    IDocumentDatabase,
)
from backend.apps.core.interfaces.services.rag_base.database.i_model_database import (
    IModelDatabase,
)
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.services.chat.models import (
    ConversationCacheModel,
    ConversationFilesModel,
    ConversationModel,
    DocumentModel,
    MessageModel,
)
from backend.apps.services.database.conversation_cache_database_service import ConversationCacheDatabaseService
from backend.apps.services.database.conversation_file_database_service import (
    ConversationFileDatabaseService,
)
from backend.apps.services.database.conversation_database_service import (
    ConversationDatabaseService,
)
from backend.apps.services.database.document_database_service import (
    DocumentDatabaseService,
)
from backend.apps.services.database.message_database_service import (
    MessageDatabaseService,
)


TModel = TypeVar("TModel", bound=Model)


class DatabaseProvider(IDatabaseProvider):
    """Provider used by application/task classes to resolve model database services."""

    def __init__(
        self,
        logger: ILogger,
        document_database: IModelDatabase[DocumentModel] | None = None,
        conversation_database: IModelDatabase[ConversationModel] | None = None,
        conversation_file_database: IModelDatabase[ConversationFilesModel] | None = None,
        conversation_message_database: IModelDatabase[MessageModel] | None = None,
        conversation_cache_database: IModelDatabase[ConversationCacheModel] | None = None
    ):
        self.logger = logger
        self._services: dict[type[Model], IModelDatabase[Any]] = {
            DocumentModel: document_database or DocumentDatabaseService(),
            ConversationModel: conversation_database or ConversationDatabaseService(),
            ConversationFilesModel: (
                conversation_file_database or ConversationFileDatabaseService()
            ),
            MessageModel: (
                conversation_message_database or MessageDatabaseService()
            ),
            ConversationCacheModel: (
                conversation_cache_database or ConversationCacheDatabaseService()
            ),
        }

    def get_model_service(self, model_type: type[TModel]) -> IModelDatabase[TModel]:
        try:
            self.logger.info(
                f"Resolving database service for model type: {model_type.__name__}",
                source=__file__,
                call_by=self.get_model_service.__name__,
            )
            return cast(IModelDatabase[TModel], self._services[model_type])
        except KeyError as exc:
            self.logger.error(
                f"No database service registered for model type: {model_type.__name__}",
                source=__file__,
                call_by=self.get_model_service.__name__,
            )
            raise ValueError(
                f"No database service registered for model type: {model_type.__name__}"
            ) from exc