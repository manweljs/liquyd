from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


def _resolved_field(document_class: type[Any], field_name: str) -> str:
    if not document_class.has_property(field_name):
        raise ValueError(f"Unknown aggregation field '{field_name}'.")
    return document_class.get_property(field_name).resolved_name


def _filter_query(
    document_class: type[Any], filters: Mapping[str, Any]
) -> dict[str, Any]:
    from .engines.opensearch.translator import translate_filters

    clauses = translate_filters(document_class, filters)
    if not clauses:
        return {"match_all": {}}
    return {"bool": {"filter": clauses}}


def _build_nested(
    document_class: type[Any], aggregations: Mapping[str, "Aggregation"]
) -> dict[str, Any]:
    return {
        name: aggregation.build(document_class)
        for name, aggregation in aggregations.items()
    }


def _parse_bucket(bucket: Mapping[str, Any], aggregations: Mapping[str, "Aggregation"]):
    result = {
        "key": bucket.get("key"),
        "count": int(bucket.get("doc_count", 0)),
    }
    if "key_as_string" in bucket:
        result["key_as_string"] = bucket["key_as_string"]
    for name, aggregation in aggregations.items():
        result[name] = aggregation.parse(bucket.get(name, {}))
    return result


class Aggregation(ABC):
    @abstractmethod
    def build(self, document_class: type[Any]) -> dict[str, Any]: ...

    @abstractmethod
    def parse(self, response: Mapping[str, Any]) -> Any: ...


@dataclass(frozen=True)
class FieldMetric(Aggregation):
    field_name: str
    metric_name: str = field(init=False, repr=False)

    def build(self, document_class: type[Any]) -> dict[str, Any]:
        return {
            self.metric_name: {
                "field": _resolved_field(document_class, self.field_name)
            }
        }

    def parse(self, response: Mapping[str, Any]) -> Any:
        return response.get("value")


@dataclass(frozen=True)
class Avg(FieldMetric):
    metric_name: str = field(default="avg", init=False, repr=False)


@dataclass(frozen=True)
class Min(FieldMetric):
    metric_name: str = field(default="min", init=False, repr=False)


@dataclass(frozen=True)
class Max(FieldMetric):
    metric_name: str = field(default="max", init=False, repr=False)


@dataclass(frozen=True)
class Sum(FieldMetric):
    metric_name: str = field(default="sum", init=False, repr=False)


@dataclass(frozen=True)
class ValueCount(FieldMetric):
    metric_name: str = field(default="value_count", init=False, repr=False)

    def parse(self, response: Mapping[str, Any]) -> int:
        return int(response.get("value", 0))


@dataclass(frozen=True)
class Cardinality(FieldMetric):
    metric_name: str = field(default="cardinality", init=False, repr=False)

    def parse(self, response: Mapping[str, Any]) -> int:
        return int(response.get("value", 0))


@dataclass(frozen=True)
class Percentile(Aggregation):
    field_name: str
    percentile: float

    def __post_init__(self) -> None:
        if not 0 <= self.percentile <= 100:
            raise ValueError("Percentile must be between 0 and 100.")

    def build(self, document_class: type[Any]) -> dict[str, Any]:
        return {
            "percentiles": {
                "field": _resolved_field(document_class, self.field_name),
                "percents": [self.percentile],
            }
        }

    def parse(self, response: Mapping[str, Any]) -> Any:
        values = response.get("values", {})
        return values.get(str(float(self.percentile)), values.get(str(self.percentile)))


@dataclass(frozen=True)
class Count(Aggregation):
    filters: Mapping[str, Any] = field(default_factory=dict)

    def __init__(self, **filters: Any) -> None:
        object.__setattr__(self, "filters", filters)

    def build(self, document_class: type[Any]) -> dict[str, Any]:
        return {"filter": _filter_query(document_class, self.filters)}

    def parse(self, response: Mapping[str, Any]) -> int:
        return int(response.get("doc_count", 0))


@dataclass(frozen=True)
class Filter(Aggregation):
    filters: Mapping[str, Any]
    aggregations: Mapping[str, Aggregation] = field(default_factory=dict)

    def build(self, document_class: type[Any]) -> dict[str, Any]:
        body = {"filter": _filter_query(document_class, self.filters)}
        if self.aggregations:
            body["aggs"] = _build_nested(document_class, self.aggregations)
        return body

    def parse(self, response: Mapping[str, Any]) -> dict[str, Any]:
        result = {"count": int(response.get("doc_count", 0))}
        for name, aggregation in self.aggregations.items():
            result[name] = aggregation.parse(response.get(name, {}))
        return result


@dataclass(frozen=True)
class Terms(Aggregation):
    field_name: str
    size: int = 10
    aggregations: Mapping[str, Aggregation] = field(default_factory=dict)
    order: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if self.size < 1:
            raise ValueError("Terms size must be greater than or equal to one.")

    def build(self, document_class: type[Any]) -> dict[str, Any]:
        terms: dict[str, Any] = {
            "field": _resolved_field(document_class, self.field_name),
            "size": self.size,
        }
        if self.order:
            terms["order"] = dict(self.order)
        body: dict[str, Any] = {"terms": terms}
        if self.aggregations:
            body["aggs"] = _build_nested(document_class, self.aggregations)
        return body

    def parse(self, response: Mapping[str, Any]) -> list[dict[str, Any]]:
        return [
            _parse_bucket(bucket, self.aggregations)
            for bucket in response.get("buckets", [])
        ]


@dataclass(frozen=True)
class DateHistogram(Aggregation):
    field_name: str
    fixed_interval: str | None = None
    calendar_interval: str | None = None
    aggregations: Mapping[str, Aggregation] = field(default_factory=dict)
    min_doc_count: int = 0

    def __post_init__(self) -> None:
        if bool(self.fixed_interval) == bool(self.calendar_interval):
            raise ValueError(
                "DateHistogram requires exactly one of fixed_interval "
                "or calendar_interval."
            )

    def build(self, document_class: type[Any]) -> dict[str, Any]:
        histogram: dict[str, Any] = {
            "field": _resolved_field(document_class, self.field_name),
            "min_doc_count": self.min_doc_count,
        }
        if self.fixed_interval:
            histogram["fixed_interval"] = self.fixed_interval
        else:
            histogram["calendar_interval"] = self.calendar_interval
        body: dict[str, Any] = {"date_histogram": histogram}
        if self.aggregations:
            body["aggs"] = _build_nested(document_class, self.aggregations)
        return body

    def parse(self, response: Mapping[str, Any]) -> list[dict[str, Any]]:
        return [
            _parse_bucket(bucket, self.aggregations)
            for bucket in response.get("buckets", [])
        ]


@dataclass(frozen=True)
class TopHits(Aggregation):
    size: int = 1
    sort: tuple[str, ...] = ()
    source: tuple[str, ...] | None = None

    def build(self, document_class: type[Any]) -> dict[str, Any]:
        if self.size < 1:
            raise ValueError("TopHits size must be greater than or equal to one.")
        top_hits: dict[str, Any] = {"size": self.size}
        if self.sort:
            top_hits["sort"] = [
                {
                    _resolved_field(document_class, name.removeprefix("-")): {
                        "order": "desc" if name.startswith("-") else "asc"
                    }
                }
                for name in self.sort
            ]
        if self.source is not None:
            top_hits["_source"] = [
                _resolved_field(document_class, name) for name in self.source
            ]
        return {"top_hits": top_hits}

    def parse(self, response: Mapping[str, Any]) -> list[dict[str, Any]]:
        return [
            dict(hit.get("_source", {}))
            for hit in response.get("hits", {}).get("hits", [])
        ]


def validate_aggregations(aggregations: Mapping[str, Aggregation]) -> None:
    if not aggregations:
        raise ValueError("At least one aggregation is required.")
    for name, aggregation in aggregations.items():
        if not name or not isinstance(name, str):
            raise ValueError("Aggregation names must be non-empty strings.")
        if not isinstance(aggregation, Aggregation):
            raise TypeError(f"Aggregation '{name}' must be an Aggregation instance.")
