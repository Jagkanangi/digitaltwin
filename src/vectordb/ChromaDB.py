import chromadb
from chromadb.api import ClientAPI
import threading
from .AbstractDB import AbstractDB
from .DataWrappers import ChromaDataWrapper
from utils.SystemConfig import config
import logging

logger = logging.getLogger(__name__)

class ChromaDB(AbstractDB):
    """
    A concrete implementation of `AbstractDB` for the ChromaDB vector database.

    This class manages the connection to ChromaDB, implementing the singleton
    pattern to ensure that a single client instance is shared across the

    application. The connection logic is thread-safe.

    It is responsible for creating `ChromaDataWrapper` instances, which are
    used to interact with specific ChromaDB collections.
    """
    _client: ClientAPI | None = None
    _client_lock = threading.Lock()

    def __init__(self):
        """
        Initializes the ChromaDB connector.

        Retrieves the database host and port from the application's
        configuration and establishes the initial connection.
        """
        self._host = config.connection.db_host
        self._port = config.connection.db_port
        try:
            self.connect()
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB connection: {e}", exc_info=True)

    def connect(self) -> ClientAPI:
        """
        Establishes a thread-safe, singleton connection to the ChromaDB server.

        This method ensures that only one instance of the `chromadb.HttpClient`
        is created and shared across the application. It uses a lock to prevent
        race conditions during initialization.

        It also includes a resilience mechanism: if a client instance already
        exists, it checks its heartbeat. If the connection is lost, it
        re-establishes it.

        Returns:
            The active ChromaDB client instance.
        """
        if ChromaDB._client is None:
            with ChromaDB._client_lock:
                if ChromaDB._client is None:
                    try:
                        ChromaDB._client = chromadb.HttpClient(host=self._host, port=self._port)
                        logger.info(f"Connected to ChromaDB at {self._host}:{self._port}")
                    except Exception as e:
                        logger.error(f"Error connecting to ChromaDB at {self._host}:{self._port}: {e}", exc_info=True)
                        raise
                else :
                    try:
                        ChromaDB._client.heartbeat()
                    except Exception as e:
                        logger.warning(f"ChromaDB heartbeat failed: {e}. Reconnecting...")
                        with ChromaDB._client_lock:
                            try:
                                ChromaDB._client = chromadb.HttpClient(host=self._host, port=self._port)
                                logger.info(f"Reconnected to ChromaDB at {self._host}:{self._port}")
                            except Exception as re_e:
                                logger.error(f"Failed to reconnect to ChromaDB: {re_e}", exc_info=True)
                                raise
        return ChromaDB._client

    def get_connection(self):
        """
        Retrieves the active ChromaDB client instance.

        This method is an alias for `connect()` and provides a consistent
        way to get the client, adhering to the `AbstractDB` interface.

        Returns:
            The active ChromaDB client instance.
        """
        return self.connect()
    
    def get_db_wrapper(self) -> ChromaDataWrapper:
        """
        Creates and returns a data wrapper for ChromaDB.

        This method acts as a factory for `ChromaDataWrapper`, returning a
        new instance that can be used to perform operations on a specific
        ChromaDB collection.

        Returns:
            A new instance of `ChromaDataWrapper`.
        """
        return ChromaDataWrapper()
