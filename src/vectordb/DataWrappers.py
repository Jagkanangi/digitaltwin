# DESIGN RATIONALE:
# The AbstractDBWrapper and its concrete implementations (e.g., ChromaDBWrapper) follow the
# Data Access Object (DAO) pattern. The primary goal is to abstract the underlying vector
# database technology from the rest of the application.

import uuid
from chromadb.api.types import QueryResult
from src.vo.Metadata import Metadata
from src.vo.Models import SearchResult
from typing import List, cast
from abc import ABC, abstractmethod
from .AbstractDataWrapper import AbstractDataWrapper
from chromadb.api import ClientAPI
from chromadb.api.models.Collection import Collection 
from .buckets.Buckets import Bucket, ChromaBucket
import logging
from utils.SystemConfig import config

# Logger for the Chroma Data Wrapper
logger = logging.getLogger(__name__)


class ChromaDataWrapper(AbstractDataWrapper):
    """
    ChromaDataWrapper is the concrete DAO for ChromaDB.
    
    This class handles the mapping between application-specific data models
    (Pydantic objects) and database-specific formats (Chroma lists/dicts).
    """

    def __init__(self):
        """
        Initializes the wrapper. The collection is lazy-loaded via init_bucket.
        """
        self._collection : Collection | None = None

    def init_bucket(self, connection : ClientAPI, bucket_name: str):
        """
        Connects this wrapper to a specific ChromaDB collection.
        
        Args:
            connection: The raw Chroma HttpClient instance.
            bucket_name: The name of the collection.
        """
        self._collection = connection.get_or_create_collection(name=bucket_name)

    def get_bucket(self) -> ChromaBucket:
        """
        Returns a simplified Bucket interface for the active collection.
        """
        if self._collection is None:
            raise RuntimeError("Bucket has not been initialized. Call init_bucket() first.")
        return ChromaBucket(self._collection)

    def add(self, texts: List[str], embeddings : List[list[float]], metadatas: List[Metadata] | None = None) -> List[str]:
        """
        Adds documents and their vector embeddings to ChromaDB.
        
        ARCHITECTURAL DETAIL: Unique ID Generation
        We use UUID v4 to ensure globally unique identifiers for every document chunk,
        enabling idempotent updates and precise deletions.
        """
        ids = [str(uuid.uuid4()) for _ in texts]
        chroma_metadatas = []
        if metadatas:
            for m in metadatas:
                # 1. Get the raw dictionary from Pydantic
                meta_dict = m.model_dump()
                
                # 2. DESIGN: DEFENSIVE SERIALIZATION
                # ChromaDB 0.5.x has a strict schema where metadata values MUST be 
                # strings, ints, floats, or bools. Lists/Dicts are not allowed.
                # We automatically stringify any list to maintain compatibility.
                for key, value in meta_dict.items():
                    if isinstance(value, list):
                        meta_dict[key] = ",".join(map(str, value))
                
                chroma_metadatas.append(meta_dict)
        
        if(self._collection is not None ):
            try:
                # Executing the bulk add operation
                self._collection.add(
                    embeddings=cast(List[list[float]], embeddings),
                    documents=texts,
                    metadatas=chroma_metadatas or None,
                    ids=ids
                )
                logger.info(f"Successfully added {len(texts)} documents to collection.")
            except Exception as e:
                logger.error(f"Error adding documents to ChromaDB: {e}", exc_info=True)
                raise
        else:
            logger.error("ChromaDB collection not initialized. Call init_bucket() first.")
            raise RuntimeError("ChromaDB collection not initialized. Call init_bucket() first.")
        return ids

    def search(self, query_text_embeddings: List[float]) -> List[SearchResult]:
        """
        Performs vector similarity search.
        
        FLOW:
        1. Query Chroma using the provided vector embedding.
        2. Flatten the nested results returned by Chroma.
        3. Validate and transform each result into a SearchResult Pydantic model.
        """
        if self._collection is None:
            logger.error("ChromaDB collection not initialized. Call init_bucket() first.")
            raise RuntimeError("ChromaDB collection not initialized. Call init_bucket() first.")
        
        n_results: int = config.db_retrieval.nn_count
        try:
            # Querying the database
            results: QueryResult = self._collection.query( # type: ignore
                query_embeddings=query_text_embeddings,
                n_results=n_results,
                include=["distances", "documents"]
            )

            if not results or not results['documents']:
                return []

            # Step 2: Result Flattening and Transformation
            # Chroma returns lists of lists; we flatten this to a single list of SearchResults.
            num_queries = len(results['ids'])
            search_results = []
            logger.info("--- Search Result Distances ---")
            for i in range(num_queries):
                ids_for_query = results['ids'][i]
                docs_for_query = results['documents'][i] if results.get('documents') and i < len(results['documents']) else [None] * len(ids_for_query)
                meta_for_query = results['metadatas'][i] if results.get('metadatas') and i < len(results['metadatas']) else [None] * len(ids_for_query)
                dist_for_query = results['distances'][i] if results.get('distances') and i < len(results['distances']) else [None] * len(ids_for_query)

                for id_val, doc, meta, dist in zip(ids_for_query, docs_for_query, meta_for_query, dist_for_query, strict=True):
                    item = {
                        'id': id_val,
                        'document': doc,
                        'metadata': meta,
                        'distance': dist,
                    }
                    logger.info(f"Doc: {item['document'][:50]}... -> Distance: {dist}")
                    if(dist < config.db_retrieval.distance_threshold):
                        search_results.append(SearchResult.model_validate(item))
            logger.info("-------------------------------")
            
            return search_results
        except Exception as e:
            logger.error(f"Error searching ChromaDB collection: {e}", exc_info=True)
            raise

    def delete_by_ids(self, ids: List[str]) -> None:
        """
        Deletes specific document entries by their UUIDs.
        """
        if self._collection is None:
            logger.error("ChromaDB collection not initialized. Call init_bucket() first.")
            raise RuntimeError("ChromaDB collection not initialized. Call init_bucket() first.")
        try:
            self._collection.delete(ids=ids)
            logger.info(f"Successfully deleted {len(ids)} documents from collection.")
        except Exception as e:
            logger.error(f"Error deleting documents from ChromaDB: {e}", exc_info=True)
            raise
    
    def delete_bucket(self, bucket_name: str, connection : ClientAPI) -> None:
        """
        Deletes an entire collection from the database.
        """
        try:
            connection.delete_collection(name=bucket_name)  
        except ValueError as e:
            logger.warning(f"Attempted to delete non-existent bucket '{bucket_name}': {e}")

        
