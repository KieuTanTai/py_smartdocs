import time

from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IGraphTimeCounterResponse, IRetrievalTimeCounterResponse, ITimeCounterResponse
from backend.apps.core.interfaces.system.i_time_counter import ITimeCounter

class TimeCounter(ITimeCounter):
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.end_time = time.perf_counter()

    def get_elapsed_time(self):
        if self.start_time is None:
            raise ValueError("Timer has not been started.")

        if self.end_time is not None:
            return self.end_time - self.start_time

        return time.perf_counter() - self.start_time

    def reset(self):
        self.start_time = None
        self.end_time = None

    def mapping_to_time_counter_response(self, extract_time: float, chunk_time: float, embedding_time: float, save_time: float, query_time: float = 0.0) -> ITimeCounterResponse:
        total_time = extract_time + chunk_time + embedding_time + save_time + query_time
        return ITimeCounterResponse(
            extract_time=extract_time,
            chunk_time=chunk_time,
            embedding_time=embedding_time,
            save_time=save_time,
            query_time=query_time,
            total_time=total_time
        )

    def mapping_to_graph_time_counter_response(self, extract_time: float, chunk_time: float, graph_retriever_time: float, query_time: float = 0.0) -> IGraphTimeCounterResponse:
        total_time = extract_time + chunk_time + graph_retriever_time + query_time
        return IGraphTimeCounterResponse(
            extract_time=extract_time,
            chunk_time=chunk_time,
            graph_retriever_time=graph_retriever_time,
            total_time=total_time,
            query_time=query_time
        )

    def mapping_to_retrieval_time_counter_response(self, retrieval_time: float, query_time: float) -> IRetrievalTimeCounterResponse:
        total_time = retrieval_time + query_time
        return IRetrievalTimeCounterResponse(
            retrieval_time=retrieval_time,
            query_time=query_time,
            total_time=total_time
        )
