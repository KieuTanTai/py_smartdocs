import asyncio
from pathlib import Path

from neo4j import Driver
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from backend.apps.core.enums.e_similarity_fn import ESimilarityFn
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import (
    INeo4jService,
)
from backend.apps.core.interfaces.system.i_logging import ILogger
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.generation.prompts import ERExtractionTemplate, RagTemplate

class Neo4jService(INeo4jService):
    def __init__(
        self,
        driver: Driver,
        metadata_dir: Path,
        node_labels: list[str],
        relationship_type: list[str],
        prompt_structure: str,
        chunk_size: int,
        chunk_overlap: int,
        logger: ILogger,
    ):
        self.driver = driver
        self.metadata_dir = metadata_dir / "neo4j"
        self.node_labels = node_labels
        self.relationship_type = relationship_type
        self.prompt_structure = prompt_structure
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.logger = logger
        self.semaphore = asyncio.Semaphore(
            1
        )  # Limit to 1 concurrent file processing to manage resources

    def create_vector_index(self, index_name: str, dimension: int, label: str = "Chunk", embedding_property: str = "embedding", similarity_fn: ESimilarityFn = ESimilarityFn.COSINE) -> str:
        self.logger.info(f"Creating vector index with name: {index_name}, dimension: {dimension}, label: {label}, embedding_property: {embedding_property}, similarity_fn: {similarity_fn.value}", Path(__file__).name, self.create_vector_index.__name__, self.create_vector_index.__name__)
        create_vector_index(self.driver, name=index_name, label=label, embedding_property=embedding_property, dimensions=dimension, similarity_fn=similarity_fn.value)
        return index_name


    def __create_graph_retriever(
        self,
        template: str,
        embedder: Embedder,
        index_name: str,
        file_caller="",
    ) -> VectorCypherRetriever:
        retriever = VectorCypherRetriever(self.driver, index_name = index_name, embedder=embedder, retrieval_query=template)
        print(f"Created Graph Retriever with index: {index_name}\n   retriever: {retriever}")
        self.logger.info(f"Created Graph Retriever with index: {index_name}\n   retriever: {retriever}", Path(__file__).name, file_caller, self.__create_graph_retriever.__name__)
        return retriever

    async def execute_file_to_kg_pipeline(
        self,
        retrieval_query: str,
        index_name: str,
        file_paths: list[Path],
        llm_model: LLMInterface,
        embedder: Embedder,
        file_caller="",
    ) -> VectorCypherRetriever:
        pipeline = self.__get_simple_KG_pipeline(llm_model, embedder)
        processed_files = 0
        self.logger.info(f"total files to process: {len(file_paths)}", Path(__file__).name, file_caller, self.execute_file_to_kg_pipeline.__name__)
        for path in file_paths:
            self.logger.info(
                f"Processing file: '{path}'", Path(__file__).name, file_caller, self.execute_file_to_kg_pipeline.__name__
            )
            async with self.semaphore:
                await pipeline.run_async(file_path=str(path))
            processed_files += 1
        self.logger.info(
            f"Completed processing files: {file_paths}", Path(__file__).name, file_caller, self.execute_file_to_kg_pipeline.__name__
        )
        return self.__create_graph_retriever(retrieval_query, embedder, index_name, file_caller)

    def search(self, query_text: str, limit: int, llm: LLMInterface, retriever: VectorCypherRetriever, template: RagTemplate, file_caller="") -> str:
        self.logger.info(f"Executing search with query: {query_text} and limit: {limit}", Path(__file__).name, file_caller, self.search.__name__)
        if (llm is None) or (retriever is None) or (template is None):
            self.logger.error("LLM, retriever, and template must be provided for search", Path(__file__).name, file_caller, self.search.__name__)
            raise ValueError("LLM, retriever, and template must be provided for search")
        graph_rag = self.__create_graph_rag_search(llm, retriever, template)
        result = graph_rag.search(query_text=query_text, retriever_config={"top_k": limit})
        self.logger.info(f"Search completed with result: {result}", Path(__file__).name, file_caller, self.search.__name__)
        return result.answer

    def __create_graph_rag_search(self, llm: LLMInterface, retriever: VectorCypherRetriever, template: RagTemplate) -> GraphRAG:
        return GraphRAG(llm=llm, retriever=retriever, prompt_template=template)

    def __get_simple_KG_pipeline(
        self, llm_model: LLMInterface, embedder: Embedder
    ) -> SimpleKGPipeline:

        pipeline = SimpleKGPipeline(
            llm=llm_model,
            driver=self.driver,
            text_splitter=FixedSizeSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap),
            embedder=embedder,
            entities=self.node_labels,
            relations=self.relationship_type,
            prompt_template=self.prompt_structure,
            from_pdf=True,
        )
        self.logger.info(f"Created SimpleKG Pipeline: {pipeline}", Path(__file__).name, "__get_simple_KG_pipeline", self.__get_simple_KG_pipeline.__name__)
        return pipeline
