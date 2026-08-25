from __future__ import annotations

from typing import Any

import pytest

from liquyd import BaseDocument, Page, Property
from liquyd.config import clear_configuration, configure
from liquyd.engines.base import EngineAdapter
from liquyd.engines.opensearch.translator import translate_queryset
from liquyd.engines.registry import register_engine, unregister_engine


class LogDocument(BaseDocument):
    id: str = Property("keyword", primary_key=True)
    project_name: str = Property("keyword")
    created_at: str = Property("date")

    class Meta:
        index = "test_logs"


class FakeEngine(EngineAdapter):
    name = "fake-pagination"

    def __init__(self) -> None:
        self.last_queryset = None

    def get_client(self, client_name=None):
        return None

    def build_query(self, queryset):
        return {}

    async def execute(self, queryset):
        return []

    async def first(self, queryset):
        return None

    async def get(self, queryset):
        raise LookupError

    async def count(self, queryset):
        return 42

    async def aggregate(self, queryset, aggregations):
        return {}

    async def paginate(self, queryset):
        self.last_queryset = queryset
        return [LogDocument(id="1", project_name="ezeas", created_at="now")], 42

    async def save_document(self, **kwargs: Any):
        return {}

    async def delete_document(self, **kwargs: Any):
        return {}

    async def create_index(self, document_class, *, client_name=None):
        return {}

    async def close_client(self, client_name=None):
        return None


@pytest.fixture
def fake_engine():
    engine = FakeEngine()
    register_engine(engine)
    configure(default={"engine": engine.name})
    yield engine
    clear_configuration()
    unregister_engine(engine.name)


async def test_paginate_preserves_filters_and_applies_window(fake_engine):
    result = await (
        LogDocument.filter(project_name="ezeas")
        .order_by("-created_at")
        .paginate(page=2, page_size=20)
    )

    assert isinstance(result, Page)
    assert result.total == 42
    assert result.total_pages == 3
    assert result.has_next is True
    assert result.has_previous is True
    assert fake_engine.last_queryset.filters == {"project_name": "ezeas"}
    assert fake_engine.last_queryset.offset_value == 20
    assert fake_engine.last_queryset.limit_value == 20
    assert fake_engine.last_queryset.ordering == ("-created_at",)


async def test_count_uses_engine(fake_engine):
    assert await LogDocument.filter(project_name="ezeas").count() == 42


@pytest.mark.parametrize(
    ("page", "page_size"),
    [(0, 20), (1, 0), (1, 101)],
)
async def test_paginate_rejects_invalid_values(fake_engine, page, page_size):
    with pytest.raises(ValueError):
        await LogDocument.filter().paginate(page=page, page_size=page_size)


def test_limit_offset_and_ordering_are_immutable(fake_engine):
    base = LogDocument.filter(project_name="ezeas")
    changed = base.limit(10).offset(5).order_by("-created_at")

    assert base.limit_value is None
    assert base.offset_value == 0
    assert base.ordering == ()
    assert changed.limit_value == 10
    assert changed.offset_value == 5
    assert changed.ordering == ("-created_at",)

    with pytest.raises(ValueError):
        base.order_by("missing")


def test_opensearch_translation_includes_window_and_sort(fake_engine):
    queryset = (
        LogDocument.filter(project_name="ezeas")
        .order_by("-created_at", "id")
        .offset(20)
        .limit(20)
    )

    assert translate_queryset(queryset) == {
        "query": {
            "bool": {
                "filter": [{"term": {"project_name": "ezeas"}}],
            }
        },
        "from": 20,
        "size": 20,
        "sort": [
            {"created_at": {"order": "desc"}},
            {"id": {"order": "asc"}},
        ],
    }
