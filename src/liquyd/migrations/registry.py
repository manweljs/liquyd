# src/liquyd/migrations/registry.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol


class EngineMigrationAdapter(Protocol):
    def get_operation_handlers(self) -> dict[str, Callable[[dict], None]]: ...

    def write_applied_migration_record(self, record: dict[str, Any]) -> None: ...

    def read_applied_migration_documents(self) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class ClientSettings:
    client_name: str
    engine_name: str
    migrations_directory: Path
    adapter_factory: Callable[["ClientSettings"], EngineMigrationAdapter]


ClientSettingsResolver = Callable[[str], ClientSettings]
DocumentDiscoveryResolver = Callable[[], list[type]]


_client_settings_resolver: ClientSettingsResolver | None = None
_document_discovery_resolver: DocumentDiscoveryResolver | None = None


def set_client_settings_resolver(resolver: ClientSettingsResolver) -> None:
    global _client_settings_resolver
    _client_settings_resolver = resolver


def set_document_discovery_resolver(resolver: DocumentDiscoveryResolver) -> None:
    global _document_discovery_resolver
    _document_discovery_resolver = resolver


def get_client_settings(client_name: str) -> ClientSettings:
    if _client_settings_resolver is None:
        raise RuntimeError(
            "Client settings resolver is not configured. "
            "Call set_client_settings_resolver(...) during Liquyd setup."
        )

    return _client_settings_resolver(client_name)


def get_client_adapter(client_name: str) -> EngineMigrationAdapter:
    client_settings = get_client_settings(client_name)
    return client_settings.adapter_factory(client_settings)


def discover_documents() -> list[type]:
    if _document_discovery_resolver is None:
        raise RuntimeError(
            "Document discovery resolver is not configured. "
            "Call set_document_discovery_resolver(...) during Liquyd setup."
        )

    return _document_discovery_resolver()
