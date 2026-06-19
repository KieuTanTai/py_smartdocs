import asyncio
from pathlib import Path
import uuid
import time
from neo4j import Driver
from neo4j_graphrag.experimental.components.text_splitters.fixed_size_splitter import (
    FixedSizeSplitter,
)
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from backend.apps.core.enums.e_similarity_fn import ESimilarityFn
from backend.apps.core.interfaces.dataclass.locate.i_neo4j_search_request import INeo4jSearchRequest
from backend.apps.core.interfaces.dataclass.tasks.i_upload_response import IGraphRagParam
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import (
    INeo4jService,
)
from backend.apps.core.interfaces.system.i_logging import ILogger
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.generation.prompts import RagTemplate

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

    def create_vector_index(self, index_name: uuid.UUID, dimension: int, label: str = "Chunk", embedding_property: str = "embedding", similarity_fn: ESimilarityFn = ESimilarityFn.COSINE) -> uuid.UUID:
        self.logger.info(f"Creating vector index with name: {index_name}, dimension: {dimension}, label: {label}, embedding_property: {embedding_property}, similarity_fn: {similarity_fn.value}", Path(__file__).name, self.create_vector_index.__name__, self.create_vector_index.__name__)
        create_vector_index(self.driver, name=str(index_name).replace("-", "_"), label=label, embedding_property=embedding_property, dimensions=dimension, similarity_fn=similarity_fn.value)
        # self.__safe_create_vector_index(name=str(index_name), label=label, embedding_property=embedding_property, dimensions=dimension, similarity_fn=similarity_fn.value)
        self.wait_for_index_ready(index_name, timeout=30, file_caller=self.create_vector_index.__name__)
        return index_name

    def get_vector_cypher_retriever(
        self,
        embedder: Embedder,
        index_name: uuid.UUID,
        file_caller="",
    ) -> VectorCypherRetriever:
        self.logger.info(f"Getting Vector Cypher Retriever with index: {index_name}", Path(__file__).name, file_caller, self.get_vector_cypher_retriever.__name__)
        retriever = self.__create_graph_retriever(template=self.prompt_structure, embedder=embedder, index_name=index_name, file_caller=file_caller)
        return retriever

    async def execute_file_to_kg_pipeline(
        self,
        retrieval_query: str,
        index_name: uuid.UUID,
        params: list[IGraphRagParam],
        llm_model: LLMInterface,
        embedder: Embedder,
        file_caller="",
    ) -> VectorCypherRetriever:
        pipeline = self.__get_simple_KG_pipeline(llm_model, embedder)
        processed_files = 0
        self.logger.info(f"total files to process: {len(params)}", Path(__file__).name, file_caller, self.execute_file_to_kg_pipeline.__name__)
        for param in params:
            self.logger.info(
                f"Processing param: '{param.document_id}'", Path(__file__).name, file_caller, self.execute_file_to_kg_pipeline.__name__
            )
            async with self.semaphore:
                await pipeline.run_async(text=param.chunk_content, 
                                         document_metadata= {
                                             "conversation_id": str(param.conversation_id),
                                             "document_id": param.document_id,
                                             "chunk_id": str(param.chunk_id)
                                         })
            processed_files += 1
        self.logger.info(
            f"Completed processing files: {processed_files}", Path(__file__).name, file_caller, self.execute_file_to_kg_pipeline.__name__
        )
        return self.__create_graph_retriever(retrieval_query, embedder, index_name, file_caller)

    def wait_for_index_ready(self, index_name: uuid.UUID, timeout: int = 30, file_caller="") -> bool:
        self.logger.info(
            f"Waiting for index '{index_name}' to be ready with timeout of {timeout} seconds",
            Path(__file__).name,
            file_caller,
            self.wait_for_index_ready.__name__,
        )

        start_time = time.time()

        while time.time() - start_time < timeout:
            with self.driver.session() as session:
                result = session.run("""
                    SHOW INDEXES
                    YIELD name, state
                    WHERE name = $index_name
                    RETURN state
                """, index_name=str(index_name))

                record = result.single()

                if record and record["state"] == "ONLINE":
                    self.logger.info(
                        f"Index '{index_name}' is ready",
                        Path(__file__).name,
                        file_caller,
                        self.wait_for_index_ready.__name__,
                    )
                    return True

            time.sleep(2)

        self.logger.warning(
            f"Timeout reached while waiting for index '{index_name}' to be ready",
            Path(__file__).name,
            file_caller,
            self.wait_for_index_ready.__name__,
        )
        return False

    def search(self, search_request: INeo4jSearchRequest, llm: LLMInterface, retriever: VectorCypherRetriever, template: RagTemplate, file_caller="") -> str:
        self.logger.info(f"Executing search with query: {search_request.query_text} and top_k: {search_request.top_k}", Path(__file__).name, file_caller, self.search.__name__)
        if (llm is None) or (retriever is None) or (template is None):
            self.logger.error("LLM, retriever, and template must be provided for search", Path(__file__).name, file_caller, self.search.__name__)
            raise ValueError("LLM, retriever, and template must be provided for search")
        graph_rag = self.__create_graph_rag_search(llm, retriever, template)
        config = {
            # "conversation_id": search_request.conversation_id,
            # "document_ids": search_request.document_ids,
            "index_name": retriever.index_name,
            "top_k": search_request.top_k
        }
        result = graph_rag.search(query_text=search_request.query_text, retriever_config=config)
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
            from_file=False,
        )
        self.logger.info(f"Created SimpleKG Pipeline: {pipeline}", Path(__file__).name, "__get_simple_KG_pipeline", self.__get_simple_KG_pipeline.__name__)
        return pipeline

    def __safe_create_vector_index(
        self,
        name: str,
        label: str,
        embedding_property: str,
        dimensions: int,
        similarity_fn: str,
    ):
        query = f"""
        CREATE VECTOR INDEX `{name}`
        IF NOT EXISTS
        FOR (n:{label}) ON n.{embedding_property}
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: toInteger($dimensions),
                `vector.similarity_function`: $similarity_fn
            }}
        }}
        """
        with self.driver.session() as session:
            session.run(query, name=name, label=label, embedding_property=embedding_property, dimensions=dimensions, similarity_fn=similarity_fn)  # type: ignore

    def __create_graph_retriever(
        self,
        template: str,
        embedder: Embedder,
        index_name: uuid.UUID,
        file_caller="",
    ) -> VectorCypherRetriever:
        retriever = VectorCypherRetriever(
            self.driver,
            index_name=str(index_name),
            embedder=embedder,
            retrieval_query=template,
        )
        print(
            f"Created Graph Retriever with index: {index_name}\n   retriever: {retriever}"
        )
        self.logger.info(
            f"Created Graph Retriever with index: {index_name}\n   retriever: {retriever}",
            Path(__file__).name,
            file_caller,
            self.__create_graph_retriever.__name__,
        )
        return retriever
