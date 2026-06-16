from dataclasses import dataclass, field
from typing import Any


@dataclass
class INeo4jRelationshipResponse:
    id: str | int
    type: str
    start_node_id: str | int
    end_node_id: str | int
    properties: dict[str, Any]


@dataclass
class INeo4jNodeResponse:
    id: str | int
    label: str
    properties: dict[str, Any]
    relationships: list[INeo4jRelationshipResponse] = field(default_factory=list)


@dataclass
class INeo4jGraphResponse:
    nodes: list[INeo4jNodeResponse]
    relationships: list[INeo4jRelationshipResponse]
