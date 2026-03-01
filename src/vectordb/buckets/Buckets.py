from abc import ABC, abstractmethod
from typing import List, Dict, Any, cast
from chromadb.api.models.Collection import Collection
# We use 'float' for embeddings because vectors are decimal numbers, not integers!
class Bucket(ABC):
    """
    An abstract base class that defines a standardized interface for a "bucket"
    of data in a vector database.

    The term "Bucket" is used as a generic name to represent database-specific
    containers like collections (ChromaDB), indexes (Pinecone), or classes
    (Weaviate). This abstraction allows the application to interact with these

    containers in a uniform way, regardless of the underlying technology.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        """Every bucket MUST have a name to be reachable."""
        pass

    @abstractmethod
    def get_documents(self) -> List[str]:
        """Returns the list of text chunks."""
        pass


    @abstractmethod
    def get_metadata(self) -> List[Dict[str, Any]]:
        """Returns the list of dictionaries for filtering."""
        pass

class ChromaBucket(Bucket):
    """
    A concrete implementation of the `Bucket` interface for ChromaDB.

    This class wraps a ChromaDB `Collection` object and provides access to its
    data (documents, embeddings, metadata) in the standardized format defined
    by the `Bucket` interface.
    """
    def __init__(self, collection : Collection):
        self._collection = collection
        self._data = self._collection.get(include=["metadatas", "documents", "embeddings"])
        
    @property
    def name(self) -> str:
        """Returns the name of the wrapped ChromaDB collection."""
        return self._collection.name

    def get_documents(self) -> List[str]:
        """
        Returns the list of documents from the collection.

        The data is fetched when the `ChromaBucket` is instantiated.
        """
        return self._data['documents'] or []

    def get_embeddings(self) -> List[List[float]]: 
        """
        Returns the list of embeddings from the collection.

        The data is fetched when the `ChromaBucket` is instantiated.
        """
        return self._data['embeddings'] or []

    def get_metadata(self) -> List[Dict[str, Any]]:
        """
        Returns the list of metadata from the collection.

        The data is fetched when the `ChromaBucket` is instantiated.
        """
        metadatas = self._data['metadatas'] or []
        return cast(List[Dict[str, Any]], metadatas)