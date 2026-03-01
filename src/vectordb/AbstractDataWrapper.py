from abc import ABC, abstractmethod
from typing import List, Any
from vo.Metadata import Metadata
from vo.Models import SearchResult
from .buckets.Buckets import Bucket

class AbstractDataWrapper(ABC):
    """
    An abstract base class that defines a database-agnostic interface for
    data manipulation, following the Data Access Object (DAO) pattern.

    An instance of a concrete implementation of this class represents a direct,
    usable interface to a specific "bucket" (e.g., a collection or index) in
    the vector database. It abstracts away the specific implementation details
    of the underlying database technology.
    """

    @abstractmethod
    def add(self, texts: List[str], embeddings : List[list[float]], metadatas: List[Metadata] | None = None) -> List[str]:
        """
        Adds texts to the vector database.
        Args:
            texts: A list of texts to add.
            metadatas: An optional list of metadata dictionaries corresponding to the texts.
        Returns:
            A list of unique IDs generated for the added texts.
        """
        pass

    @abstractmethod
    def search(self, query_text_embeddings: List[float]) -> List[SearchResult]:
        """
        Searches the vector database for similar texts.
        Args:
            query_texts: A list of texts to search for.
            n_results: The number of results to return.
        Returns:
            A list of search results.
        """
        pass

    @abstractmethod
    def delete_by_ids(self, ids: List[str]) -> None:
        """
        Deletes texts from the vector database by their IDs.
        Args:
            ids: A list of IDs of the texts to delete.
        """
        pass

    @abstractmethod
    def delete_bucket(self, bucket_name : str, connection : Any) -> None:
        """
        Deletes texts from the vector database by their IDs.
        Args:
            ids: A list of IDs of the texts to delete.
        """
        pass

    @abstractmethod
    def get_bucket(self) -> Bucket:
        """
        Retrieves an object representing the underlying data bucket.

        This method should only be called after `init_bucket` has been
        successfully executed.

        Returns:
            An object representing the data bucket.

        Raises:
            RuntimeError: If the bucket has not been initialized.
        """
        pass

    @abstractmethod
    def init_bucket(self, connection: Any, bucket_name : str):
        """
        Initializes the wrapper with a connection to a specific data bucket.

        Note: The term "bucket" is used here as a generic name for the
        underlying data container, which may have different names in
        different databases (e.g., "collection" in ChromaDB, "class" in
        Weaviate, "index" in Pinecone).

        Args:
            connection: The database client connection object.
            bucket_name: The name of the bucket to initialize.
        """
        pass
