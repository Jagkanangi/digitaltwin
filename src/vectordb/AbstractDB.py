from abc import ABC, abstractmethod
from typing import Any
from vectordb.AbstractDataWrapper import AbstractDataWrapper

# DESIGN RATIONALE:
# The AbstractDB class is the cornerstone of the database abstraction layer.
# It defines a common interface that all vector database implementations in the
# application must adhere to. This design promotes a "plug-and-play" architecture:
# as long as a new database connector class implements these abstract methods,
# it can be seamlessly integrated into the application via the VectorDBFactory
# without requiring any changes to the business logic.
#
# This approach decouples the application's core logic from the specific
# database technology, enhancing flexibility and making future migrations
# or extensions much simpler.

class AbstractDB(ABC):
    """
    An abstract base class that defines the standard interface for managing
    vector database connections and retrieving data wrappers.

    This class ensures that all concrete database implementations provide a
    consistent API for establishing and retrieving connections, as well as for
    obtaining a data wrapper for interacting with specific data "buckets"
    (e.g., collections, indexes).
    """

    @abstractmethod
    def connect(self) -> Any:
        """
        Establishes a connection to the database and returns a client object.
        """
        pass
    
    @abstractmethod
    def get_connection(self) -> Any:
        """
        Returns an active, ready-to-use client object for the database.
        """


    @abstractmethod
    def get_db_wrapper(self) -> 'AbstractDataWrapper':
        """
        Returns a database-agnostic data wrapper (Data Access Object).

        This wrapper is responsible for abstracting all data manipulation
        operations (add, search, delete) for a specific data bucket.

        Returns:
            An instance of a class that implements `AbstractDataWrapper`.
        """
        pass

