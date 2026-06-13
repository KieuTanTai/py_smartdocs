from pathlib import Path

import neo4j

from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_node_labels import INeo4jNodeLabels
from backend.apps.core.interfaces.system.i_logging import ILogger

class Neo4jNodeLabelsConfig(INeo4jNodeLabels):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def get_node_labels(self, file_caller: str = "") -> list[str]:
        list = self.__build_basic_node_labels()
        self.logger.info(f"Node labels to be used for Neo4j graph database: {list}", Path(__file__).name, file_caller, self.get_node_labels.__name__)
        return list
    
    def get_relationship_type(self, file_caller: str = "") -> list[str]:
        list = self.__build_Relationship_type()
        self.logger.info(f"Relationship types to be used for Neo4j graph database: {list}", Path(__file__).name, file_caller, self.get_relationship_type.__name__)
        return list

    def __build_Relationship_type(self) -> list[str]:
        return [
            "RELATED_TO",
            "PART_OF",
            "LOCATED_IN",
            "CREATED_BY",
            "MENTIONS",
            "CITES",
            "SUPPORTS",
            "CONTRADICTS",
            "CAUSES",
            "PRECEDES",
            "FOLLOWS"
        ]

    def __build_basic_node_labels(self) -> list[str]:
            return [
                "Document",
                "Chunk",
                "Entity",
                "Concept",
                "Person",
                "Organization",
                "Place",
                "Event",
                "Topic"
            ]