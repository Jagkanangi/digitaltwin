import os
from typing import List

from .AbstractEmbeddingModel import AbstractEmbeddingModel
from chonkie.embeddings import OpenAIEmbeddings
from chonkie import Pipeline
from chonkie.chunker import SemanticChunker
from utils.SystemConfig import config
class ChonkieSemanticEmbedding(AbstractEmbeddingModel):
    """
    A class for performing semantic text chunking using Chonkie's SemanticChunker.

    This class extends AbstractEmbeddingModel and is specialized for breaking down
    large texts into semantically related chunks. It uses an embedding model to
    understand the meaning of sentences and groups them based on cosine similarity.
    This is particularly useful for preparing text for Retrieval-Augmented Generation (RAG)
    systems where chunk coherence is important for context quality.
    """
    _chunking_model = config.system.models.chunking_model
    def __init__(self,
                 file_name : str | None = None,
                 directory_name : str | None = None,
                 text_to_chunk : str | None = None,
                 threshold: float = 0.5,
                 chunk_size: int = 2048,
                 similarity_window: int = 3,
                 min_sentences_per_chunk: int = 5,
                 model_name: str = config.system.models.embedding_model):
        """
        Initializes the ChonkieSemanticEmbedding instance.

        Args:
            file_name: The path to a single file to be processed.
            dir_name: The path to a directory of files to be processed.
            text: A string of text to be processed.
            threshold: The cosine similarity threshold for merging sentences.
                       Sentences with similarity above this value are grouped.
            chunk_size: The maximum number of tokens allowed in a chunk.
            similarity_window: The number of preceding sentences to compare against
                               for semantic similarity.
            min_sentences_per_chunk: The minimum number of sentences required in a chunk.
            model_name: The name of the OpenAI embedding model to use for semantic analysis.
        """
        super().__init__(file_name=file_name, directory_name= directory_name, text_to_chunk=text_to_chunk, model_name=model_name)
        self.threshold = threshold
        self.chunk_size = chunk_size
        self.similarity_window = similarity_window
        self.min_sentences_per_chunk = min_sentences_per_chunk
        self.initialize_client()

    def initialize_client(self):
        """
        Initializes the OpenAI client for Chonkie using the API key from environment variables.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self._embed_model = OpenAIEmbeddings(api_key=api_key, model=self.model_name)

    def configure_chunker_for_pipeline(self, pipeline):
        """
        Configures the Chonkie pipeline to use the SemanticChunker with the specified parameters.

        This method adds the SemanticChunker to the pipeline, which will handle the
        core logic of splitting text based on semantic similarity.
        """
        pipeline.chunk_with(SemanticChunker.__name__,
                                                 threshold = self.threshold,
                                                 chunk_size = self.chunk_size,
                                                 min_sentences_per_chunk = self.min_sentences_per_chunk,
                                                 similarity_window = self.similarity_window,
                                                 embedding_model = self._chunking_model)