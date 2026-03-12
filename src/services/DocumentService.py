import os
import logging
import numpy as np
from embeddings.AbstractEmbeddingModel import AbstractEmbeddingModel
from services.VectorDBService import VectorDBService
from vo.Metadata import Metadata
from typing import Type
from vo.settings import settings
import tempfile

try:
    from google.cloud import storage
except ImportError:
    storage = None

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, embedding_model_class: Type[AbstractEmbeddingModel], vector_db_service: VectorDBService):
        self.embedding_model_class = embedding_model_class
        self.vector_db_service = vector_db_service

    def process_and_embed_directory(self, bucket_name: str):
        """
        Processes each file in a source directory, generates embeddings, saves them to the vector database,
        and then moves the processed file to a destination directory.
        The source is determined by the application environment ('gcp' or 'local').
        """
        if settings.system.app_env == 'gcp':
            self._process_files_from_gcs(bucket_name)
        else:
            self._process_files_from_local_directory(bucket_name)

    def _process_files_from_local_directory(self, bucket_name: str):
        """
        Processes files from a local directory.
        """
        source_directory = settings.file_locations.document_to_process_dir
        destination_directory = settings.file_locations.document_processed_dir
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

    def _process_files_from_gcs(self, collection_name: str):
        """
        Processes files from a GCS bucket.
        """
        if not storage:
            logger.error("Google Cloud Storage library is not installed. Please install it with 'pip install google-cloud-storage'")
            return
            
        gcs_bucket_name = settings.file_locations.gcp_bucket_name
        storage_client = storage.Client()
        bucket = storage_client.bucket(gcs_bucket_name)
        
        blobs = bucket.list_blobs()
        
        for blob in blobs:
            if not blob.name.startswith('processed/'):
                logger.info(f"Processing file from GCS: {blob.name}")
                try:
                    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
                        temp_file.write(blob.download_as_text())
                        temp_file_path = temp_file.name
                    
                    self._process_and_embed_file(temp_file_path, collection_name)
                    
                    # Move blob to processed folder
                    processed_blob_name = f"processed/{blob.name}"
                    bucket.copy_blob(blob, bucket, processed_blob_name)
                    blob.delete()
                    
                    logger.info(f"Finished processing and moved file in GCS: {blob.name} to {processed_blob_name}")
                    
                except Exception as e:
                    logger.error(f"Failed to process file {blob.name} from GCS: {e}", exc_info=True)
                finally:
                    if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                        os.remove(temp_file_path)

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
