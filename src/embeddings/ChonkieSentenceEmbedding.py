import os
from typing import List, Union, Optional, Literal

from .AbstractEmbeddingModel import AbstractEmbeddingModel
from chonkie.embeddings import OpenAIEmbeddings
from chonkie import Pipeline
from chonkie.chunker import SentenceChunker
class ChonkieSentenceEmbedding(AbstractEmbeddingModel):
    """
    A class for performing sentence-based text chunking using Chonkie's SentenceChunker.

    This class extends AbstractEmbeddingModel and is designed for splitting text into
    chunks based on a fixed number of sentences or tokens. It provides a straightforward,
    rule-based approach to chunking, which can be faster than semantic chunking when
    deep contextual understanding is not necessary.
    """
    def __init__(
        self,
        file_name : str | None,
        dir_name : str | None,
        text : str | None,
        chunk_size: int = 2048,
        chunk_overlap: int = 200,
        min_sentences_per_chunk: int = 1,
        min_characters_per_sentence: int = 12,
        model_name: str = "text-embedding-3-small"):
        """
        Initializes the ChonkieSentenceEmbedding instance.

        Args:
            file_name: The path to a single file to be processed.
            dir_name: The path to a directory of files to be processed.
            text: A string of text to be processed.
            chunk_size: The maximum number of tokens allowed in a chunk.
            chunk_overlap: The number of tokens to overlap between consecutive chunks.
                           This helps maintain context across chunk boundaries.
            min_sentences_per_chunk: The minimum number of sentences required in a chunk.
            min_characters_per_sentence: The minimum number of characters for a sentence to be considered valid.
            model_name: The name of the OpenAI model to use (for client initialization, though not for chunking logic itself).
        """

        super().__init__(file_name=file_name, directory_name= dir_name, text_to_chunk=text, model_name=model_name)
        self.chunk_size = chunk_size
        self.min_sentences_per_chunk = min_sentences_per_chunk
        self.min_characters_per_sentence = min_characters_per_sentence
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
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
        Configures the Chonkie pipeline to use the SentenceChunker with the specified parameters.

        This method adds the SentenceChunker to the pipeline, which will split the text
        based on sentence boundaries and token counts.
        """
        pipeline.chunk_with(SentenceChunker.__name__,
                                                chunk_overlap = self.chunk_overlap,
                                                 chunk_size = self.chunk_size,
                                                 min_sentences_per_chunk = self.min_sentences_per_chunk,
                                                 min_characters_per_sentence = self.min_characters_per_sentence)
    