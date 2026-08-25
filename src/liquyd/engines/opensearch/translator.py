from __future__ import annotations

from typing import Any

from ...queryset import QuerySet

LOOKUPS = {"exact", "in", "gt", "gte", "lt", "lte"}


def translate_filters(
    document_class: type[Any], filters: dict[str, Any] | Any
) -> list[dict[str, Any]]:
    clauses: list[dict[str, Any]] = []
    for expression, value in filters.items():
        field_name, separator, possible_lookup = expression.rpartition("__")
        lookup = (
            possible_lookup if separator and possible_lookup in LOOKUPS else "exact"
        )
        if lookup == "exact":
            field_name = expression

        property_instance = document_class.get_property(field_name)
        resolved_name = property_instance.resolved_name

        if lookup == "exact":
            clauses.append({"term": {resolved_name: value}})
        elif lookup == "in":
            clauses.append({"terms": {resolved_name: list(value)}})
        else:
            clauses.append({"range": {resolved_name: {lookup: value}}})
    return clauses


class OpenSearchQueryTranslator:
    def translate(self, queryset: QuerySet) -> dict[str, Any]:
        filters: list[dict[str, Any]] = []

        filters.extend(translate_filters(queryset.document_class, queryset.filters))

        if not filters:
            query: dict[str, Any] = {"match_all": {}}
        else:
            query = {
                "bool": {
                    "filter": filters,
                }
            }

        body: dict[str, Any] = {"query": query}

        if queryset.offset_value:
            body["from"] = queryset.offset_value

        if queryset.limit_value is not None:
            body["size"] = queryset.limit_value

        if queryset.ordering:
            body["sort"] = [
                {
                    queryset.document_class.get_property(
                        field.removeprefix("-")
                    ).resolved_name: {
                        "order": "desc" if field.startswith("-") else "asc"
                    }
                }
                for field in queryset.ordering
            ]

        return body


_translator = OpenSearchQueryTranslator()


def translate_queryset(queryset: QuerySet) -> dict[str, Any]:
    return _translator.translate(queryset)
