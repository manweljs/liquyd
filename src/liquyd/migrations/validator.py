from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List

from liquyd.migrations.loader import get_last_migration, load_client_migrations
from liquyd.migrations.snapshot import build_snapshot_state
from liquyd.migrations.types import MigrationFile


@dataclass(frozen=True)
class ValidationResult:
    client_name: str
    is_in_sync: bool
    has_migrations: bool
    has_pending_migrations: bool
    schema_changed: bool
    current_snapshot: dict
    last_migration_name: str | None
    last_migration_snapshot: dict | None
    pending_migration_names: List[str]


def _get_pending_migration_names(
    migrations: List[MigrationFile],
    applied_migration_names: Iterable[str],
) -> List[str]:
    applied_migration_name_set = set(applied_migration_names)
    return [
        migration.name
        for migration in migrations
        if migration.name not in applied_migration_name_set
    ]


def validate_client_migrations(
    client_name: str,
    base_directory: str | Path,
    applied_migration_names: Iterable[str] | None = None,
) -> ValidationResult:
    applied_migration_names = applied_migration_names or []

    current_snapshot_state = build_snapshot_state(client_name=client_name)
    current_snapshot = asdict(current_snapshot_state)

    migrations = load_client_migrations(
        base_directory=Path(base_directory),
        client_name=client_name,
    )
    last_migration = get_last_migration(
        base_directory=Path(base_directory),
        client_name=client_name,
    )

    pending_migration_names = _get_pending_migration_names(
        migrations=migrations,
        applied_migration_names=applied_migration_names,
    )

    if last_migration is None:
        return ValidationResult(
            client_name=client_name,
            is_in_sync=False,
            has_migrations=False,
            has_pending_migrations=False,
            schema_changed=True,
            current_snapshot=current_snapshot,
            last_migration_name=None,
            last_migration_snapshot=None,
            pending_migration_names=[],
        )

    last_migration_snapshot = last_migration.snapshot
    schema_changed = current_snapshot != last_migration_snapshot
    has_pending_migrations = len(pending_migration_names) > 0

    return ValidationResult(
        client_name=client_name,
        is_in_sync=not schema_changed and not has_pending_migrations,
        has_migrations=True,
        has_pending_migrations=has_pending_migrations,
        schema_changed=schema_changed,
        current_snapshot=current_snapshot,
        last_migration_name=last_migration.name,
        last_migration_snapshot=last_migration_snapshot,
        pending_migration_names=pending_migration_names,
    )
