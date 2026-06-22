"""
Interface for Upload Job module.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import uuid

import faiss
import numpy as np

from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.enums.e_similarity_fn import ESimilarityFn
from backend.apps.core.interfaces.dataclass.cache.i_cache_param_value import ICacheParam
from backend.apps.core.interfaces.dataclass.extract.i_extract_response import IExtractResponse
from backend.apps.core.interfaces.dataclass.response.i_chat_response import IChatResponse
from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IconversationDocumentGetResponse
from backend.apps.core.interfaces.dataclass.response.i_generate_response import IGenerateResponse
from backend.apps.core.interfaces.dataclass.tasks.i_chunk_and_cache_response import IChunkAndCacheResponse, IChunkResponse
from backend.apps.core.interfaces.dataclass.tasks.i_upload_response import IEmbedResponse, IGraphRagParam, IGraphRagUploadResponse, IUploadResponse
from backend.apps.core.interfaces.llm.i_llm_client import ILLMClient
from neo4j_graphrag.retrievers import VectorCypherRetriever

from backend.apps.services.chat.models import ConversationFilesModel

class IUploadJob(ABC):
    """
    Contract for Document Upload Processing.
    """

    @abstractmethod
    def step_extract_and_normalize(
        self, file_path: Path, provider: EProviderName, file_caller: str = ""
    ) -> IExtractResponse:
        """
        extract and normalize text from file
        Args:
            file_path: real path of file to extract
            provider: provider name to use when extract (for example: google drive file may need google provider to extract)
            file_caller: function name of caller for logging
        Returns:
            extracted and normalized text from file
        """
        pass

    @abstractmethod
    def step_extract(
        self, file_path: Path, provider: EProviderName, file_caller: str = ""
    ) -> IExtractResponse:
        """
        extract text from file
        Args:
            file_path: real path of file or list of files to extract
            provider: provider name to use when extract (for example: google drive file may need google provider to extract)
            file_caller: function name of caller for logging
        Returns:
            extracted text from file or list of files
        """
        pass

    @abstractmethod
    def step_normalize(self, raw_text: str, file_caller: str = "") -> str:
        """
        normalize extracted text
        Args:
            raw_text: raw text to normalize
            file_caller: function name of caller for logging
        Returns:
            normalized text
        """
        pass

    @abstractmethod
    def step_chunk(
        self, document_id: str, normalized_text: str, file_caller: str = ""
    ) -> IChunkResponse:
        """
        chunk text into smaller pieces for embedding
        Args:
            document_id: ID of the document
            normalized_text: normalized text to chunk and cache
            file_caller: function name of caller for logging
        Returns:
            response containing chunked data
        """
        pass

    @abstractmethod
    def step_embed(
        self,
        chunk_response: IChunkResponse,
        provider: EProviderName,
        file_caller: str = "",
    ) -> IEmbedResponse:
        """
        embed chunked data and save to vector store
        Args:
            chunk_response: response containing chunked data
            provider: provider name to use for embedding (for example: different embedding model may be used for different provider)
            file_caller: function name of caller for logging
        Returns:
            response containing embedded data
        """
        pass

    @abstractmethod
    def step_cache(
        self,
        chunk_response: IChunkResponse,
        embedding_response: IEmbedResponse,
        file_caller: str = "",
    ) -> IChunkAndCacheResponse:
        """
        cache chunked data
        Args:
            chunk_response: response containing chunked data
            embedding_response: response containing embedded data
            file_caller: function name of caller for logging
        Returns:
            response containing cached data
        """
        pass

    def step_save(
        self,
        provider: EProviderName,
        faiss_file_id: uuid.UUID,
        document_ids: list[str],
        embedding_batches: list[np.ndarray],
        chunk_texts: list[str],
        paths: list[Path],
        ids: np.ndarray,
        file_caller: str = "",
    ) -> IUploadResponse | None:
        """
        save embedded data to vector store
        Args:
            provider: provider name to use for saving (for example: different vector store may be used for different provider)
            faiss_file_id: the ID of the FAISS file where the index is stored
            document_ids: list of document IDs corresponding to the embedded data
            embedding_batches: list of embedded vectors to save
            chunk_texts: list of original chunk texts
            paths: list of paths where the documents are cached
            ids: list of IDs corresponding to the embedded vectors
            file_caller: function name of caller for logging
        Returns:
            response containing save results and metadata, or None if saving is not applicable for the provider
        """
        pass

    @abstractmethod
    def summarize_document(self, 
                            faiss_index: faiss.IndexFlatL2 | faiss.IndexIDMap, 
                            faiss_file_id: uuid.UUID,
                            embeddings_stack: np.ndarray,
                            cache_params: list[ICacheParam],
                            provider: EProviderName,
                            model_name: str,
                            file_caller: str = "") -> IGenerateResponse:
        """
        summarize document based on original texts retrieved from vector store, this is used to improve the quality of summary by providing more context to LLM.
        Args:
            faiss_index: the FAISS index containing the embedded vectors for the document
            faiss_file_id: the ID of the FAISS file where the index is stored
            embeddings_stack: the stack of embedded vectors for the document
            cache_params: list of cache parameters used for retrieving original texts
            provider: provider name to use for summarization (for example: different LLM provider may be used for different provider)
            model_name: model name to use for summarization
            file_caller: function name of caller for logging
        Returns:
            summarized text for the document
        Raises:
            ValueError: If provider is invalid or document is not found
            Exception: For any other processing errors
        """

    @abstractmethod
    async def step_build_knowledge_graph(
        self,
        conversation_id: uuid.UUID,
        graph_params: list[IGraphRagParam],
        model_name: str,
        embedding_model_name: str,
        provider: EProviderName = EProviderName.GEMINI,
        similarity_fn: ESimilarityFn = ESimilarityFn.COSINE,
        file_caller: str = "",
    ) -> IGraphRagUploadResponse:
        """
        build knowledge graph for document
        Args:
            graph_params: list of graph parameters
            model_name: model name to use for building knowledge graph
            embedding_model_name: embedding model name to use for building knowledge graph
            provider: provider name to use for building knowledge graph (for example: different LLM provider may be used for different provider)
            similarity_fn: function to use for calculating similarity
            file_caller: function name of caller for logging
        Returns:
            IGraphRagUploadResponse: the created graph retriever with time counter
        Raises:
            ValueError: If provider is invalid or document is not found
            Exception: For any other processing errors
        """

        pass

    @abstractmethod
    def build_name(self, document_ids: list[str], split_by: str = "-", file_caller: str = "") -> str:
        """
        build file name for saving vector store files and this also use for conversation name
        Args:
            document_ids: list of document IDs to include in the file name
            split_by: string to use for splitting document IDs in the file name
            file_caller: function name of caller for logging
        Returns:
            file name built from document IDs
        """        
        pass

    @abstractmethod
    def build_chunk_keys(
        self, file_id: str, chunk_texts: list[str], file_caller: str = ""
    ) -> list[tuple[np.int64, str]]:
        """
        build chunk keys for caching
        Args:
            file_id: the ID of the FAISS file where the index is stored
            chunk_texts: list of original chunk texts
            file_caller: function name of caller for logging
        Returns:
            list of tuples containing chunk IDs and corresponding chunk texts
        """
        pass

    @abstractmethod
    def load_document(self, conversation_id: str, file_caller: str = "") -> IconversationDocumentGetResponse:
        """
        load document information for a conversation, which can be used for further processing such as building knowledge graph, or for displaying the document information in the UI, etc. The document information is stored in the database with the conversation_id as reference, and it includes the document ids and paths, etc.
        Args:
            conversation_id: the ID of the conversation to load documents for
            file_caller: function name of caller for logging
        Returns:
            IconversationDocumentGetResponse containing the document information for the conversation
        Raises:
            ValueError: If conversation is not found or has no associated documents
            Exception: For any other processing errors
        """
        pass