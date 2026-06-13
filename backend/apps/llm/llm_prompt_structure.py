from backend.apps.core.interfaces.llm.i_llm_prompt_structure import ILLMPromptStructure
from neo4j_graphrag.generation.prompts import RagTemplate

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

    # * This method is used to build a prompt for a single file, which is then called by the public build_prompt_for_multiple_file method to create prompts for multiple files. It formats the retrieved chunks and user input in a structured way for the LLM to process.
    def build_prompt_for_retrieval_query(self) -> str:
        """
        Creates a structured prompt for LLM interactions based on a retrieval query.
        This prompt will include instructions for the LLM to generate a Cypher query based on the provided natural language query, along with any necessary constraints or guidelines to ensure the generated query is accurate and relevant.
        """
        prompt = """
            //1) Go out 2-3 hops in the entity graph and get relationships
            WITH node AS chunk
            MATCH (chunk)<-[:FROM_CHUNK]-(entity)-[relList:!FROM_CHUNK]-{1,2}(nb)
            UNWIND relList AS rel

            //2) collect relationships and text chunks
            WITH collect(DISTINCT chunk) AS chunks, collect(DISTINCT rel) AS rels

            //3) format and return context
            RETURN apoc.text.join([c in chunks | c.text], '\n') +
            apoc.text.join([r in rels |
            startNode(r).name+' - '+type(r)+' '+r.details+' -> '+endNode(r).name],
            '\n') AS info
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
