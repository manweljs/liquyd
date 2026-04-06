# discovery.py
from __future__ import annotations

from typing import Iterable, Type

from liquyd.migrations.registry import discover_client_documents


def discover_documents(client_name: str) -> list[Type]:
    return discover_client_documents(client_name)


def iter_documents(client_name: str) -> Iterable[Type]:
    for document_class in discover_documents(client_name):
        yield document_class
