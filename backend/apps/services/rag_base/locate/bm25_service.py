import datetime
import pickle
from pathlib import Path
from typing import Any, Dict
import numpy as np
from rank_bm25 import BM25Okapi

from backend.apps.core.interfaces.services.rag_base.locate.i_vector_store_service import IVectorStoreService
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.response.i_vector_db_response import (
    IVectorDBDeleteResponse, IVectorDBLoadResponse, IVectorDBQueryResponse, IVectorDBUpsertResponse
)
from backend.apps.utils.path_file_helper import create_path_file, is_existed_in_metadata

class BM25Service(IVectorStoreService):
    def __init__(self, metadata_dir: Path, logger: ILogger):
        self.metadata_dir = metadata_dir / "bm25"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger

    def create_index(self, np_vectors: np.ndarray = np.array([]), ids: np.ndarray = np.array([]), file_caller: str = "") -> Any:
        # BM25 không cần init index rỗng bằng np_vectors như FAISS
        return None

    def upsert(self, bm25_texts_map: Dict[str, str], vector_id: str, file_caller: str = "") -> IVectorDBUpsertResponse:
        # Tách từ (tokenize) cho thuật toán BM25
        keys = list(bm25_texts_map.keys())
        corpus = list(bm25_texts_map.values())
        tokenized_corpus = [doc.lower().split() for doc in corpus]
        
        # Tạo mô hình BM25Okapi
        bm25_model = BM25Okapi(tokenized_corpus)
        
        # Đóng gói cả key và model vào chung 1 object để serialize
        save_data = {
            "keys": keys,
            "model": bm25_model
        }
        
        destination_path = create_path_file(self.metadata_dir, vector_id, "bm25")
        with open(destination_path, "wb") as f:
            pickle.dump(save_data, f)
            
        self.logger.info(f"Upserted BM25 index cho document '{vector_id}'", file_caller=file_caller)
        return IVectorDBUpsertResponse(UUID=vector_id, create_at=datetime.datetime.now(), sumarize_content="", is_success=True)

    def search(self, index: Any, vector_id: str, query_vector: np.ndarray, query_text: str | None = None, limit=5, allow_ids: set | None = None, chunk_file_map: dict | None = None, file_caller: str = "") -> IVectorDBQueryResponse:
        if not query_text:
            raise ValueError("BM25 requires 'query_text' to perform lexical search.")
            
        keys = index["keys"]
        bm25_model = index["model"]
        
        tokenized_query = query_text.lower().split()
        doc_scores = bm25_model.get_scores(tokenized_query)
        
        # Lấy top_n index có điểm cao nhất
        top_indices = np.argsort(doc_scores)[::-1][:limit]
        
        distances = []
        indices_keys = []
        
        for idx in top_indices:
            score = doc_scores[idx]
            if score > 0: # Chỉ lấy các đoạn có chứa ít nhất 1 từ khóa
                distances.append(score)
                indices_keys.append(keys[idx]) # Trả về key chuỗi ("doc_id:chunk_id")
                
        self.logger.info(f"BM25 Search tìm thấy {len(distances)} kết quả", file_caller=file_caller)
        return IVectorDBQueryResponse(UUID=vector_id, distances=distances, indices=indices_keys)

    def load(self, vector_id: str, file_caller: str = "") -> IVectorDBLoadResponse:
        path = self.is_existed_in_metadata(vector_id)
        if not path:
            return IVectorDBLoadResponse(UUID=vector_id, is_success=False, message="BM25 index not found")
            
        with open(path, "rb") as f:
            index = pickle.load(f)
            
        return IVectorDBLoadResponse(UUID=vector_id, is_success=True, index=index)

    def is_existed_in_metadata(self, vector_id: str) -> Path | None:
        return is_existed_in_metadata(self.metadata_dir, vector_id, "bm25", self.logger)
    
    def delete(self, vector_id: str, file_caller: str = "") -> IVectorDBDeleteResponse:
        pass # Implement tương tự như FAISS