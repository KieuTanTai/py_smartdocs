import datetime
from pathlib import Path
from typing import Any

import numpy as np
import faiss

from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import (
    IVectorStoreService,
)
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.response.i_vector_db_response import (
    IVectorDBDeleteResponse,
    IVectorDBLoadResponse,
    IVectorDBQueryResponse,
    IVectorDBUpsertResponse,
)
from backend.apps.utils.path_file_helper import create_path_file, delete_file_metadata_with_file_name, is_existed_in_metadata

class FaissService(IVectorStoreService):
    """
    singleton service for FAISS vector store operations.
    This class auto add output metadata file to metadata/faiss directory when upsert vector, and use cache to check if vector is existed before upsert.
    This class provides methods to upsert, search, delete, cache vectors and get collection info using FAISS library.
    It is designed to be used as a vector store backend in the LocateService.
    """

    def __init__(
        self,
        metadata_dir: Path,
        logger: ILogger,
    ):
        self.metadata_dir = metadata_dir / "faiss" 
        self.logger = logger

    def create_index(self, np_vectors: np.ndarray, ids: np.ndarray = np.array([]), file_caller: str = "") -> faiss.IndexFlatL2 | faiss.IndexIDMap:
        return self.__generate_faiss_index(np_vectors, ids, file_caller)

    def upsert(self, index: Any, vector_id: str, file_caller: str = "") -> IVectorDBUpsertResponse:
        self.__write_metadata_file(vector_id, index)
        self.logger.info(f"Upserted FAISS index for vector_id '{vector_id}' to metadata",
            Path(__file__).name, file_caller, method_call=self.upsert.__name__)
        return IVectorDBUpsertResponse(UUID=vector_id, create_at=datetime.datetime.now(), 
                                       sumarize_content="", is_success=True)

    def search(self, index: Any, vector_id: str, query_vector: np.ndarray, limit=5, allow_ids: set | None = None, 
               chunk_file_map: dict | None = None, file_caller: str = "") -> IVectorDBQueryResponse:
        query_vector = self.__validate_input(query_vector, np.float32)
        self.logger.info(f"Searching FAISS index for vector_id '{vector_id}' with query vector of shape {query_vector.shape}",
            Path(__file__).name, file_caller, method_call=self.search.__name__)
        distances, indices = index.search(query_vector, limit)
        distances, indices = self.__filter_output_search_results(distances, indices, allow_ids, chunk_file_map, file_caller)
        self.logger.info(f"FAISS search results for vector_id '{vector_id}': distances={distances}, indices={indices}",
            Path(__file__).name, file_caller, method_call=self.search.__name__)
        return IVectorDBQueryResponse(UUID=vector_id, distances=distances.tolist()[0], indices=indices.tolist()[0])

    def delete(self, vector_id: str, file_caller: str = "") -> IVectorDBDeleteResponse:
        deleted_count = delete_file_metadata_with_file_name(self.metadata_dir, vector_id, "faiss", self.logger)    
        if deleted_count == 0:
            self.logger.warning(f"Vector with id '{vector_id}' does not exist in metadata and cannot be deleted",
                Path(__file__).name, file_caller, method_call=self.delete.__name__)
            return IVectorDBDeleteResponse(UUID=vector_id, is_success=False, message=f"Vector with id '{vector_id}' does not exist in metadata")
        else:
            self.logger.info(f"Deleted vector with id '{vector_id}' from metadata",
                Path(__file__).name, file_caller, method_call=self.delete.__name__)
        return IVectorDBDeleteResponse(UUID=vector_id, is_success=True, deleted_count=deleted_count)

    def load(self, vector_id: str, file_caller: str = "") -> IVectorDBLoadResponse:
        path = self.is_existed_in_metadata(vector_id)
        if (path is None):
            self.logger.error(f"Metadata for vector_id '{vector_id}' does not exist",
                Path(__file__).name, file_caller, method_call=self.load.__name__)
            raise ValueError(f"Vector with id '{vector_id}' does not exist in metadata")
        index = faiss.read_index(str(path))
        self.logger.info(f"Loaded FAISS index for vector_id '{vector_id}' from metadata",
            Path(__file__).name, file_caller, method_call=self.load.__name__)
        return IVectorDBLoadResponse(UUID=vector_id, is_success=True, index=index)

    def is_existed_in_metadata(self, vector_id: str) -> Path | None:
        return is_existed_in_metadata(self.metadata_dir, vector_id, "faiss", self.logger)


    # region Private methods
    # helper method to filter FAISS search results based on allow_ids and chunk_file_map, it will log the filtering process and return the filtered distances and indices
    def __filter_output_search_results(self, distances: np.ndarray, indices: np.ndarray, allow_ids: set | None, chunk_file_map: dict | None, file_caller: str = "") -> tuple[np.ndarray, np.ndarray]:
        if allow_ids is None and chunk_file_map is None:
            self.logger.warning("No filters applied to search results, returning all results",
                Path(__file__).name, file_caller, method_call=self.__filter_output_search_results.__name__)
            return distances, indices

        filtered_distances = []
        filtered_indices = []
        for dist_row, idx_row in zip(distances, indices):
            filtered_row = [(dist, idx) for dist, idx in zip(dist_row, idx_row) if (allow_ids is None or idx in allow_ids) 
                            and (chunk_file_map is None or chunk_file_map.get(idx) is not None)]
            if filtered_row:
                filtered_distances.append([dist for dist, _ in filtered_row])
                filtered_indices.append([idx for _, idx in filtered_row])
        self.logger.info(f"Filtered search results: distances={filtered_distances}, indices={filtered_indices}",
            Path(__file__).name, file_caller, method_call=self.__filter_output_search_results.__name__)
        return np.array(filtered_distances), np.array(filtered_indices)

    # helper method to validate input numpy array, it will check if the input is empty, has zero rows, and has the correct dtype. It will also reshape 1D float32 input to 2D if necessary, and log the validation process.
    def __validate_input(self, input: np.ndarray, input_type: Any):
        if (input.size == 0):
            return input  # Return empty array as-is (valid for ids when no IDs are provided)
        if (input.shape[0] == 0):
            self.logger.error("Input cannot have zero rows",
                Path(__file__).name, Path(__file__).name)
            raise ValueError("Input cannot have zero rows")
        if (input.dtype != input_type):
            self.logger.warning(f"Input dtype {input.dtype} does not match expected type {input_type}, attempting to convert",
                Path(__file__).name, Path(__file__).name)
            input = np.asarray(input, dtype=input_type)
        if (input.ndim == 1 and input_type == np.float32):
            self.logger.info("Input is 1D, reshaping to 2D with one row",
                Path(__file__).name, Path(__file__).name)
            input = input.reshape(1, -1)
        
        return input

    # helper method to generate FAISS index from numpy vectors, it will validate the input vectors and ids, and log the process. It supports both IndexFlatL2 and IndexIDMap based on whether ids are provided.
    def __generate_faiss_index(self, np_vectors: np.ndarray, ids: np.ndarray = np.array([]), file_caller: str = "") -> faiss.IndexFlatL2 | faiss.IndexIDMap:
        np_vectors = self.__validate_input(np_vectors, np.float32)
        ids = self.__validate_input(ids, np.int64)
        dimension = np_vectors.shape[1] if np_vectors.ndim > 1 else np_vectors.shape[0]
        if ids.size > 0:
            self.logger.info(f"Creating FAISS index with {np_vectors.shape[0]} vectors, dimension {dimension}, and ids",
                Path(__file__).name, file_caller, method_call=self.__generate_faiss_index.__name__)
            index = faiss.IndexIDMap(faiss.IndexFlatL2(dimension))
            index.add_with_ids(np_vectors, ids) # type: ignore
            return index
        else:
            self.logger.info(f"Creating FAISS index with {np_vectors.shape[0]} vectors and dimension {dimension} without ids",
                Path(__file__).name, file_caller, method_call=self.__generate_faiss_index.__name__)
            index = faiss.IndexFlatL2(dimension)
            index.add(np_vectors) # type: ignore
            self.logger.info(f"Generated FAISS index with {index.ntotal} vectors and dimension {dimension}",
                Path(__file__).name, file_caller, method_call=self.__generate_faiss_index.__name__)
            return index


    # helper method to write FAISS index metadata file, it will check if metadata for the vector_id already exists before writing, and log the process
    def __write_metadata_file(self, vector_id: str, faiss_index: faiss.IndexFlatL2, file_caller: str = ""):
        path = self.is_existed_in_metadata(vector_id)
        if (path is not None and type(path) == Path):
            self.logger.warning(f"Metadata for vector_id '{vector_id}' already exists, skipping write",
                Path(__file__).name, file_caller, method_call=self.is_existed_in_metadata.__name__)
            return

        destination_path = create_path_file(self.metadata_dir, vector_id, "faiss")
        faiss.write_index(faiss_index, str(destination_path))
        self.logger.info(f"FAISS index metadata for vector_id '{vector_id}' written to '{destination_path}'",
            Path(__file__).name, file_caller, method_call=self.__write_metadata_file.__name__)
