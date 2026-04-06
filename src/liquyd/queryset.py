from __future__ import annotations

from typing import Any

from .config import get_client_engine, get_default_client_name
from .engines.registry import get_engine
from .types import ClientName


class QuerySet:
    def __init__(
        self,
        document_class: type[Any],
        *,
        client_name: ClientName | None = None,
        filters: dict[str, Any] | None = None,
    ) -> None:
        self.document_class = document_class
        self.client_name = client_name or get_default_client_name()
        self.filters = dict(filters or {})

    def using(self, client_name: ClientName) -> QuerySet:
        return self.__class__(
            self.document_class,
            client_name=client_name,
            filters=self.filters,
        )

    def filter(self, **kwargs: Any) -> QuerySet:
        next_filters = dict(self.filters)
        next_filters.update(kwargs)
        return self.__class__(
            self.document_class,
            client_name=self.client_name,
            filters=next_filters,
        )

    def get_index_name(self) -> str:
        return self.document_class.get_index_name()

    def get_engine_name(self) -> str:
        return get_client_engine(self.client_name)

    def get_engine_adapter(self):
        engine_name = self.get_engine_name()
        return get_engine(engine_name)

    def build(self) -> dict[str, Any]:
        engine_adapter = self.get_engine_adapter()
        return engine_adapter.build_query(self)

    async def execute(self) -> Any:
        engine_adapter = self.get_engine_adapter()
        return await engine_adapter.execute(self)

    async def all(self) -> Any:
        return await self.execute()

    async def first(self) -> Any:
        engine_adapter = self.get_engine_adapter()
        return await engine_adapter.first(self)

    async def get(self) -> Any:
        engine_adapter = self.get_engine_adapter()
        return await engine_adapter.get(self)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"document_class={self.document_class.__name__}, "
            f"client_name={self.client_name!r}, "
            f"filters={self.filters!r})"
        )
