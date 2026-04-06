from __future__ import annotations

from typing import Any

from ...queryset import QuerySet


class OpenSearchQueryTranslator:
    def translate(self, queryset: QuerySet) -> dict[str, Any]:
        filters: list[dict[str, Any]] = []

        for field_name, value in queryset.filters.items():
            property_instance = queryset.document_class.get_property(field_name)
            filters.append(
                {
                    "term": {
                        property_instance.resolved_name: value,
                    }
                }
            )

        if not filters:
            return {"query": {"match_all": {}}}

        return {
            "query": {
                "bool": {
                    "filter": filters,
                }
            }
        }


_translator = OpenSearchQueryTranslator()


def translate_queryset(queryset: QuerySet) -> dict[str, Any]:
    return _translator.translate(queryset)
