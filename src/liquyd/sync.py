from __future__ import annotations

from .document_registry import list_documents


async def create_all_indexes(client_name: str | None = None) -> list[dict]:
    results: list[dict] = []

    for document_class in list_documents():
        queryset = (
            document_class.using(client_name)
            if client_name
            else document_class.filter()
        )
        engine_adapter = queryset.get_engine_adapter()
        result = await engine_adapter.create_index(
            document_class,
            client_name=queryset.client_name,
        )
        results.append(result)

    return results
