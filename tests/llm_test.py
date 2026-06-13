"""
Test requests to all 3 LLM providers: Gemini, Mistral, and Ollama
"""

import asyncio
import datetime
from pathlib import Path
from backend.apps.core.enums.e_similarity_fn import ESimilarityFn
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_service import (
    INeo4jService,
)
from backend.apps.core.interfaces.services.repository.i_connect_graph_db_session import (
    IConnectGraphDBSession,
)
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.core.interfaces.core.i_dataclass_transaction import (
    ICompletionRequest,
    ICompletionResponse,
    IEmbeddingResponse,
)
from neo4j_graphrag.generation.prompts import ERExtractionTemplate

from backend.apps.llm.llm_prompt_structure import LLMPromptStructure
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.services.rag_base.locate.neo4j.neo4j_node_labels_config import (
    Neo4jNodeLabelsConfig,
)
from sys_services.logging import Logger
from sys_services.read_config.config_provider import EnvConfigProvider
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.read_config.read_ollama_config import OLLAMA_CONFIG
from backend.apps.services.rag_base.locate.neo4j.neo4j_session import Neo4jSession
from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from backend.apps.core.interfaces.services.rag_base.locate.neo4j.i_neo4j_node_labels import (
    INeo4jNodeLabels,
)

# Test prompt
RETRIEVED_CHUNKS = [
    """
Trách nhiệm của Ban Giám đốc
Ban Giám đốc Công ty chịu trách nhiệm về việc lập và trình bày trung thực và hợp lý Báo cáo tài chính của Công ty theo các chuẩn mực kế toán Việt Nam, Chế độ Kế toán doanh nghiệp Việt Nam và các quy định pháp lý có liên quan đến việc lập và trình bày Báo cáo tài chính và chịu trách nhiệm về kiểm soát nội bộ mà Ban Giám đốc xác định là cần thiết để đảm bảo cho việc lập và trình bày Báo cáo tài chính không có sai sót trong yếu do gian lận hoặc nhầm lẫn.

## Trách nhiệm của Kiểm toán viên
Trách nhiệm của chúng tôi là đưa ra ý kiến về Báo cáo tài chính dựa trên kết quả của cuộc kiểm toán.

Chúng tôi đã tiến hành kiểm toán theo các chuẩn mực kiểm toán Việt Nam.

Các chuẩn mực này yêu cầu chúng tôi tuân thủ chuẩn mực và các quy định về đạo đức nghề nghiệp, lập kế hoạch và thực hiện cuộc kiểm toán để đạt được sự đảm bảo hợp lý về việc liệu Báo cáo tài chính của Công ty có còn sai sót trong yếu hay không.

""",
    """
Công việc kiểm toán bao gồm thực hiện các thủ tục nhằm thu thập các bằng chứng kiểm toán về các số liệu và thuyết minh trên Báo cáo tài chính.

Các thủ tục kiểm toán được lựa chọn dựa trên xét đoán của kiểm toán viên, bao gồm đánh giá rủi ro có sai sót trong yếu trong Báo cáo tài chính do gian lận hoặc nhầm lẫn.

Khi thực hiện đánh giá các rủi ro này, kiểm toán viên đã xem xét kiểm soát nội bộ của Công ty liên quan đến việc lập và trình bày Báo cáo tài chính trung thực, hợp lý nhằm thiết kế các thủ tục kiểm toán phù hợp với tình hình thực tế, tuy nhiên không nhằm mục đích đưa ra ý kiến về hiệu quả của kiểm soát nội bộ của Công ty.

Công việc kiểm toán cũng bao gồm đánh giá tính thích hợp của các chính sách kế toán được áp dụng và tính hợp lý của các ước tính kế toán của Ban Giám đốc cũng như đánh giá việc trình bày tổng thể Báo cáo tài chính.
""",
]
ROOT_DIR = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT_DIR / "docs" / "pdfs_test" / "Báo cáo tài chính Kiểm toán năm 2025.pdf"
PDF_PATH_2 = ROOT_DIR / "docs" / "pdfs_test" / "SmartDocsReq.pdf"

PATHS = [
    # PDF_PATH,
    PDF_PATH_2
]
USER_INPUT = "công việc bao gồm những gì"
USER_INPUT_2 = "tóm tắt yêu cầu"
llm_structure_model = LLMPromptStructure()
build_template = (
    llm_structure_model.build_prompt_for_retrieval_query()
)  # use for create_rag_template for neo4j retrieval query
build_prompt = llm_structure_model.build_prompt(
    retrieved_chunks=RETRIEVED_CHUNKS, user_input=USER_INPUT
)
FACTORY = LLMProviderFactory(config_provider=EnvConfigProvider(), logger=Logger())
CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"
logger = Logger()
session: IConnectGraphDBSession = None  # type: ignore

# Track results
embed_results = {
    "gemini": None,
    "mistral": None,
    "ollama": None,
}

generate_results = {
    "gemini": "",
    "mistral": "",
    "ollama": "",
}

models = {
    "gemini": GEMINI_EMBEDDING_CONFIG["model"],
    "gemini_embedding": GEMINI_EMBEDDING_CONFIG["embedding_model"],
    "mistral": MISTRAL_CONFIG["model"],
    "mistral_embedding": MISTRAL_CONFIG["embedding_model"],
    "ollama": OLLAMA_CONFIG["model"],
    "ollama_embedding": OLLAMA_CONFIG["embedding_model"],
}

llm_models = {
    "gemini": None,
    "mistral": None,
    "ollama": None,
}

embedder_model = {
    "gemini": None,
    "mistral": None,
    "ollama": None,
}

errors = {
    "gemini": "",
    "mistral": "",
    "ollama": "",
}


def test_gemini():
    try:
        gemini_client = FACTORY.get_provider(EProviderName.GEMINI)
        request = ICompletionRequest(
            provider=EProviderName.GEMINI, model=models["gemini"], prompt=build_prompt
        )
        embed_request = ICompletionRequest(
            provider=EProviderName.GEMINI,
            model=models["gemini_embedding"],
            prompt=build_prompt,
        )
        generate_results["gemini"] = gemini_client.generate(request, file_caller=Path(__file__).name)
        embed_results["gemini"] = gemini_client.embedding(embed_request, file_caller=Path(__file__).name)  # type: ignore
        embedder_model["gemini"] = gemini_client.get_embedder_model(models["gemini_embedding"], file_caller=Path(__file__).name)  # type: ignore
        llm_models["gemini"] = gemini_client.get_llm_model(models["gemini"], file_caller=Path(__file__).name)  # type: ignore

    except Exception as e:
        errors["gemini"] = str(e)


def test_mistral():
    try:
        mistral_client = FACTORY.get_provider(EProviderName.MISTRAL)
        request = ICompletionRequest(
            provider=EProviderName.MISTRAL, model=models["mistral"], prompt=build_prompt
        )
        embed_request = ICompletionRequest(
            provider=EProviderName.MISTRAL,
            model=models["mistral_embedding"],
            prompt=build_prompt,
        )
        generate_results["mistral"] = mistral_client.generate(request, file_caller=Path(__file__).name)
        embed_results["mistral"] = mistral_client.embedding(embed_request, file_caller=Path(__file__).name)  # type: ignore
        embedder_model["mistral"] = mistral_client.get_embedder_model(models["mistral_embedding"], file_caller=Path(__file__).name)  # type: ignore
        llm_models["mistral"] = mistral_client.get_llm_model(models["mistral"], file_caller=Path(__file__).name)  # type: ignore
    except Exception as e:
        errors["mistral"] = str(e)


def test_ollama():
    try:
        ollama_client = FACTORY.get_provider(EProviderName.OLLAMA)
        request = ICompletionRequest(
            provider=EProviderName.OLLAMA, model=models["ollama"], prompt=build_prompt
        )
        embed_request = ICompletionRequest(
            provider=EProviderName.OLLAMA,
            model=models["ollama_embedding"],
            prompt=build_prompt,
        )
        generate_results["ollama"] = ollama_client.generate(request, file_caller=Path(__file__).name)
        embed_results["ollama"] = ollama_client.embedding(embed_request, file_caller=Path(__file__).name)  # type: ignore
        embedder_model["ollama"] = ollama_client.get_embedder_model(models["ollama_embedding"], file_caller=Path(__file__).name)  # type: ignore
        llm_models["ollama"] = ollama_client.get_llm_model(models["ollama"], file_caller=Path(__file__).name)  # type: ignore
    except Exception as e:
        errors["ollama"] = str(e)


async def run_all_tests():
    await asyncio.gather(
        asyncio.to_thread(test_gemini),
        # asyncio.to_thread(test_mistral),
        # asyncio.to_thread(test_ollama),
    )


def save_results(
    name: str,
    result: str,
    embedding_result: str = "",
    error: str = "",
    embedder_model_result: str = "",
    llm_model_result: str = "",
):
    _separator = "─" * 80
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(OUTPUT_DIR / "llm_test_results.txt", "a") as f:
        # Write separator for readability
        f.write(f"{_separator}\n")

        # Write header with timestamp and type
        f.write(f"[{timestamp}] [{name}]\n")

        # Write message with proper indentation
        f.write(f"Result:\n  {result}\n")

        # write embedding result if provided
        if embedding_result:
            f.write(f"Embedding Result:\n  {embedding_result}\n")

        if embedder_model_result:
            f.write(f"Embedder Model Result:\n  {embedder_model_result}\n")

        if llm_model_result:
            f.write(f"LLM Model Result:\n  {llm_model_result}\n")

        # Write error if provided
        if error:
            f.write(f"Error:\n  {error}\n")

        # Write end marker
        f.write(f"{_separator}\n")


# TEST NEO4J MODULES
def test_get_neo4j_session() -> IConnectGraphDBSession:
    try:
        config_provider = EnvConfigProvider()
        node_labels_config = Neo4jNodeLabelsConfig(logger)
        sess = Neo4jSession(config_provider=config_provider, metadata_dir=CURRENT_DIR, node_labels_config=node_labels_config, logger=logger)
        logger.flush()  # Ensure all logs are written before proceeding
        return sess
    except Exception as e:
        logger.error(f"Error in test_get_neo4j_session: {e}")
        raise


def test_get_neo4j_service() -> INeo4jService:
    try:
        service = session.connect(file_caller="test_get_neo4j_service")
        if (service is None) or (not isinstance(service, INeo4jService)):
            raise ValueError(
                "Failed to get a valid Neo4jService instance from the session"
            )
        logger.flush()  # Ensure all logs are written before proceeding
        return service
    except Exception as e:
        logger.error(f"Error in test_get_neo4j_service: {e}")
        raise


async def test_neo4j_service_search():
    try:
        service = test_get_neo4j_service()
        # part 1: run simple kg pipeline for file to kg conversion to ensure everything is set up correctly
        if (llm_models["gemini"] is None) or (embedder_model["gemini"] is None):
            raise ValueError(
                "Gemini LLM model and embedder model must be available for testing Neo4jService search"
            )
        print(f"llm: {llm_models['gemini']}")
        print(f"embedder: {embedder_model['gemini'].__dict__}")
        name = service.create_vector_index(index_name="demo", dimension=embedder_model["gemini"].embedding_dim, 
                                                   label="Chunk", embedding_property="embedding", similarity_fn=ESimilarityFn.COSINE)
        retriever = await service.execute_file_to_kg_pipeline(
            retrieval_query=build_template,
            index_name=name,
            file_paths=PATHS,
            llm_model=llm_models["gemini"],
            embedder=embedder_model["gemini"],
            file_caller="test_neo4j_service_search",
        )
        result = service.search(
            query_text=USER_INPUT_2,
            limit=5,
            llm=llm_models["gemini"],
            retriever=retriever,
            template=llm_structure_model.create_rag_template(),
            file_caller="test_neo4j_service_search",
        )
        logger.info("test_neo4j_service_search executed successfully.")
        logger.info(f"Search result: {result}")
        logger.flush()  # Ensure all logs are written before proceeding
    except Exception as e:
        logger.error(f"Error in test_neo4j_service_search: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
    # for provider in generate_results.keys():
    #     save_results(
    #         name=provider.capitalize(),
    #         result=generate_results[provider],
    #         embedding_result=str(embed_results[provider]),
    #         error=errors[provider],
    #         embedder_model_result=str(embedder_model[provider]),
    #         llm_model_result=str(llm_models[provider]),
    #     )
    # Run Neo4j tests
    print(f"Ex: {ERExtractionTemplate().DEFAULT_TEMPLATE}")
    try:
        session = test_get_neo4j_session()
        asyncio.run(test_neo4j_service_search())
        logger.info("test_neo4j_service_search passed successfully.")
    except Exception as e:
        logger.error(f"test_neo4j_service_search failed with error: {e}")
    finally:
        session.disconnect(file_caller="main")
        logger.flush()
