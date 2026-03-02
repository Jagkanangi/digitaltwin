from utils.SystemConfig import config
from .AbstractDB import AbstractDB
from .ChromaDB import ChromaDB
from .ChromaDBHttpClient import ChromaDBHttpClient

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

    db_mapping = {
        "ChromaDB": ChromaDB,
        "ChromaDBHttpClient": ChromaDBHttpClient,
    }

    if db_type in db_mapping:
        return db_mapping[db_type]()
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")
