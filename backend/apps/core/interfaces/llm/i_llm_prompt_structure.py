from abc import ABC, abstractmethod

class ILLMPromptStructure(ABC):
    @abstractmethod
    def __init__(self, retrieved_chunks: list[str], user_input: str):
        pass

    @abstractmethod
    def build_prompt(self) -> str:
        pass