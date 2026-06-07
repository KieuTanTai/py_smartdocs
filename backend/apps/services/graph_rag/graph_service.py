"""
Graph-based RAG service using Neo4j knowledge graphs.
Provides entity extraction, relationship mapping, and graph traversal search.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER

_neo4j_config = {
    "uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "auth": (
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "change-me"),
    ),
}


class Neo4jConnection:
    """
    Manages a Neo4j driver connection with lazy initialization.
    Falls back to file-based graph store if Neo4j is unavailable.
    """

    _instance: Optional["Neo4jConnection"] = None

    def __init__(self, logger: ILogger) -> None:
        self.logger = logger
        self._driver = None
        self._connected = False

    @classmethod
    def get_instance(cls, logger: ILogger) -> "Neo4jConnection":
        if cls._instance is None:
            cls._instance = cls(logger)
        return cls._instance

    def connect(self) -> bool:
        """Attempt to open a Neo4j connection. Returns True on success."""
        if self._connected:
            return True
        try:
            from neo4j import GraphDatabase
            self._driver = GraphDatabase.driver(
                _neo4j_config["uri"],
                auth=_neo4j_config["auth"],
            )
            self._driver.verify_connectivity()
            self._connected = True
            self.logger.info("Neo4j connection established", source="Neo4jConnection")
            return True
        except ImportError:
            self.logger.warning(
                "neo4j package not installed; graph operations will use file fallback.",
                source="Neo4jConnection",
            )
            return False
        except Exception as exc:
            self.logger.warning(
                f"Neo4j unavailable ({exc}); using file-based graph fallback.",
                source="Neo4jConnection",
            )
            return False

    def close(self) -> None:
        if self._driver:
            self._driver.close()
            self._connected = False

    def write(self, cypher: str, params: Optional[dict] = None) -> list[dict]:
        if not self._connected or not self._driver:
            raise RuntimeError("Neo4j not connected.")
        with self._driver.session() as session:
            result = session.run(cypher, params or {})
            return [dict(r) for r in result]

    def read(self, cypher: str, params: Optional[dict] = None) -> list[dict]:
        return self.write(cypher, params)


class GraphService:
    """
    Service for graph-based document processing.

    Operations:
        - Build knowledge graphs from documents (entity extraction)
        - Store graph in Neo4j (or file fallback)
        - Search using graph traversal (PageRank-style)
        - Hybrid: combine vector + graph retrieval
    """

    def __init__(self, logger: ILogger) -> None:
        self.logger = logger
        self._storage_dir = Path("storage/graph")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._neo4j = Neo4jConnection.get_instance(logger)
        self._use_neo4j = self._neo4j.connect()

    # ── Graph building ─────────────────────────────────────────────────────────

    def build_document_graph(
        self,
        document_id: str,
        chunks: list[str],
    ) -> dict:
        """
        Build a knowledge graph from document chunks.

        Steps:
          1. Extract entities (noun phrases, named entities) from each chunk
          2. Extract relationships between entities
          3. Store in Neo4j (or JSON file fallback)
          4. Return graph summary
        """
        nodes = []
        edges = []
        entity_id_map: dict[str, str] = {}

        for chunk_idx, chunk_text in enumerate(chunks):
            entities = self._extract_entities(chunk_text)
            for entity in entities:
                eid = f"{document_id}_{chunk_idx}_{entity['text'][:20]}"
                if entity["text"] not in entity_id_map:
                    entity_id_map[entity["text"]] = eid
                    nodes.append({
                        "id": eid,
                        "label": entity["text"],
                        "type": entity["type"],
                        "chunk_idx": chunk_idx,
                        "document_id": document_id,
                    })

            # Build relationships between co-occurring entities
            for i, e1 in enumerate(entities):
                for e2 in entities[i + 1:]:
                    rid = f"rel_{eid}_{entity_id_map.get(e2['text'], '')}"
                    edges.append({
                        "id": rid,
                        "from": entity_id_map.get(e1["text"], ""),
                        "to": entity_id_map.get(e2["text"], ""),
                        "document_id": document_id,
                    })

        # Persist to Neo4j or file
        if self._use_neo4j:
            self._persist_to_neo4j(document_id, nodes, edges)
        else:
            self._persist_to_file(document_id, nodes, edges)

        return {
            "document_id": document_id,
            "nodes": len(nodes),
            "edges": len(edges),
            "storage": "neo4j" if self._use_neo4j else "file",
        }

    def _extract_entities(self, text: str) -> list[dict]:
        """
        Simple entity extraction using spaCy-style heuristics.
        Extracts: PERSON, ORG, GPE, NORP, PRODUCT, EVENT, CONCEPT.
        Falls back to noun phrase extraction using regex.
        """
        import re
        entities = []
        seen: set[str] = set()

        # Named-entity regex patterns
        patterns = {
            "PERSON": r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
            "ORG": r"\b[A-Z][A-Za-z]*(?:Inc|LLC|Corp|Ltd|Company|Group)\b",
            "GPE": r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:City|Country|State|Province|Region)\b",
            "CONCEPT": r"\b(software|hardware|network|database|API|server|client|protocol|architecture|security)\b",
            "PRODUCT": r"\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\s+(?:v\d+\.\d+|version\s+\d+)\b",
        }

        for entity_type, pattern in patterns.items():
            for match in re.finditer(pattern, text):
                label = match.group(1) if match.lastindex else match.group(0)
                if label and label not in seen:
                    seen.add(label)
                    entities.append({"text": label, "type": entity_type})

        return entities

    def _persist_to_neo4j(
        self,
        document_id: str,
        nodes: list[dict],
        edges: list[dict],
    ) -> None:
        for node in nodes:
            self._neo4j.write(
                """
                MERGE (n:Entity {id: $id})
                SET n.label = $label, n.type = $type,
                    n.chunk_idx = $chunk_idx, n.document_id = $document_id
                """,
                node,
            )
        for edge in edges:
            if edge["from"] and edge["to"]:
                self._neo4j.write(
                    """
                    MATCH (a:Entity {id: $from}), (b:Entity {id: $to})
                    MERGE (a)-[r:RELATED {document_id: $document_id}]->(b)
                    """,
                    edge,
                )
        self.logger.info(
            f"Persisted graph to Neo4j: {len(nodes)} nodes, {len(edges)} edges",
            source="GraphService",
        )

    def _persist_to_file(
        self,
        document_id: str,
        nodes: list[dict],
        edges: list[dict],
    ) -> None:
        path = self._storage_dir / f"{document_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"nodes": nodes, "edges": edges}, f, ensure_ascii=False, indent=2)
        self.logger.info(
            f"Persisted graph to file: {path}",
            source="GraphService",
        )

    # ── Graph search ────────────────────────────────────────────────────────────

    def graph_search(
        self,
        query: str,
        document_ids: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search knowledge graph using entity matching and PageRank-style traversal.

        Returns list of chunks most relevant to the query via graph structure.
        """
        if self._use_neo4j:
            return self._graph_search_neo4j(query, document_ids, top_k)
        return self._graph_search_file(query, document_ids, top_k)

    def _graph_search_neo4j(
        self,
        query: str,
        document_ids: list[str],
        top_k: int,
    ) -> list[dict]:
        results = []
        try:
            entities = self._extract_entities(query)
            for entity in entities:
                records = self._neo4j.read(
                    """
                    MATCH (e:Entity {label: $label})
                    WHERE e.document_id IN $doc_ids
                    OPTIONAL MATCH (e)-[:RELATED*1..2]-(related:Entity)
                    RETURN e.label AS entity, e.chunk_idx AS chunk_idx,
                           collect(DISTINCT related.label) AS neighbours
                    LIMIT $limit
                    """,
                    {
                        "label": entity["text"],
                        "doc_ids": document_ids,
                        "limit": top_k,
                    },
                )
                for r in records:
                    results.append({
                        "entity": r.get("entity"),
                        "chunk_idx": r.get("chunk_idx"),
                        "neighbours": r.get("neighbours") or [],
                        "score": 1.0 / (len(results) + 1),
                    })
        except Exception as exc:
            self.logger.error(f"Neo4j graph search failed: {exc}", source="GraphService")
        return results[:top_k]

    def _graph_search_file(
        self,
        query: str,
        document_ids: list[str],
        top_k: int,
    ) -> list[dict]:
        results = []
        query_entities = {e["text"] for e in self._extract_entities(query)}
        for doc_id in document_ids:
            path = self._storage_dir / f"{doc_id}.json"
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                graph = json.load(f)
            for node in graph.get("nodes", []):
                if node["label"] in query_entities:
                    results.append({
                        "entity": node["label"],
                        "chunk_idx": node.get("chunk_idx"),
                        "neighbours": [
                            e["label"]
                            for e in graph["nodes"]
                            if any(
                                ed["from"] == node["id"] and ed["to"] == e["id"]
                                for ed in graph.get("edges", [])
                            )
                        ],
                        "score": 1.0 / (len(results) + 1),
                    })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    # ── Hybrid RAG (vector + graph) ─────────────────────────────────────────────

    def hybrid_search(
        self,
        query: str,
        document_ids: list[str],
        vector_results: list[dict],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Combine vector search results with graph-based entity context.

        Boosts chunks that:
          1. Appeared in vector results AND
          2. Are connected to query entities in the graph
        """
        graph_results = self.graph_search(query, document_ids, top_k=top_k * 2)
        entity_set = {r["entity"] for r in graph_results}
        boosted: list[dict] = []
        seen_chunks: set[int] = set()

        # Priority 1: in both vector and graph
        for vr in vector_results:
            for gr in graph_results:
                if vr.get("chunk_idx") == gr.get("chunk_idx"):
                    boosted.append({**vr, "graph_score": gr["score"], "boosted": True})
                    seen_chunks.add(vr["chunk_idx"])
                    break

        # Priority 2: in vector only
        for vr in vector_results:
            if vr.get("chunk_idx") not in seen_chunks:
                boosted.append({**vr, "boosted": False})
                seen_chunks.add(vr["chunk_idx"])

        # Priority 3: in graph only
        for gr in graph_results:
            if gr.get("chunk_idx") not in seen_chunks:
                boosted.append({**gr, "boosted": False})
                seen_chunks.add(gr["chunk_idx"])

        return boosted[:top_k]
