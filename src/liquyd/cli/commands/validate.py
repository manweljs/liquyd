# validate.py
from __future__ import annotations

from pathlib import Path

from liquyd.migrations.registry import get_client_adapter, get_client_settings
from liquyd.migrations.state import extract_applied_migration_names
from liquyd.migrations.validator import validate_client_migrations, ValidationResult


def validate(client_name: str) -> ValidationResult:
    client_settings = get_client_settings(client_name)
    client_adapter = get_client_adapter(client_name)

    applied_migration_documents = client_adapter.read_applied_migration_documents()
    applied_migration_names = extract_applied_migration_names(
        migration_documents=applied_migration_documents
    )

    return validate_client_migrations(
        client_name=client_name,
        base_directory=Path(client_settings.migrations_directory),
        applied_migration_names=applied_migration_names,
    )
