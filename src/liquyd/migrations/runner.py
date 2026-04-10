# src/liquyd/migrations/runner.py
from __future__ import annotations

from pathlib import Path
from typing import Callable

from liquyd.migrations.loader import iter_pending_migrations
from liquyd.migrations.state import build_applied_migration_record
from liquyd.migrations.types import MigrationFile


OperationHandler = Callable[[dict], None]
MigrationRecordWriter = Callable[[dict], None]


def _run_operation(
    operation: dict,
    operation_handlers: dict[str, OperationHandler],
) -> None:
    operation_type = operation["type"]
    operation_handler = operation_handlers.get(operation_type)

    if operation_handler is None:
        raise ValueError(
            f"No migration handler is registered for operation type "
            f"'{operation_type}'."
        )

    operation_handler(operation)


def apply_migration(
    migration: MigrationFile,
    operation_handlers: dict[str, OperationHandler],
    record_writer: MigrationRecordWriter,
    allow_breaking: bool = False,
) -> None:
    for operation in migration.operations:
        _run_operation(
            operation=operation,
            operation_handlers=operation_handlers,
        )

    applied_record = build_applied_migration_record(
        migration_name=migration.name,
        document_snapshot=migration.snapshot,
        operations=migration.operations,
    )
    record_writer(applied_record.to_document())


def migrate_client(
    base_directory: str | Path,
    applied_migration_names: list[str],
    operation_handlers: dict[str, OperationHandler],
    record_writer: MigrationRecordWriter,
    allow_breaking: bool = False,
) -> list[str]:
    pending_migrations = iter_pending_migrations(
        base_directory=Path(base_directory),
        applied_migration_names=applied_migration_names,
    )

    applied_now: list[str] = []

    for migration in pending_migrations:
        apply_migration(
            migration=migration,
            operation_handlers=operation_handlers,
            record_writer=record_writer,
            allow_breaking=allow_breaking,
        )
        applied_now.append(migration.name)

    return applied_now
