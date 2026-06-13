from abc import ABC, abstractmethod
from pathlib import Path
from neo4j_graphrag.embeddings import Embedder
from neo4j_graphrag.llm.base import LLMInterface
from neo4j_graphrag.retrievers import VectorCypherRetriever
from neo4j_graphrag.generation.prompts import RagTemplate
from backend.apps.core.enums.e_similarity_fn import ESimilarityFn

class INeo4jService(ABC):
    """
    This interface defines the contract for a Neo4j service that provides methods for interacting with a Neo4j graph database.
    It includes methods for creating vector indexes, executing a file to knowledge graph pipeline, creating graph
    retrievers, and performing search operations using retrieval-augmented generation (RAG) techniques.
    Implementations of this interface should provide concrete logic for each of these operations, allowing for flexibility
    When you wanna search results from Neo4j graph database based on a query, you can use the search method of this interface, which will utilize the provided LLM and retriever to generate a response based on the retrieved information from the graph database.
    first: run execute_file_to_kg_pipeline to process files and create the knowledge graph in Neo4j, then create a graph retriever using create_graph_retriever, and finally use the search method to perform queries against the graph database and generate responses using the LLM.
    second: create rag template using create_rag_template, then create a graph retriever using create_graph_retriever, and finally use the search method to perform queries against the graph database and generate responses using the LLM.
    third: create a retriever using create_graph_retriever, and then use the search method to perform queries against the graph database and generate responses using the LLM, without necessarily running the file to knowledge graph pipeline or creating a RAG template, depending on the use case and requirements of the application.
    after that: you can use the search method to perform queries against the graph database and generate responses using the LLM, leveraging the created retriever and RAG template as needed for the specific query and response generation process.
    """

    @abstractmethod
    # def get_simple_KG_pipeline(self, llm_model: LLMInterface, embedder: Embedder) -> SimpleKGPipeline:
    #     pass
    async def execute_file_to_kg_pipeline(
        self,
        retrieval_query: str,
        index_name: str,
        file_paths: list[Path],
        llm_model: LLMInterface,
        embedder: Embedder,
        file_caller="",
    ) -> VectorCypherRetriever:
        """
        Executes the file to knowledge graph pipeline for the given file paths using the provided LLM model and embedder.
        This method automatically creates a graph retriever based on the provided template and embedder, and returns the retriever for use in subsequent search operations.
        :param file_paths: List of file paths to process
        :param retrieval_query: Query for retrieving relevant information
        :param index_name: Name of the vector index to use
        :param llm_model: LLM model to use for the pipeline
        :param embedder: Embedder to use for the pipeline
        :param file_caller: Optional string to identify the caller of this method for logging purposes
        :return: VectorCypherRetriever instance
        """

        pass

    @abstractmethod
    def create_vector_index(self, index_name: str, dimension: int, label: str = "Chunk", embedding_property: str = "embedding", similarity_fn: ESimilarityFn = ESimilarityFn.COSINE) -> str:
        """
        Creates a vector index in the Neo4j database with the specified parameters.
        :param index_name: Name of the index to create
        :param dimension: Dimension of the vectors to be indexed
        :param label: Node label to which the index will be applied (default is "Chunk")
        :param embedding_property: Name of the property that contains the vector embeddings (default is "embedding")
        :param similarity_fn: Similarity function to use for the index (default is "COSINE")
        :return: Name of the created index
        """
        pass

    # @abstractmethod
    # def create_rag_template(self, template_str: str, expected_inputs: list[str]) -> RagTemplate:
    #     """
    #     Creates a RAG template with the specified template string and expected inputs.  
    #     You can use this method to create a RAG template that defines the structure of the prompt to be used for retrieval-augmented generation, based on the specific requirements of your application and the expected inputs for the template.
    #     :param template_str: The template string that defines the structure of the prompt to be used for retrieval-augmented generation.
    #     :param expected_inputs: A list of expected input variables that will be used to format the template string.
    #     :return: A RagTemplate object that can be used to generate prompts for retrieval-augmented generation.
    #     """
    #     pass

    # @abstractmethod
    # def create_graph_retriever(self, template: str, embedder: Embedder, index_name: str = "text_embeddings", file_caller="") -> VectorCypherRetriever:
    #     """
    #     Creates a graph retriever that can be used to retrieve relevant information from the Neo4j database based on the provided template and embedder.
    #     :param template: The template string that defines the structure of the retrieval query to be used by the retriever.
    #     :param embedder: The embedder to use for generating vector embeddings for the retrieval process.
    #     :param index_name: The name of the vector index to use for retrieval (default is "text_embeddings").
    #     :param file_caller: Optional string to identify the caller of this method for logging purposes.
    #     :return: A VectorCypherRetriever object that can be used to perform retrieval operations on the Neo4j database.
    #     """
    #     pass

    @abstractmethod
    def search(self, query_text:str, limit: int, llm: LLMInterface, retriever: VectorCypherRetriever, template: RagTemplate, file_caller="") -> str:
        """
        Performs a search operation on the Neo4j database using the provided query, LLM, retriever, and template.
        :param query: The search query to execute against the Neo4j database.
        :param limit: The maximum number of results to return from the search.
        :param llm: The LLM interface to use for generating responses based on the retrieved information.
        :param retriever: The graph retriever to use for retrieving relevant information from the Neo4j database.
        :param template: The RAG template to use for formatting the prompt for the LLM based on the retrieved information.
        :param file_caller: Optional string to identify the caller of this method for logging purposes.
        :return: A string response generated by the LLM based on the retrieved information and formatted using the provided template.
        """
        pass
