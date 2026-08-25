from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from .config import get_client_engine, get_default_client_name
from .engines.registry import get_engine
from .types import ClientName


@dataclass(frozen=True)
class Page:
    items: list[Any]
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        return ceil(self.total / self.page_size) if self.total else 0

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1 and self.total_pages > 0


class QuerySet:
    def __init__(
        self,
        document_class: type[Any],
        *,
        client_name: ClientName | None = None,
        filters: dict[str, Any] | None = None,
        limit_value: int | None = None,
        offset_value: int = 0,
        ordering: tuple[str, ...] = (),
    ) -> None:
        self.document_class = document_class
        self.client_name = client_name or get_default_client_name()
        self.filters = dict(filters or {})
        self.limit_value = limit_value
        self.offset_value = offset_value
        self.ordering = ordering

    def _clone(self, **changes: Any) -> QuerySet:
        state = {
            "client_name": self.client_name,
            "filters": self.filters,
            "limit_value": self.limit_value,
            "offset_value": self.offset_value,
            "ordering": self.ordering,
        }
        state.update(changes)
        return self.__class__(self.document_class, **state)

    def using(self, client_name: ClientName) -> QuerySet:
        return self._clone(client_name=client_name)

    def filter(self, **kwargs: Any) -> QuerySet:
        next_filters = dict(self.filters)
        next_filters.update(kwargs)
        return self._clone(filters=next_filters)

    def limit(self, value: int) -> QuerySet:
        if value < 0:
            raise ValueError("QuerySet limit must be greater than or equal to zero.")
        return self._clone(limit_value=value)

    def offset(self, value: int) -> QuerySet:
        if value < 0:
            raise ValueError("QuerySet offset must be greater than or equal to zero.")
        return self._clone(offset_value=value)

    def order_by(self, *fields: str) -> QuerySet:
        for field in fields:
            field_name = field.removeprefix("-")
            if not field_name or not self.document_class.has_property(field_name):
                raise ValueError(f"Unknown ordering field '{field_name}'.")
        return self._clone(ordering=tuple(fields))

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

    async def count(self) -> int:
        engine_adapter = self.get_engine_adapter()
        return await engine_adapter.count(self)

    async def aggregate(self, **aggregations: Any) -> dict[str, Any]:
        from .aggregations import validate_aggregations

        validate_aggregations(aggregations)
        engine_adapter = self.get_engine_adapter()
        return await engine_adapter.aggregate(self, aggregations)

    async def paginate(self, *, page: int = 1, page_size: int = 20) -> Page:
        if page < 1:
            raise ValueError("Pagination page must be greater than or equal to one.")
        if page_size < 1:
            raise ValueError(
                "Pagination page_size must be greater than or equal to one."
            )
        if page_size > 100:
            raise ValueError("Pagination page_size cannot be greater than 100.")

        paginated_queryset = self.offset((page - 1) * page_size).limit(page_size)
        engine_adapter = paginated_queryset.get_engine_adapter()
        items, total = await engine_adapter.paginate(paginated_queryset)
        return Page(items=items, page=page, page_size=page_size, total=total)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"document_class={self.document_class.__name__}, "
            f"client_name={self.client_name!r}, "
            f"filters={self.filters!r}, "
            f"limit={self.limit_value!r}, offset={self.offset_value!r}, "
            f"ordering={self.ordering!r})"
        )
