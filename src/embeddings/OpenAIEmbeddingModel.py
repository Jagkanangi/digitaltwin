import os
import openai as client
from typing import List
import logging

logger = logging.getLogger(__name__)

class OpenAIEmbeddingModel():
    def __init__(self, model_name="text-embedding-3-small", model_key="", model_role_type=""):
        super().__init__()
        self.model_name = model_name
        self.model_key = model_key
        self.model_role_type = model_role_type
        self.initialize_client()

    def initialize_client(self):
        """
        Initializes the OpenAI client.
        """
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.error("OPENAI_API_KEY environment variable not set.")
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            client.api_key = api_key
            logger.info("OpenAI client initialized for embeddings.")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            raise

    def is_chonkie(self) -> bool:
        return False
    def get_embedding(self, text: str) -> List[float]:
        """
        Gets an embedding from the OpenAI API.
        """
        try:
            response = client.embeddings.create(
                model=self.model_name,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding from OpenAI: {e}", exc_info=True)
            raise
