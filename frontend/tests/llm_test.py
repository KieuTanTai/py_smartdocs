"""
Test requests to all 3 LLM providers: Gemini, Mistral, and Ollama
"""

import asyncio
import datetime
from pathlib import Path
from backend.apps.core.interfaces.system.i_config import IConfigProvider
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.services.chat.i_completion import (
    ICompletionRequest,
    ICompletionResponse,
    IEmbeddingResponse,
)
from backend.apps.llm.llm_provider_factory import LLMProviderFactory
from sys_services.enums.e_provider_name import EProviderName
from sys_services.logging import DEFAULT_LOGGER
from sys_services.read_config.config_provider import DEFAULT_CONFIG_PROVIDER
from sys_services.read_config.read_gemini_config import GEMINI_EMBEDDING_CONFIG
from sys_services.read_config.read_mistral_config import MISTRAL_CONFIG
from sys_services.read_config.read_ollama_config import OLLAMA_CONFIG

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


USER_INPUT = "công việc bao gồm những gì"
TEST_PROMPT = f"""
        You are an assistant that helps answer questions based on the following retrieved information:
        
        ---------------------
        {RETRIEVED_CHUNKS}
        ---------------------

        User question: {USER_INPUT}

        Please provide a comprehensive answer based on the above information. 
        If the information is insufficient to answer the question, please indicate that you do not have enough information to provide an answer.
        NOT ALLOWED TO MAKE UP ANSWERS. ONLY USE THE INFORMATION PROVIDED ABOVE.
        """
FACTORY = LLMProviderFactory(config_provider=DEFAULT_CONFIG_PROVIDER, logger=DEFAULT_LOGGER)
CURRENT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = CURRENT_DIR / "output"

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

errors = {
    "gemini": "",
    "mistral": "",
    "ollama": "",
}

def test_gemini():
    try:
        gemini_client = FACTORY.get_provider(EProviderName.GEMINI)
        request = ICompletionRequest(provider=EProviderName.GEMINI, model=models["gemini"], prompt=TEST_PROMPT)
        embed_request = ICompletionRequest(provider=EProviderName.GEMINI, model=models["gemini_embedding"], prompt=TEST_PROMPT)
        generate_results["gemini"] = gemini_client.generate(request)
        embed_results["gemini"] = gemini_client.embedding(embed_request)

    except Exception as e:
        errors["gemini"] = str(e)

def test_mistral():
    try:
        mistral_client = FACTORY.get_provider(EProviderName.MISTRAL)
        request = ICompletionRequest(provider=EProviderName.MISTRAL, model=models["mistral"], prompt=TEST_PROMPT)
        embed_request = ICompletionRequest(provider=EProviderName.MISTRAL, model=models["mistral_embedding"], prompt=TEST_PROMPT)
        generate_results["mistral"] = mistral_client.generate(request)
        embed_results["mistral"] = mistral_client.embedding(embed_request)
    except Exception as e:
        errors["mistral"] = str(e)

def test_ollama():
    try:
        ollama_client = FACTORY.get_provider(EProviderName.OLLAMA)
        request = ICompletionRequest(provider=EProviderName.OLLAMA, model=models["ollama"], prompt=TEST_PROMPT)
        embed_request = ICompletionRequest(provider=EProviderName.OLLAMA, model=models["ollama_embedding"], prompt=TEST_PROMPT)
        generate_results["ollama"] = ollama_client.generate(request)
        embed_results["ollama"] = ollama_client.embedding(embed_request)
    except Exception as e:
        errors["ollama"] = str(e)

async def run_all_tests():
    await asyncio.gather(
        asyncio.to_thread(test_gemini),
        asyncio.to_thread(test_mistral),
        asyncio.to_thread(test_ollama),
    )

def save_results(name: str, result: str, embedding_result: str = "", error: str = ""):
    _separator = "─" * 80
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(OUTPUT_DIR / "llm_test_results.txt", "a") as f:
        # Write separator for readability
        f.write(f"{_separator}\n")

        # Write header with timestamp and type
        f.write(f"[{timestamp}] [{name}]\n")

        # Write message with proper indentation
        f.write(f"Result:\n  {result}\n")

        #write embedding result if provided
        if embedding_result:
            f.write(f"Embedding Result:\n  {embedding_result}\n")

        # Write error if provided
        if error:
            f.write(f"Error:\n  {error}\n")

        # Write end marker
        f.write(f"{_separator}\n")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
    for provider in generate_results.keys():
        save_results(
            name=provider.capitalize(),
            result=generate_results[provider],
            embedding_result=str(embed_results[provider]),
            error=errors[provider],
        )
