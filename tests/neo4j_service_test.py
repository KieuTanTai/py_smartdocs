import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from backend.apps.services.rag_base.locate.neo4j.neo4j_service import Neo4jService
from backend.apps.core.enums.e_similarity_fn import ESimilarityFn

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def mock_driver():
    return MagicMock()

@pytest.fixture
def neo4j_service(mock_driver, mock_logger):
    return Neo4jService(
        driver=mock_driver,
        metadata_dir=Path("./mock_metadata"),
        node_labels=["Document", "Entity", "Person"],
        relationship_type=["MENTIONS", "LOCATED_IN"],
        prompt_structure="Mock Prompt Template",
        chunk_size=500,
        chunk_overlap=50,
        logger=mock_logger
    )

def test_create_vector_index(neo4j_service, mock_logger):
    """Test 1: Kiểm tra hàm tạo Index có gọi đúng thư viện của Neo4j không"""
    
    # SỬA Ở ĐÂY: Thêm 'backend.' vào trước 'apps'
    with patch("backend.apps.services.rag_base.locate.neo4j.neo4j_service.create_vector_index") as mock_create_idx:
        
        index_name = neo4j_service.create_vector_index(
            index_name="test_doc_index",
            dimension=768,
            label="Chunk"
        )
        
        assert index_name == "test_doc_index"
        mock_create_idx.assert_called_once_with(
            neo4j_service.driver, 
            name="test_doc_index", 
            label="Chunk", 
            embedding_property="embedding", 
            dimensions=768, 
            similarity_fn=ESimilarityFn.COSINE.value
        )
        mock_logger.info.assert_called()

@pytest.mark.asyncio
async def test_execute_text_to_kg_pipeline_success(neo4j_service, mock_logger):
    """Test 2: Kiểm tra luồng cỗ máy Pipeline đọc Text và nhét vào Đồ thị (Async)"""
    
    mock_llm = MagicMock()
    mock_embedder = MagicMock()
    mock_texts = [
        "Văn bản trích xuất từ PDF số 1.",
        "Văn bản trích xuất từ file Word số 2."
    ]

    with patch("backend.apps.services.rag_base.locate.neo4j.neo4j_service.SimpleKGPipeline") as MockPipelineClass:
        mock_pipeline_instance = MockPipelineClass.return_value
        mock_pipeline_instance.run_async = AsyncMock()

        with patch.object(neo4j_service, "_Neo4jService__create_graph_retriever") as mock_create_retriever:
            mock_create_retriever.return_value = "Thành Công Sinh Retriever"

            result = await neo4j_service.execute_file_to_kg_pipeline(
                retrieval_query="MATCH (n) RETURN n",
                index_name="test_index",
                extracted_texts=mock_texts,
                llm_model=mock_llm,
                embedder=mock_embedder,
                file_caller="Test"
            )

            assert MockPipelineClass.called
            assert mock_pipeline_instance.run_async.call_count == 2
            
            mock_pipeline_instance.run_async.assert_any_call(text="Văn bản trích xuất từ PDF số 1.")
            mock_pipeline_instance.run_async.assert_any_call(text="Văn bản trích xuất từ file Word số 2.")
            
            assert result == "Thành Công Sinh Retriever"
            mock_create_retriever.assert_called_once()