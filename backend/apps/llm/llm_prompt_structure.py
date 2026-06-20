from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from neo4j_graphrag.generation.prompts import RagTemplate

class LLMPromptStructure(ILLMPromptStructure):
    """
    This Singleton class defines the structure of prompts used for LLM interactions in the application.
    It provides a standardized way to create prompts for different LLM providers, ensuring consistency and maintainability across the codebase.
    The prompt structure includes sections for system instructions, user input, and any additional context or constraints that may be necessary for the LLM to generate accurate and relevant responses.
    """
    def __init__(self):
        pass

    def build_init_processed_prompt(self, user_input: str) -> str:
        """
        Creates a structured prompt for LLM interactions based on the user input and retrieved chunks of information.
        The prompt is designed to provide clear instructions to the LLM, along with relevant context from the retrieved chunks, to facilitate accurate and relevant response generation.
        :param user_input: The user's input or question that the LLM needs to respond to.
        :return: The structured prompt as a string.
        """
        prompt = f"""
        You are an assistant that helps answer questions based on the following retrieved information, now just the user input is provided (maybe file paths that have been uploaded), no retrieved information is available:
        
        ---------------------
        {user_input}
        ---------------------

        Please provide a comprehensive answer based on the above information. 
        If the information is insufficient to answer the question, please indicate that you do not have enough information to provide an answer.
        NOT ALLOWED TO MAKE UP ANSWERS. ONLY USE THE INFORMATION PROVIDED ABOVE.
        """
        return prompt.strip()

    def build_summary_prompt(self, user_input: str) -> str:
        """
        Creates a structured prompt for LLM interactions based on the user input and retrieved chunks of information.
        The prompt is designed to provide clear instructions to the LLM, along with relevant context from the retrieved chunks, to facilitate accurate and relevant response generation.
        """
        prompt = f"""
        You are an assistant that helps answer questions based on the following retrieved information:
        
        ---------------------
        {user_input}
        ---------------------

        Please provide a comprehensive answer based on the above information. 
        If the information is insufficient to answer the question, please indicate that you do not have enough information to provide an answer.
        NOT ALLOWED TO MAKE UP ANSWERS. ONLY USE THE INFORMATION PROVIDED ABOVE.
        """
        return prompt.strip()

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

    # * This method is used to build a prompt for a single file, which is then called by the public build_prompt_for_multiple_file method to create prompts for multiple files. It formats the retrieved chunks and user input in a structured way for the LLM to process.


    def build_prompt_for_retrieval_query(self) -> str:
        prompt = """
            // GraphRAG retrieval policy

            // Seed
            WITH node AS chunk

            // Document boundary constraint (optional runtime param)
            WHERE chunk.document_id IN $document_ids

            // 2-hop entity expansion
            MATCH (chunk)<-[:FROM_CHUNK]-(entity)-[relList:!FROM_CHUNK]-(nb)
            WHERE nb.document_id IN $document_ids

            UNWIND relList AS rel

            // aggregation
            WITH collect(DISTINCT chunk) AS chunks,
                collect(DISTINCT rel) AS rels

            RETURN
            apoc.text.join([c in chunks | c.text], '\n') +
            apoc.text.join([r in rels |
            startNode(r).name + ' - ' + type(r) + ' ' +
            coalesce(r.details,'') + ' -> ' + endNode(r).name
            ], '\n') AS info
        """
        return prompt.strip()
    def create_rag_template(self) -> RagTemplate:
        return RagTemplate(
            template="""
        You are an assistant that helps answer questions based on the following retrieved information:
        
        ---------------------
        {context}
        ---------------------

        User question: {query_text}

        Please provide a comprehensive answer based on the above information. 
        If the information is insufficient to answer the question, please indicate that you do not have enough information to provide an answer.
        NOT ALLOWED TO MAKE UP ANSWERS. ONLY USE THE INFORMATION PROVIDED ABOVE.
        """,
            expected_inputs=["context", "query_text"],
        )

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
