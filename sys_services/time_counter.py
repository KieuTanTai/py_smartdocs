import time

class TimeCounter:
    def __init__(self):
        self.start_time = None
        self.end_time = None
        
    @classmethod
    def start(cls):
        instance = cls()
        instance.start_time = time.perf_counter()
        return instance

    @classmethod
    def __stop(cls, instance):
        instance.end_time = time.perf_counter()

    @classmethod
    def elapsed_ms(cls, instance) -> float:
        cls.__stop(instance)
        if instance.start_time is None or instance.end_time is None:
            raise ValueError("Timer has not been started and stopped properly.")
        return (instance.end_time - instance.start_time) * 1000