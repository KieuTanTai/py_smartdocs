from abc import ABC, abstractmethod
from neo4j_graphrag.generation.prompts import RagTemplate
class ILLMPromptStructure(ABC):
    @abstractmethod
    def build_prompt(self, retrieved_chunks: list[str], user_input: str) -> str:
        """
        Creates a structured prompt for LLM interactions based on the user input and retrieved chunks of information.
        The prompt is designed to provide clear instructions to the LLM, along with relevant context from the retrieved chunks, to facilitate accurate and relevant response generation.
        :param retrieved_chunks: A list of strings representing the retrieved chunks of information relevant to the user's query.
        :param user_input: The user's input or question that the LLM needs to respond to.
        :return: The structured prompt as a string.
        """
        pass

    @abstractmethod
    def build_prompt_for_multiple_file(self, dict_retrieved_chunks: dict[str, list[str]], user_input: str) -> str:
        """
        Creates a structured prompt for LLM interactions based on multiple files.
        :param dict_retrieved_chunks: A dictionary mapping file names to lists of retrieved chunks from each file.
        :param user_input: The user's input or question that the LLM needs to respond to.
        :return: The structured prompt as a string.
        """
        pass

    @abstractmethod
    def build_prompt_for_retrieval_query(self) -> str:
        """
        Creates a structured prompt for LLM interactions based on a retrieval query.
        :return: The structured prompt as a string.
        """
        pass

    @abstractmethod
    def create_rag_template(self) -> RagTemplate:
        """
        Creates a RAG template with the specified template string and expected inputs.  
        You can use this method to create a RAG template that defines the structure of the prompt to be used for retrieval-augmented generation, based on the specific requirements of your application and the expected inputs for the template.
        :return: A RagTemplate object that can be used to generate prompts for retrieval-augmented generation.
         """
        pass
