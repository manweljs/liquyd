from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..base import EngineAdapter
from .client import get_opensearch_client
from .translator import translate_queryset
from opensearchpy import NotFoundError

if TYPE_CHECKING:
    from ...queryset import QuerySet


class OpenSearchEngineAdapter(EngineAdapter):
    name = "opensearch"

    def get_client(self, client_name: str | None = None) -> Any:
        return get_opensearch_client(client_name)

    def build_query(self, queryset: QuerySet) -> dict[str, Any]:
        return translate_queryset(queryset)

    def get_index_settings(self, client_name: str | None = None) -> dict[str, Any]:
        client = self.get_client(client_name)
        engine_config = getattr(client, "_liquyd_config", {}) or {}

        number_of_replicas = engine_config.get("number_of_replicas", 0)

        return {
            "number_of_replicas": number_of_replicas,
        }

    def _hydrate_hit(self, queryset: QuerySet, hit: dict[str, Any]) -> Any:
        source = dict(hit.get("_source", {}))
        document_id = hit.get("_id")

        document = queryset.document_class.from_dict(
            source,
            by_name=True,
            is_persisted=True,
        )

        if document_id is not None:
            document.set_primary_key_value(document_id)

        return document

    def _get_primary_key_filter_value(self, queryset: QuerySet) -> Any | None:
        primary_key_name = queryset.document_class.get_primary_key_name()

        if len(queryset.filters) != 1:
            return None

        if primary_key_name not in queryset.filters:
            return None

        return queryset.filters[primary_key_name]

    async def execute(self, queryset: QuerySet) -> list[Any]:
        client = self.get_client(queryset.client_name)
        request_body = self.build_query(queryset)

        response = await client.search(
            index=queryset.get_index_name(),
            body=request_body,
        )

        hits = response.get("hits", {}).get("hits", [])
        return [self._hydrate_hit(queryset, dict(hit)) for hit in hits]

    async def first(self, queryset: QuerySet) -> Any | None:
        primary_key_value = self._get_primary_key_filter_value(queryset)
        if primary_key_value is not None:
            try:
                return await self.get(queryset)
            except LookupError:
                return None

        client = self.get_client(queryset.client_name)
        request_body = self.build_query(queryset)
        request_body["size"] = 1

        response = await client.search(
            index=queryset.get_index_name(),
            body=request_body,
        )

        hits = response.get("hits", {}).get("hits", [])
        if not hits:
            return None

        return self._hydrate_hit(queryset, dict(hits[0]))

    async def get(self, queryset: QuerySet) -> Any:
        primary_key_value = self._get_primary_key_filter_value(queryset)
        if primary_key_value is not None:
            client = self.get_client(queryset.client_name)

            try:
                response = await client.get(
                    index=queryset.get_index_name(),
                    id=primary_key_value,
                )
            except NotFoundError as exc:
                raise LookupError("No document matched the query.") from exc

            return self._hydrate_hit(queryset, dict(response))

        client = self.get_client(queryset.client_name)
        request_body = self.build_query(queryset)
        request_body["size"] = 2

        response = await client.search(
            index=queryset.get_index_name(),
            body=request_body,
        )

        hits = response.get("hits", {}).get("hits", [])

        if not hits:
            raise LookupError("No document matched the query.")

        if len(hits) > 1:
            raise LookupError("Multiple documents matched the query.")

        return self._hydrate_hit(queryset, dict(hits[0]))

    async def save_document(
        self,
        *,
        document_class: type[Any],
        source: dict[str, Any],
        document_id: Any | None = None,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        client = self.get_client(client_name)
        index_name = document_class.get_index_name()

        if document_id is None:
            response = await client.index(
                index=index_name,
                body=source,
                refresh=True,
            )
        else:
            response = await client.index(
                index=index_name,
                id=document_id,
                body=source,
                refresh=True,
            )

        return {
            "document_id": response.get("_id"),
            "result": response.get("result"),
            "response": dict(response),
        }

    async def delete_document(
        self,
        *,
        document_class: type[Any],
        document_id: Any,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        client = self.get_client(client_name)
        index_name = document_class.get_index_name()

        response = await client.delete(
            index=index_name,
            id=document_id,
            refresh=True,
        )

        return {
            "document_id": response.get("_id"),
            "result": response.get("result"),
            "response": dict(response),
        }

    async def create_index(
        self,
        document_class: type[Any],
        *,
        client_name: str | None = None,
    ) -> dict[str, Any]:
        client = self.get_client(client_name)
        index_name = document_class.get_index_name()
        index_settings = self.get_index_settings(client_name)

        index_exists = await client.indices.exists(index=index_name)
        if index_exists:
            return {
                "acknowledged": True,
                "index": index_name,
                "created": False,
            }

        response = await client.indices.create(
            index=index_name,
            body={
                "settings": index_settings,
            },
        )
        return {
            "acknowledged": bool(response.get("acknowledged", False)),
            "index": index_name,
            "created": True,
            "response": dict(response),
        }


opensearch_engine = OpenSearchEngineAdapter()
