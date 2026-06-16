import sys
from unittest.mock import MagicMock, AsyncMock, patch

# =====================================================================
# 🚀 GIẢ LẬP DJANGO MODELS TRƯỚC KHI IMPORT MỌI THỨ KHÁC
# =====================================================================
mock_django_models = MagicMock()
sys.modules['backend.apps.services.chat.models'] = mock_django_models
sys.modules['apps.services.chat.models'] = mock_django_models

import pytest
from pathlib import Path
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.core.i_dataclass_transaction import ICompletionRequest
from backend.apps.core.interfaces.job.i_message_job import IMessageJobContextHit

from backend.apps.job.upload_job import UploadJob
from backend.apps.job.message_job import MessageJob

# ==========================================
# 🛠️ PHẦN 1: TẠO CÁC FIXTURE GIẢ LẬP (MOCKS)
# ==========================================

@pytest.fixture
def mock_logger():
    return MagicMock()

@pytest.fixture
def mock_config_provider():
    config = MagicMock()
    # TẠO CẤU HÌNH GIẢ CHO GEMINI ĐỂ VƯỢT QUA LỖI VALUE ERROR
    mock_provider_record = MagicMock()
    mock_provider_record.provider_name = EProviderName.MISTRAL
    mock_provider_record.embed_model_name = "mistral-large-latest"
    config.get_list_providers.return_value = [mock_provider_record]
    return config

@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    client.generate.return_value = "Đây là câu trả lời từ LLM kết hợp Graph RAG"
    mock_embedding_response = MagicMock()
    mock_embedding_response.embedding = MagicMock()
    mock_embedding_response.embedding.astype.return_value = [0.1, 0.2, 0.3]
    client.embedding.return_value = mock_embedding_response
    return client

@pytest.fixture
def mock_llm_factory(mock_llm_client):
    factory = MagicMock()
    factory.get_provider.return_value = mock_llm_client
    return factory

@pytest.fixture
def mock_neo4j_service():
    service = MagicMock()
    service.execute_file_to_kg_pipeline = AsyncMock()
    service.search.return_value = "Nguyễn Văn A -[LÀ QUẢN LÝ]-> Dự án Alpha"
    service._Neo4jService__create_graph_retriever.return_value = "MockRetriever"
    return service

@pytest.fixture
def mock_hybrid_search():
    hybrid = MagicMock()
    hybrid.fuse_results.return_value = [
        IMessageJobContextHit(text="Tài liệu ghi rằng dự án Alpha đang thiếu vốn.", score=0.9, source_document_id="doc_1")
    ]
    return hybrid

@pytest.fixture
def mock_locate_service():
    locate = MagicMock()
    store = MagicMock()
    store.load.return_value.is_success = False 
    locate.get_vector_store.return_value = store
    return locate

@pytest.fixture
def mock_cache_session():
    return MagicMock()

@pytest.fixture
def mock_extract_service():
    return MagicMock()

# ==========================================
# TEST UPLOAD JOB (Tạo Đồ Thị)
# ==========================================

def test_upload_job_step_build_knowledge_graph(
    mock_extract_service, mock_llm_factory, mock_locate_service, 
    mock_config_provider, mock_logger, mock_neo4j_service, mock_cache_session
):
    upload_job = UploadJob(
        extract_service=mock_extract_service,
        normalize=MagicMock(),
        chunker=MagicMock(),
        cache_session=mock_cache_session,
        llm_provider_factory=mock_llm_factory,
        locate_service=mock_locate_service,
        config_provider=mock_config_provider,
        logger=mock_logger,
        neo4j_service=mock_neo4j_service
    )

    upload_job.step_build_knowledge_graph(
        document_id="doc_123",
        extracted_text="Nội dung văn bản dài cần bóc tách thực thể...",
        provider=EProviderName.MISTRAL,
        file_caller="Test"
    )

    mock_neo4j_service.create_vector_index.assert_called_once_with(
        index_name="graph_index_doc_123", dimension=768, label="Chunk"
    )
    
    mock_neo4j_service.execute_file_to_kg_pipeline.assert_called_once()
    call_kwargs = mock_neo4j_service.execute_file_to_kg_pipeline.call_args.kwargs
    assert call_kwargs["extracted_texts"] == ["Nội dung văn bản dài cần bóc tách thực thể..."]
    assert call_kwargs["index_name"] == "graph_index_doc_123"

# ==========================================
# TEST MESSAGE JOB (Trộn Graph & Vector)
# ==========================================

@patch("backend.apps.job.message_job.MessageModel")
@patch("backend.apps.job.message_job.ConversationModel")
@patch("backend.apps.job.message_job.ConversationFilesModel")
def test_message_job_run_integrates_graph_and_vector(
    mock_conv_files_model, mock_conv_model, mock_msg_model,
    mock_llm_factory, mock_config_provider, mock_locate_service,
    mock_cache_session, mock_logger, mock_hybrid_search, 
    mock_extract_service, mock_neo4j_service, mock_llm_client
):
    mock_mapping = MagicMock()
    mock_mapping.faiss_index.faiss_index_id = "doc_123"
    mock_conv_files_model.objects.filter.return_value.exists.return_value = True
    mock_conv_files_model.objects.filter.return_value.first.return_value = mock_mapping
    mock_conv_files_model.objects.filter.return_value.__iter__.return_value = [] 
    
    message_job = MessageJob(
        llm_provider_factory=mock_llm_factory,
        config_provider=mock_config_provider,
        locate_service=mock_locate_service,
        cache_session=mock_cache_session,
        logger=mock_logger,
        hybrid_search_service=mock_hybrid_search,
        extract_service=mock_extract_service,
        neo4j_service=mock_neo4j_service
    )

    message_job._retrieve_context_hits = MagicMock(return_value=[
        IMessageJobContextHit(text="Tài liệu: Dự án Alpha thiếu vốn.", score=0.9, source_document_id="doc_123")
    ])

    response = message_job.run(
        conversation_id="conv_789", 
        content="Anh A đang làm dự án nào và tình trạng ra sao?", 
        provider=EProviderName.MISTRAL,
        model_name="mistral-large-latest"
    )

    mock_neo4j_service.search.assert_called_once()
    
    llm_call_kwargs = mock_llm_client.generate.call_args.args[0]
    generated_prompt = llm_call_kwargs.prompt

    assert "Dự án Alpha thiếu vốn" in generated_prompt, "Lỗi: Prompt thiếu Context từ Hybrid Search"
    assert "Nguyễn Văn A -[LÀ QUẢN LÝ]-> Dự án Alpha" in generated_prompt, "Lỗi: Prompt thiếu Graph Context từ Neo4j"
    
    assert response.assistant == "Đây là câu trả lời từ LLM kết hợp Graph RAG"
    assert response.provider == EProviderName.MISTRAL.value