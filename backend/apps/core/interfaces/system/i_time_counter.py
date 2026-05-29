from abc import ABC, abstractmethod

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
        call stop() before calling this method to ensure accurate timing. If stop() is not called, this method will call stop() internally to calculate the elapsed time up to the current moment.
        Returns:
            float: The elapsed time in seconds.
        """
        pass