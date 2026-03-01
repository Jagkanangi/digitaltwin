from src.utils.SystemConfig import config
from src.vectordb.AbstractDB import AbstractDB
from src.vectordb.ChromaDB import ChromaDB
from src.vectordb.ChormaDBHttpClient import ChromaDBHttpClient
def get_vectordb() -> AbstractDB:
    """
    A factory function that creates and returns a vector database instance.

    This function reads the `DB_TYPE` from the application's configuration
    and dynamically instantiates the corresponding concrete implementation of
    `AbstractDB`. This is the core of the plug-and-play architecture, as it
    allows for swapping the vector database backend (e.g., from ChromaDB to
    another system) by simply changing a configuration value.

    Raises:
        ValueError: If the configured `DB_TYPE` is not supported.

    Returns:
        An instance of a class that implements the `AbstractDB` interface.
    """
    db_type = config.connection.db_type

    if db_type == 'chroma':
        return ChromaDB()
    elif db_type == "chroma_remote":
        return ChromaDBHttpClient()
    # Add other database types here in the future, e.g.:
    # elif db_type == 'weaviate':
    #     return WeaviateDB()
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")
