from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure

class LLMPromptStructure(ILLMPromptStructure):
    """
    This class defines the structure of prompts used for LLM interactions in the application.   
    It provides a standardized way to create prompts for different LLM providers, ensuring consistency and maintainability across the codebase.
    The prompt structure includes sections for system instructions, user input, and any additional context or constraints that may be necessary for the LLM to generate accurate and relevant responses.
    """

    def __init__(self, retrieved_chunks: list[str], user_input: str):
        self.user_input = user_input
        self.retrieved_chunks = retrieved_chunks

    def build_prompt(self) -> str:
        """
        Creates a structured prompt for LLM interactions based on the user input and retrieved chunks of information.
        The prompt is designed to provide clear instructions to the LLM, along with relevant context from the retrieved chunks, to facilitate accurate and relevant response generation.
        """
        prompt = f"""
        You are an assistant that helps answer questions based on the following retrieved information:
        
        ---------------------
        {self.retrieved_chunks}
        ---------------------

        User question: {self.user_input}

        Please provide a comprehensive answer based on the above information. 
        If the information is insufficient to answer the question, please indicate that you do not have enough information to provide an answer.
        NOT ALLOWED TO MAKE UP ANSWERS. ONLY USE THE INFORMATION PROVIDED ABOVE.
        """
        return prompt.strip()
