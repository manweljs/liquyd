# src/liquyd/migrations/discovery.py
from __future__ import annotations

from typing import Iterable, Type

from liquyd.document_registry import list_documents


def iter_documents() -> Iterable[Type]:
    for document_class in list_documents():
        yield document_class
