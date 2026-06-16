from pathlib import Path
import asyncio

# Import Interfaces
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.interfaces.job.i_delete_job import IDeleteJob
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import INeo4jService
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_logging import ILogger

class DeleteJob(IDeleteJob):
    def __init__(
        self,
        locate_service: ILocateService,
        neo4j_service: INeo4jService,
        cache_session: IConnectCacheSession,
        logger: ILogger
    ):
        self.locate_service = locate_service
        self.neo4j_service = neo4j_service
        self.cache_session = cache_session
        self.logger = logger

    def step_delete_vectors(self, document_id: str, file_caller: str = "") -> bool:
        """Dọn dẹp FAISS và BM25"""
        self.logger.info(f"Starting to delete vectors for document {document_id}", Path(__file__).name, file_caller, self.step_delete_vectors.__name__)
        try:
            faiss_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
            bm25_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)
            
            file_name = f"{document_id}" 
            
            if faiss_store:
                faiss_store.delete(file_name, file_caller=self.step_delete_vectors.__name__)
            if bm25_store:
                bm25_store.delete(file_name, file_caller=self.step_delete_vectors.__name__)
                
            self.logger.info(f"Successfully deleted FAISS/BM25 vectors for {document_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete vectors for {document_id}: {str(e)}")
            raise e

    def step_delete_graph_data(self, document_id: str, file_caller: str = "") -> bool:
        """Dọn dẹp Graph DB (Neo4j)"""
        self.logger.info(f"Starting to delete Graph data for document {document_id}", Path(__file__).name, file_caller, self.step_delete_graph_data.__name__)
        index_name = f"graph_index_{document_id}"
        
        try:
            # 1. Chạy ngầm hàm Async để gọi Cypher xóa Node trong Neo4j
            async def _run_delete_pipeline():
                # Xóa các Node Chunk thuộc về Document này
                # Giả định lúc tạo Graph, bạn có lưu metadata source/document_id vào node Chunk
                delete_query = f"""
                MATCH (c:Chunk) WHERE c.index_name = '{index_name}' 
                DETACH DELETE c
                """
                # Lưu ý: Cần viết thêm hàm execute_query trong INeo4jService nếu chưa có
                await self.neo4j_service.execute_query(delete_query)
                
            asyncio.run(_run_delete_pipeline())

            # 2. Xóa Vector Index của Graph trong Neo4j
            try:
                self.neo4j_service.drop_vector_index(index_name=index_name)
            except Exception as e:
                self.logger.warning(f"Index {index_name} might not exist or failed to drop: {e}")

            self.logger.info(f"Successfully deleted Graph Data for {document_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete Graph Data for {document_id}: {str(e)}")
            raise e

    def step_clear_cache(self, document_id: str, file_caller: str = "") -> bool:
        """Dọn dẹp Cache (Redis)"""
        self.logger.info(f"Clearing cache for document {document_id}", Path(__file__).name, file_caller, self.step_clear_cache.__name__)
        try:
            cache_service = self.cache_session.connect(file_caller=self.step_clear_cache.__name__)
            # Gọi hàm xóa cache theo key (Yêu cầu ICacheService có hàm delete)
            cache_service.delete(document_id, file_caller=self.step_clear_cache.__name__)
            self.logger.info(f"Successfully cleared cache for {document_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear cache for {document_id}: {str(e)}")
            # Không raise error ở đây để tránh làm chết luồng nếu Redis có sự cố nhỏ
            return False
        finally:
            self.cache_session.disconnect(file_caller=self.step_clear_cache.__name__)