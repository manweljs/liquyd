# migrate.py
from __future__ import annotations

from pathlib import Path

from liquyd.migrations.registry import get_client_adapter, get_client_settings
from liquyd.migrations.runner import migrate_client
from liquyd.migrations.state import extract_applied_migration_names


def migrate(
    client_name: str,
    allow_breaking: bool = False,
) -> list[str]:
    client_settings = get_client_settings(client_name)
    client_adapter = get_client_adapter(client_name)

    applied_migration_documents = client_adapter.read_applied_migration_documents()
    applied_migration_names = extract_applied_migration_names(
        migration_documents=applied_migration_documents
    )

    return migrate_client(
        client_name=client_name,
        base_directory=Path(client_settings.migrations_directory),
        applied_migration_names=applied_migration_names,
        operation_handlers=client_adapter.get_operation_handlers(),
        record_writer=client_adapter.write_applied_migration_record,
        allow_breaking=allow_breaking,
    )
