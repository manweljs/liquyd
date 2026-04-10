# src/liquyd/engines/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from ..types import ClientName

if TYPE_CHECKING:
    from ..queryset import QuerySet


class EngineAdapter(ABC):
    name: str

    @abstractmethod
    def get_client(self, client_name: ClientName | None = None) -> Any: ...

    @abstractmethod
    def build_query(self, queryset: QuerySet) -> dict[str, Any]: ...

    @abstractmethod
    async def execute(self, queryset: QuerySet) -> Any: ...

    @abstractmethod
    async def first(self, queryset: QuerySet) -> Any: ...

    @abstractmethod
    async def get(self, queryset: QuerySet) -> Any: ...

    @abstractmethod
    async def save_document(
        self,
        *,
        document_class: type[Any],
        source: dict[str, Any],
        document_id: Any | None = None,
        client_name: ClientName | None = None,
    ) -> Any: ...

    @abstractmethod
    async def delete_document(
        self,
        *,
        document_class: type[Any],
        document_id: Any,
        client_name: ClientName | None = None,
    ) -> Any: ...

    @abstractmethod
    async def create_index(
        self,
        document_class: type[Any],
        *,
        client_name: ClientName | None = None,
    ) -> Any: ...

    @abstractmethod
    async def close_client(self, client_name: ClientName | None = None) -> None: ...
