from __future__ import annotations

from typing import Any

import pytest

from liquyd import (
    Avg,
    BaseDocument,
    Count,
    DateHistogram,
    Percentile,
    Property,
    Terms,
    TopHits,
)
from liquyd.config import clear_configuration, configure
from liquyd.engines.opensearch.adapter import OpenSearchEngineAdapter
from liquyd.engines.opensearch.translator import translate_queryset
from liquyd.engines.registry import register_engine, unregister_engine


class RequestLog(BaseDocument):
    id: str = Property("keyword", primary_key=True)
    created_at: str = Property("date")
    status: str = Property("keyword")
    request_type: str = Property("keyword")
    duration_ms: int = Property("integer")
    error_message: str | None = Property("text")

    class Meta:
        index = "request_logs"


class FakeClient:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.last_search: dict[str, Any] | None = None

    async def search(self, **kwargs: Any) -> dict[str, Any]:
        self.last_search = kwargs
        return self.response


class FakeOpenSearchEngine(OpenSearchEngineAdapter):
    name = "fake-opensearch-aggregations"

    def __init__(self, client: FakeClient) -> None:
        self.client = client

    def get_client(self, client_name=None):
        return self.client


@pytest.fixture
def aggregation_engine():
    client = FakeClient(
        {
            "aggregations": {
                "total": {"doc_count": 120},
                "errors": {"doc_count": 5},
                "average_duration": {"value": 42.5},
                "p95_duration": {"values": {"95.0": 210.0}},
                "types": {
                    "buckets": [
                        {
                            "key": "GRAPHQL",
                            "doc_count": 80,
                            "average_duration": {"value": 50.0},
                        }
                    ]
                },
            }
        }
    )
    engine = FakeOpenSearchEngine(client)
    register_engine(engine)
    configure(default={"engine": engine.name})
    yield client
    clear_configuration()
    unregister_engine(engine.name)


async def test_aggregate_builds_one_search_and_normalizes_response(aggregation_engine):
    result = await RequestLog.filter(created_at__gte="2026-08-25T00:00:00Z").aggregate(
        total=Count(),
        errors=Count(status="error"),
        average_duration=Avg("duration_ms"),
        p95_duration=Percentile("duration_ms", 95),
        types=Terms(
            "request_type",
            aggregations={"average_duration": Avg("duration_ms")},
        ),
    )

    assert result == {
        "total": 120,
        "errors": 5,
        "average_duration": 42.5,
        "p95_duration": 210.0,
        "types": [{"key": "GRAPHQL", "count": 80, "average_duration": 50.0}],
    }
    assert aggregation_engine.last_search == {
        "index": "request_logs",
        "body": {
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"created_at": {"gte": "2026-08-25T00:00:00Z"}}}
                    ]
                }
            },
            "size": 0,
            "aggs": {
                "total": {"filter": {"match_all": {}}},
                "errors": {
                    "filter": {"bool": {"filter": [{"term": {"status": "error"}}]}}
                },
                "average_duration": {"avg": {"field": "duration_ms"}},
                "p95_duration": {
                    "percentiles": {"field": "duration_ms", "percents": [95]}
                },
                "types": {
                    "terms": {"field": "request_type", "size": 10},
                    "aggs": {"average_duration": {"avg": {"field": "duration_ms"}}},
                },
            },
        },
    }


def test_range_and_in_filter_translation(aggregation_engine):
    queryset = RequestLog.filter(
        created_at__gte="start",
        created_at__lt="end",
        request_type__in=["REST", "GRAPHQL"],
    )
    assert translate_queryset(queryset)["query"]["bool"]["filter"] == [
        {"range": {"created_at": {"gte": "start"}}},
        {"range": {"created_at": {"lt": "end"}}},
        {"terms": {"request_type": ["REST", "GRAPHQL"]}},
    ]


def test_date_histogram_and_top_hits_translation():
    aggregation = DateHistogram(
        "created_at",
        fixed_interval="5m",
        aggregations={
            "errors": Count(status="error"),
            "latest": TopHits(size=1, sort=("-created_at",), source=("status",)),
        },
    )
    assert aggregation.build(RequestLog) == {
        "date_histogram": {
            "field": "created_at",
            "min_doc_count": 0,
            "fixed_interval": "5m",
        },
        "aggs": {
            "errors": {"filter": {"bool": {"filter": [{"term": {"status": "error"}}]}}},
            "latest": {
                "top_hits": {
                    "size": 1,
                    "sort": [{"created_at": {"order": "desc"}}],
                    "_source": ["status"],
                }
            },
        },
    }


@pytest.mark.parametrize("percentile", [-1, 101])
def test_percentile_rejects_out_of_range(percentile):
    with pytest.raises(ValueError):
        Percentile("duration_ms", percentile)


def test_aggregation_validates_fields():
    with pytest.raises(ValueError, match="Unknown aggregation field"):
        Avg("missing").build(RequestLog)
