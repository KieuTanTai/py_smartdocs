"""
Message tasks module.
Handles async RAG chat queries.
"""

from dataclasses import asdict
from pathlib import Path
from celery import Task

from backend.apps.core.enums.e_pipeline_type import EPipelineType
from backend.apps.core.enums.e_provider_name import EProviderName
from backend.apps.core.interfaces.dataclass.application.i_message_response import IChatHistoryResponse, IMessageDTO
from backend.apps.core.interfaces.dataclass.job.i_message_job import IMessageJobResponse
from backend.apps.core.interfaces.system.i_logging import ILogger
from backend.apps.interfaces.job.i_message_job import IMessageJob
from backend.apps.interfaces.tasks.i_message_task import IMessageTask
from sys_services.time_counter import TimeCounter

class MessageTask(IMessageTask):

    def __init__(self, message_job: IMessageJob, logger: ILogger, time_counter: TimeCounter):
        self.message_job = message_job
        self.logger = logger
        self.time_counter = time_counter

    @property
    def name(self) -> str:
        """Return the task name for routing."""
        return Path(__file__).stem  # Dynamic name based on filename

    def run(self, conversation_id: str, content: str, provider_name: EProviderName, pipeline_type: EPipelineType, model_name: str, embedding_model_name: str) -> IMessageJobResponse:
        self.time_counter.reset()
        self.time_counter.start()
        
        self.logger.info(f"Task Orchestrator Started for Conversation: {conversation_id}")

        # STEP 1: LẤY PARAM CONVERSATION TẠI TASK 
        conversation = self.message_job.get_conversation(conversation_id)

        # STEP 2: LƯU TIN NHẮN CỦA USER
        self.message_job.save_message(conversation, is_user_send=True, content=content)

        # STEP 3: GỌI HÀM LẤY CONTEXT TRÊN TASK
        prompt, context_hits = self.message_job.build_prompt_and_retrieve(
            content=content,
            conversation=conversation,
            provider=provider_name,
            pipeline_type=pipeline_type,
            model_name=model_name,
            embedding_model_name=embedding_model_name
        )

        # STEP 4: GỌI HÀM LLM TRÊN TASK
        assistant_content = self.message_job.generate_answer(
            provider=provider_name,
            model_name=model_name,
            prompt=prompt
        )

        # STEP 5: LƯU TIN NHẮN ASSISTANT TẠI TASK
        self.message_job.save_message(conversation, is_user_send=False, content=assistant_content)

        # CHỐT THỜI GIAN
        elapsed = self.time_counter.get_elapsed_time()
        self.logger.info(f"MessageTask End-to-End completed in {elapsed:.2f}ms")
        
        # --- RETURN RESPONSE NÀY TRÊN TASK ---
        return IMessageJobResponse(
            conversation_id=conversation_id,
            provider=provider_name.value,
            model=model_name,
            latency_ms=int(elapsed),
            mode=pipeline_type.value,
            retrieval_hits=context_hits
        )
        
    def get_history(self, conversation_id: str, limit: int = 50, offset: int = 0) -> IChatHistoryResponse:
        self.time_counter.reset()
        self.time_counter.start()
        
        self.logger.info(f"Task get_history started for: {conversation_id}")

        # 1. GỌI JOB VÀ NHẬN VỀ KIỂU DỮ LIỆU PYTHON THUẦN (SẠCH)
        title = self.message_job.get_conversation_title(conversation_id)
        formatted_messages = self.message_job.get_messages(conversation_id, limit, offset)
        total_messages = self.message_job.count_messages(conversation_id)

        # 2. CHỐT THỜI GIAN
        elapsed = self.time_counter.get_elapsed_time()
        self.logger.info(f"Task get_history completed in {elapsed:.2f}ms")

        # 3. ĐÓNG GÓI TRẢ CHO APPLICATION
        return IChatHistoryResponse(
            conversation_id=str(conversation_id),
            conversation_title=title,
            messages=formatted_messages, # Đã là List[IMessageDTO] từ Job đưa lên
            count=len(formatted_messages),
            total=total_messages
        )