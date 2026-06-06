from abc import ABC, abstractmethod

class ILLMPromptStructure(ABC):
    @abstractmethod
    def build_prompt(self, retrieved_chunks: list[str], user_input: str) -> str:
        pass

    @abstractmethod
    def build_prompt_for_multiple_file(self, dict_retrieved_chunks: dict[str, list[str]], user_input: str) -> str:
        pass