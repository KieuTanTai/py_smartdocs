from pathlib import Path

import neo4j
from neo4j import Driver
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_node_labels import INeo4jNodeLabels
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import INeo4jService
from backend.apps.core.interfaces.services.repository.i_connect_graph_db_session import IConnectGraphDBSession
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.services.rag_base.locate.neo4j.neo4j_service import Neo4jService
from neo4j_graphrag.generation.prompts import ERExtractionTemplate

class Neo4jSession(IConnectGraphDBSession):
    def __init__(self, config_provider: IConfigProvider, metadata_dir: Path, node_labels_config: INeo4jNodeLabels, logger: ILogger):
        if config_provider is None:
            raise ValueError("Neo4j configuration must be provided")
        self.driver = self.__create_neo4j_driver(config_provider)
        self.metadata_dir = metadata_dir
        self.node_labels_config = node_labels_config
        self.logger = logger
        self.chunk_size = config_provider.get_chunking_config().get("chunk_size", 500)
        self.chunk_overlap = config_provider.get_chunking_config().get("chunk_overlap", 100)

    def connect(self, file_caller="") -> INeo4jService:
        self.logger.info("Connecting to Neo4j graph database session...", Path(__file__).name, file_caller, self.connect.__name__)
        labels = self.node_labels_config.get_node_labels(file_caller)
        relationship_types = self.node_labels_config.get_relationship_type(file_caller)
        self.logger.info(f"Retrieved node labels: {labels}", Path(__file__).name, file_caller, self.connect.__name__)
        self.logger.info(f"Retrieved relationship types: {relationship_types}", Path(__file__).name, file_caller, self.connect.__name__)
        template = ERExtractionTemplate().DEFAULT_TEMPLATE
        self.logger.info(f"Built prompt structure for KG creation: {template}", Path(__file__).name, file_caller, self.connect.__name__)
        return Neo4jService(driver=self.driver, metadata_dir=self.metadata_dir, node_labels=labels, relationship_type=relationship_types, chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap, prompt_structure=template, logger=self.logger)

    def disconnect(self, file_caller=""):
        self.logger.info("Disconnecting from Neo4j graph database session...", Path(__file__).name, file_caller, self.disconnect.__name__)
        self.driver.close()

    def __create_neo4j_driver(self, config_provider: IConfigProvider) -> Driver:
        config = config_provider.get_neo4j_config()
        uri = config.get("uri")
        if uri is None:
            raise ValueError("Neo4j URI must be provided in the configuration")
        user = config.get("user")
        if user is None:
            raise ValueError("Neo4j user must be provided in the configuration")
        password = config.get("password")
        if password is None:
            raise ValueError("Neo4j password must be provided in the configuration")
        return neo4j.GraphDatabase.driver(uri, auth=(user, password))