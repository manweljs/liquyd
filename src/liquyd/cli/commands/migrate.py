# src/liquyd/cli/commands/migrate.py
from __future__ import annotations

from pathlib import Path
from typing import Any

from opensearchpy import NotFoundError, OpenSearch

from liquyd.document_registry import get_document
from liquyd.migrations.runner import migrate_client
from liquyd.migrations.state import (
    extract_applied_migration_names,
    get_migration_index_name,
)


def _get_client_settings(
    liquyd_config: dict[str, Any],
    client_name: str,
) -> dict[str, Any]:
    client_settings = liquyd_config.get(client_name)
    if not isinstance(client_settings, dict):
        raise ValueError(f"Client '{client_name}' was not found in LIQUYD_CONFIG.")
    return client_settings


def _build_opensearch_client(
    liquyd_config: dict[str, Any],
    client_name: str,
) -> OpenSearch:
    client_settings = dict(_get_client_settings(liquyd_config, client_name))
    client_settings.pop("documents", None)

    engine_name = client_settings.get("engine")
    if engine_name != "opensearch":
        raise ValueError(
            f"Client '{client_name}' uses unsupported engine '{engine_name}'."
        )

    client_settings.pop("engine", None)
    return OpenSearch(**client_settings)


def _get_index_settings(client_settings: dict[str, Any]) -> dict[str, Any]:
    number_of_replicas = client_settings.get("number_of_replicas", 0)
    return {
        "number_of_replicas": number_of_replicas,
    }


def _ensure_migration_index(
    client: OpenSearch,
    client_name: str,
    client_settings: dict[str, Any],
) -> str:
    migration_index_name = get_migration_index_name(client_name)

    if client.indices.exists(index=migration_index_name):
        return migration_index_name

    client.indices.create(
        index=migration_index_name,
        body={
            "settings": _get_index_settings(client_settings),
            "mappings": {
                "properties": {
                    "migration_name": {"type": "keyword"},
                    "applied_at": {"type": "date"},
                }
            },
        },
    )
    return migration_index_name


def _read_applied_migration_documents(
    client: OpenSearch,
    client_name: str,
    client_settings: dict[str, Any],
) -> list[dict[str, Any]]:
    migration_index_name = _ensure_migration_index(
        client=client,
        client_name=client_name,
        client_settings=client_settings,
    )

    try:
        response = client.search(
            index=migration_index_name,
            body={
                "size": 1000,
                "sort": [{"applied_at": {"order": "asc"}}],
                "query": {"match_all": {}},
            },
        )
    except NotFoundError:
        return []

    hits = response.get("hits", {}).get("hits", [])
    return [dict(hit.get("_source", {})) for hit in hits]


def _write_applied_migration_record(
    client: OpenSearch,
    client_name: str,
    client_settings: dict[str, Any],
    record: dict[str, Any],
) -> None:
    migration_index_name = _ensure_migration_index(
        client=client,
        client_name=client_name,
        client_settings=client_settings,
    )

    client.index(
        index=migration_index_name,
        id=record["migration_name"],
        body=record,
    )


def _handle_create_index(
    client: OpenSearch,
    client_settings: dict[str, Any],
    operation: dict[str, Any],
) -> None:
    document_class = get_document(operation["document_name"])
    index_name = document_class.get_index_name()

    if client.indices.exists(index=index_name):
        return

    client.indices.create(
        index=index_name,
        body={
            "settings": _get_index_settings(client_settings),
            **document_class.get_mapping_body(),
        },
    )


def _handle_add_field(
    client: OpenSearch,
    operation: dict[str, Any],
) -> None:
    document_class = get_document(operation["document_name"])
    field_name = operation["field_name"]
    if not field_name:
        raise ValueError("Field name is required for add_field operation.")

    property_instance = document_class.get_property(field_name)

    client.indices.put_mapping(
        index=document_class.get_index_name(),
        body={
            "properties": {
                property_instance.resolved_name: property_instance.to_mapping(),
            }
        },
    )


def _handle_delete_index(
    client: OpenSearch,
    operation: dict[str, Any],
) -> None:
    index_name = operation["index_name"]

    if not client.indices.exists(index=index_name):
        return

    client.indices.delete(index=index_name)


def _handle_unsupported_operation(operation: dict[str, Any]) -> None:
    raise NotImplementedError(
        f"Operation '{operation['type']}' is not implemented for OpenSearch migrate yet."
    )


def migrate(
    base_directory: str | Path,
    liquyd_config: dict[str, Any],
    client_name: str = "default",
    allow_breaking: bool = False,
) -> list[str]:
    client_settings = _get_client_settings(liquyd_config, client_name)
    client = _build_opensearch_client(liquyd_config, client_name)

    try:
        applied_migration_documents = _read_applied_migration_documents(
            client=client,
            client_name=client_name,
            client_settings=client_settings,
        )
        applied_migration_names = extract_applied_migration_names(
            migration_documents=applied_migration_documents
        )

        operation_handlers = {
            "create_index": lambda operation: _handle_create_index(
                client=client,
                client_settings=client_settings,
                operation=operation,
            ),
            "add_field": lambda operation: _handle_add_field(
                client=client,
                operation=operation,
            ),
            "delete_index": lambda operation: _handle_delete_index(
                client=client,
                operation=operation,
            ),
            "remove_field": _handle_unsupported_operation,
            "change_field": _handle_unsupported_operation,
            "reindex_required": _handle_unsupported_operation,
        }

        return migrate_client(
            base_directory=Path(base_directory),
            applied_migration_names=applied_migration_names,
            operation_handlers=operation_handlers,
            record_writer=lambda record: _write_applied_migration_record(
                client=client,
                client_name=client_name,
                client_settings=client_settings,
                record=record,
            ),
            allow_breaking=allow_breaking,
        )
    finally:
        client.close()
