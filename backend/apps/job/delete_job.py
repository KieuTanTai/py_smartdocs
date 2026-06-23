from pathlib import Path
from asgiref.sync import async_to_sync
import concurrent.futures

# Import Interfaces
from backend.apps.core.enums.e_backend_storage_name import EBackendStorageName
from backend.apps.core.interfaces.services.rag_base.storage.i_storage import IFileStorage
from backend.apps.interfaces.job.i_delete_job import IDeleteJob
from backend.apps.core.interfaces.services.rag_base.locate.i_locate_service import ILocateService
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import INeo4jService
from backend.apps.core.interfaces.services.repository.i_connect_cache_session import IConnectCacheSession
from backend.apps.core.interfaces.system.i_logging import ILogger
from sys_services.time_counter import TimeCounter

class DeleteJob(IDeleteJob):
    def __init__(
        self,
        locate_service: ILocateService,
        neo4j_service: INeo4jService,
        cache_session: IConnectCacheSession,
        logger: ILogger,
        storage_service: IFileStorage,
        time_counter: TimeCounter
    ):
        self.locate_service = locate_service
        self.neo4j_service = neo4j_service
        self.cache_session = cache_session
        self.logger = logger
        self.storage_service = storage_service
        self.time_counter = time_counter

    def step_delete_vectors(self, document_id: str, file_caller: str = "") -> bool:
        """Dọn dẹp FAISS và BM25"""
        self.logger.info(f"Starting to delete vectors for document {document_id}", Path(__file__).name, file_caller, self.step_delete_vectors.__name__)
        try:
            faiss_store = self.locate_service.get_vector_store(EBackendStorageName.FAISS)
            bm25_store = self.locate_service.get_vector_store(EBackendStorageName.BM25)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                futures = []
                caller_name = self.step_delete_vectors.__name__
                
                if faiss_store:
                    futures.append(executor.submit(self._delete_single_vector_store, faiss_store, document_id, caller_name))
                if bm25_store:
                    futures.append(executor.submit(self._delete_single_vector_store, bm25_store, document_id, caller_name))
                
                # Chờ cả 2 hoàn thành
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                
            self.logger.info(f"Successfully deleted FAISS/BM25 vectors for {document_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete vectors for {document_id}: {str(e)}")
            raise e
        
    def _delete_single_vector_store(self, store, document_id: str, caller_name: str) -> None:
        """Hàm công nhân: Xóa độc lập trên một Vector Store cụ thể."""
        if store:
            try:
                store.delete(document_id, file_caller=caller_name)
            except Exception as e:
                # Ghi log store bị lỗi (FAISS/BM25)
                store_name = store.__class__.__name__
                self.logger.warning(
                    f"Warning: Failed to delete from {store_name} for document {document_id}. Error: {e}", 
                    source=str(self.__class__)
                )
                raise e 

    def step_delete_graph_data(self, document_id: str, file_caller: str = "") -> bool:
        """Dọn dẹp Graph DB (Neo4j)"""
        self.logger.info(f"Starting to delete Graph data for document {document_id}", Path(__file__).name, file_caller, self.step_delete_graph_data.__name__)
        safe_id_str = str(document_id).replace("-", "")
        index_name = f"graph_index_{safe_id_str}"
        
        try:
            
            delete_query = """
            MATCH (c:Chunk) WHERE c.index_name = $index_name 
            DETACH DELETE c
            """
                
            async_to_sync(self.neo4j_service.execute_query)(
                query=delete_query, 
                parameters={"index_name": index_name}
            )

            # Xóa Vector Index của Graph trong Neo4j
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
            cache_key = f"document_chunks:{document_id}:meta"
            # Gọi hàm xóa cache theo key
            cache_service.delete(cache_key, file_caller=self.step_clear_cache.__name__)
            self.logger.info(f"Successfully cleared cache for {document_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear cache for {document_id}: {str(e)}")
            return False
        finally:
            self.cache_session.disconnect(file_caller=self.step_clear_cache.__name__)
            
    def step_delete_cloud_file(self, file_id: str, file_caller: str = "") -> bool:
        """Dọn dẹp file lưu tạm trên Mistral Cloud"""
        self.logger.info(f"Starting to delete cloud file {file_id}", Path(__file__).name, file_caller, self.step_delete_cloud_file.__name__)
        try:

            success = self.storage_service.delete_file(file_id)
            if success:
                self.logger.info(f"Successfully deleted cloud file {file_id}")
            return success
        except Exception as e:
            self.logger.warning(f"Cloud file {file_id} might not exist or failed to delete: {str(e)}")

            return False