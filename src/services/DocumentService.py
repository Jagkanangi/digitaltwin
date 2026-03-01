import os
import logging
import numpy as np
from embeddings.AbstractEmbeddingModel import AbstractEmbeddingModel
from services.VectorDBService import VectorDBService
from vo.Metadata import Metadata
from typing import Type
from utils.SystemConfig import config

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, embedding_model_class: Type[AbstractEmbeddingModel], vector_db_service: VectorDBService):
        self.embedding_model_class = embedding_model_class
        self.vector_db_service = vector_db_service

    def process_and_embed_directory(self, bucket_name: str):
        """
        Processes each file in a source directory, generates embeddings, saves them to the vector database,
        and then moves the processed file to a destination directory.
        """
        source_directory = config.system.file_locations.document_to_process_dir
        destination_directory = config.system.file_locations.document_processed_dir
        os.makedirs(source_directory, exist_ok=True)
        os.makedirs(destination_directory, exist_ok=True)

        for file_name in os.listdir(source_directory):
            source_path = os.path.join(source_directory, file_name)
            destination_path = os.path.join(destination_directory, file_name)

            if os.path.isfile(source_path):
                logger.info(f"Processing file: {file_name}")
                try:
                    self._process_and_embed_file(source_path, bucket_name)
                    os.rename(source_path, destination_path)
                    logger.info(f"Finished processing and moved file: {file_name}")
                except Exception as e:
                    logger.error(f"Failed to process file {file_name}: {e}", exc_info=True)

    def _process_and_embed_file(self, file_path: str, collection_name: str):
        """
        Processes a single file, generates embeddings, and saves them to the vector database.
        """
        embedding_model = self.embedding_model_class(file_name=file_path, directory_name=None, text_to_chunk=None)
        documents = embedding_model.get_embeddings()
        
        texts = [chunk.text for doc in documents for chunk in doc.chunks if chunk.embedding is not None]
        embeddings = []
        for doc in documents:
            for chunk in doc.chunks:
                if chunk.embedding is not None:
                    if isinstance(chunk.embedding, np.ndarray):
                        embeddings.append(chunk.embedding.tolist())
                    else:
                        embeddings.append(chunk.embedding)

        metadatas = [Metadata.model_validate(doc.metadata) for doc in documents for chunk in doc.chunks if chunk.embedding is not None and doc.metadata]
        
        if texts:
            db_wrapper = self.vector_db_service.get_db_wrapper(collection_name)
            db_wrapper.add(texts=texts, embeddings=embeddings, metadatas=metadatas)
