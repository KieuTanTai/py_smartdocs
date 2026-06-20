from abc import ABC, abstractmethod

from backend.apps.core.interfaces.dataclass.response.i_conversation_response import IGraphTimeCounterResponse, IRetrievalTimeCounterResponse, ITimeCounterResponse

class ITimeCounter(ABC):
    @abstractmethod
    def start(self) -> None:
        """
        Start the time counter.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        Stop the time counter.
        If you just want to get elapsed time, you can call get_elapsed_time() directly without calling stop() because get_elapsed_time() will call stop() internally.
        """
        pass

    @abstractmethod
    def get_elapsed_time(self) -> float:
        """
        Get the elapsed time in seconds.
        call stop() before calling this method to ensure accurate timing. If stop() is not called, this method will call stop() 
        internally to calculate the elapsed time up to the current moment.
        Returns:
            float: The elapsed time in seconds.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the time counter to its initial state.
        This can be useful if you want to reuse the same time counter instance for multiple measurements.
        """
        pass

    @abstractmethod
    def mapping_to_retrieval_time_counter_response(self, retrieval_time: float, query_time: float) -> IRetrievalTimeCounterResponse:
        """
        Map the recorded time values to an IRetrievalTimeCounterResponse dataclass instance.
        This method should take the recorded time values (e.g., retrieval_time, query_time) and return an instance of IRetrievalTimeCounterResponse with these values populated.
        Returns:
            IRetrievalTimeCounterResponse: An instance of IRetrievalTimeCounterResponse containing the recorded time values.
        """
        pass

    @abstractmethod
    def mapping_to_graph_time_counter_response(self, extract_time: float, chunk_time: float, graph_retriever_time: float, query_time: float = 0.0) -> IGraphTimeCounterResponse:
        """
        Map the recorded time values to an IGraphTimeCounterResponse dataclass instance.
        This method should take the recorded time values (e.g., extract_time, chunk_time, graph_retriever_time, total_time, query_time) and return an instance of IGraphTimeCounterResponse with these values populated.
        Returns:
            IGraphTimeCounterResponse: An instance of IGraphTimeCounterResponse containing the recorded time values.
        """
        pass

    @abstractmethod
    def mapping_to_time_counter_response(self, extract_time: float, chunk_time: float, embedding_time: float, save_time: float, query_time: float = 0.0) -> ITimeCounterResponse:
        """
        Map the recorded time values to an ITimeCounterResponse dataclass instance.
        This method should take the recorded time values (e.g., extract_time, chunk_time, embedding_time, save_time, query_time) and return an instance of ITimeCounterResponse with these values populated.
        Returns:
            ITimeCounterResponse: An instance of ITimeCounterResponse containing the recorded time values.
        """
        pass