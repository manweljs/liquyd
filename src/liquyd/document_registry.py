from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING

from .exceptions import DocumentDefinitionError

if TYPE_CHECKING:
    from .document import BaseDocument


class DocumentRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._documents: dict[str, type[BaseDocument]] = {}

    def register(self, document_class: type[BaseDocument]) -> None:
        document_name = document_class.__name__.strip()

        if not document_name:
            raise DocumentDefinitionError("Document name cannot be empty.")

        with self._lock:
            self._documents[document_name] = document_class

    def get(self, document_name: str) -> type[BaseDocument]:
        document_class = self._documents.get(document_name)
        if document_class is None:
            raise DocumentDefinitionError(
                f"Document '{document_name}' is not registered."
            )
        return document_class

    def has(self, document_name: str) -> bool:
        return document_name in self._documents

    def unregister(self, document_name: str) -> None:
        with self._lock:
            self._documents.pop(document_name, None)

    def clear(self) -> None:
        with self._lock:
            self._documents = {}

    def list(self) -> list[type[BaseDocument]]:
        return list(self._documents.values())

    def list_names(self) -> list[str]:
        return list(self._documents.keys())


_registry = DocumentRegistry()


def register_document(document_class: type[BaseDocument]) -> None:
    _registry.register(document_class)


def get_document(document_name: str) -> type[BaseDocument]:
    return _registry.get(document_name)


def has_document(document_name: str) -> bool:
    return _registry.has(document_name)


def unregister_document(document_name: str) -> None:
    _registry.unregister(document_name)


def clear_documents() -> None:
    _registry.clear()


def list_documents() -> list[type[BaseDocument]]:
    return _registry.list()


def list_document_names() -> list[str]:
    return _registry.list_names()
