from pydantic import RootModel
from typing import Dict, Union, List

MetadataValue = Union[str, int, float, bool, None, List[str], List[int], List[float], List[bool]]

class Metadata(RootModel[Dict[str, MetadataValue]]):
    """
    A generic Pydantic model for metadata. It wraps a dictionary with keys
    as strings and values of a type union that is compatible with what vector
    databases like ChromaDB expect for metadata.

    Usage:
        metadata_obj = Metadata.model_validate({"source": "file.pdf", "page": 1})
        dictionary = metadata_obj.model_dump()
    """
    pass
