from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure

class LLMPromptStructure(ILLMPromptStructure):
    """
    This Singleton class defines the structure of prompts used for LLM interactions in the application.   
    It provides a standardized way to create prompts for different LLM providers, ensuring consistency and maintainability across the codebase.
    The prompt structure includes sections for system instructions, user input, and any additional context or constraints that may be necessary for the LLM to generate accurate and relevant responses.
    """

    def build_prompt(self, retrieved_chunks: list[str], user_input: str) -> str:
        """
        Creates a structured prompt for LLM interactions based on the user input and retrieved chunks of information.
        The prompt is designed to provide clear instructions to the LLM, along with relevant context from the retrieved chunks, to facilitate accurate and relevant response generation.
        """
        prompt = f"""
        You are an assistant that helps answer questions based on the following retrieved information:
        
        ---------------------
        {retrieved_chunks}
        ---------------------

        User question: {user_input}

        Please provide a comprehensive answer based on the above information. 
        If the information is insufficient to answer the question, please indicate that you do not have enough information to provide an answer.
        NOT ALLOWED TO MAKE UP ANSWERS. ONLY USE THE INFORMATION PROVIDED ABOVE.
        """
        return prompt.strip()

    def build_prompt_for_multiple_file(self, dict_retrieved_chunks: dict[str, list[str]], user_input: str) -> str:
        """
        Creates a structured prompt for LLM interactions based on multiple files.
        This will call the private __build_prompt_for_single_file method for each file and combine the results into a single prompt.
        """
        merged_prompt = ""
        for file_name, retrieved_chunks in dict_retrieved_chunks.items():
            merged_prompt += self.__build_prompt_for_single_file(file_name, retrieved_chunks, user_input) + "\n\n"

        prompt = f"""
        You are an assistant that helps answer questions based on the following retrieved information from multiple files:
        
        ---------------------
        {merged_prompt}
        ---------------------

        User question: {user_input}

        Please provide a comprehensive answer based on the above information. 
        If the information is insufficient to answer the question, please indicate that you do not have enough information to provide an answer.
        NOT ALLOWED TO MAKE UP ANSWERS. ONLY USE THE INFORMATION PROVIDED ABOVE.
        """
        return prompt.strip()

    def __build_prompt_for_single_file(self, file_name: str, retrieved_chunks: list[str], user_input: str) -> str:
        """
        Private method to create a structured prompt for a single file.
        This method is called by the public build_prompt method to generate the prompt for each file.
        """
        prompt = f"""
        file {file_name}:
        ---------------------
        {retrieved_chunks}
        ---------------------
        User question: {user_input}

        end question for file {file_name}
        """
        return prompt.strip()
