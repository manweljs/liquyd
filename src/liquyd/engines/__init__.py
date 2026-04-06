from .opensearch import opensearch_engine
from .registry import register_engine

register_engine(opensearch_engine)

__all__ = [
    "opensearch_engine",
    "register_engine",
]
