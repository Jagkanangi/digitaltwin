from vectordb.VectorDBFactory import get_vectordb
from vectordb.AbstractDataWrapper import AbstractDataWrapper
from embeddings.OpenAIEmbeddingModel import OpenAIEmbeddingModel
import logging

# Initialize logger for the Vector DB Service
logger = logging.getLogger(__name__)

class VectorDBService():
    """
    VectorDBService acts as the high-level API for all vector-related operations.
    
    ARCHITECTURAL ROLE: Retrieval Engine
    This service is a core component of the RAG (Retrieval-Augmented Generation) pipeline.
    It abstracts the complexities of embedding generation and vector similarity search.
    
    DESIGN PATTERN: Factory Pattern
    It uses 'get_vectordb()' to instantiate a database connector without knowing
    the specific implementation (e.g., ChromaDB, Pinecone), adhering to the
    Dependency Inversion Principle.
    """
    def __init__(self):
        try:
            # Dynamically get the configured database instance via factory
            self.db = get_vectordb()
            logger.info("VectorDB instance retrieved successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize VectorDB: {e}", exc_info=True)
            raise

    def get_db_wrapper(self, bucket_name: str) -> AbstractDataWrapper:
        """
        DESIGN PATTERN: Data Access Object (DAO) / Wrapper
        
        Retrieves a 'wrapper' that provides a simplified interface for a specific 
        collection (bucket) within the vector database.
        
        Args:
            bucket_name (str): The name of the collection/index.
        """
        try:
            db_wrapper : AbstractDataWrapper = self.db.get_db_wrapper()
            # Initialize the bucket (create if not exists)
            db_wrapper.init_bucket(self.db.get_connection(), bucket_name)
            logger.info(f"DB wrapper initialized for bucket: {bucket_name}")
            return db_wrapper
        except Exception as e:
            logger.error(f"Error getting DB wrapper for bucket {bucket_name}: {e}", exc_info=True)
            raise
    
    def query(self, rag_text: str, bucket_name:str):
        """
        Executes the RAG query flow.
        
        FLOW:
        1. Generate embedding for the input text using OpenAI.
        2. Initialize the database wrapper for the target bucket.
        3. Perform vector similarity search.
        4. Concatenate results into a single context string.
        """
        try:
            # 1. Embedding Generation
            embedding_model = OpenAIEmbeddingModel()
            query_embedding = embedding_model.get_embedding(rag_text)

            # 2. Vector Search
            db_wrapper = self.get_db_wrapper(bucket_name)
            search_results = db_wrapper.search([query_embedding])

            # 3. Context Synthesis
            if search_results:
                result_text = "Context : "
                for result in search_results:
                    result_text += result.document + "\n"
                logger.info(f"Query successful for bucket {bucket_name}. Found {len(search_results)} results.")
                return result_text
            
            logger.info(f"Query returned no results for bucket {bucket_name}.")
            return None
        except Exception as e:
            logger.error(f"Error querying vector DB for bucket {bucket_name}: {e}", exc_info=True)
            return None

    

