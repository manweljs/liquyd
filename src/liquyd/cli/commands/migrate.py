# src/liquyd/cli/commands/migrate.py
from __future__ import annotations

from pathlib import Path
from typing import Callable

from liquyd.migrations.runner import migrate_client
from liquyd.migrations.state import extract_applied_migration_names


def migrate(
    base_directory: str | Path,
    applied_migration_documents: list[dict],
    operation_handlers: dict[str, Callable[[dict], None]],
    record_writer: Callable[[dict], None],
    allow_breaking: bool = False,
) -> list[str]:
    applied_migration_names = extract_applied_migration_names(
        migration_documents=applied_migration_documents
    )

    return migrate_client(
        base_directory=Path(base_directory),
        applied_migration_names=applied_migration_names,
        operation_handlers=operation_handlers,
        record_writer=record_writer,
        allow_breaking=allow_breaking,
    )
