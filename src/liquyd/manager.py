from __future__ import annotations

from typing import Any

from .queryset import QuerySet
from .types import ClientName


class DocumentManager:
    def __init__(self, document_class: type[Any]) -> None:
        self.document_class = document_class

    def using(self, client_name: ClientName) -> QuerySet:
        return QuerySet(
            self.document_class,
            client_name=client_name,
        )

    def all(self) -> QuerySet:
        return QuerySet(self.document_class)

    def filter(self, **kwargs: Any) -> QuerySet:
        return QuerySet(self.document_class).filter(**kwargs)
