# src/liquyd/migrations/loader.py
from __future__ import annotations

import json
from pathlib import Path

from liquyd.migrations.state import is_migration_applied
from liquyd.migrations.types import MigrationFile


def _iter_migration_files(base_directory: Path) -> list[Path]:
    return sorted(base_directory.glob("*.json"))


def load_client_migrations(base_directory: Path) -> list[MigrationFile]:
    return [
        load_migration_file(migration_file_path)
        for migration_file_path in _iter_migration_files(base_directory)
    ]


def get_last_migration(base_directory: Path) -> MigrationFile | None:
    migration_files = _iter_migration_files(base_directory)
    if not migration_files:
        return None

    return load_migration_file(migration_files[-1])


def iter_pending_migrations(
    base_directory: Path,
    applied_migration_names: list[str],
) -> list[MigrationFile]:
    pending_migrations: list[MigrationFile] = []

    for migration_file_path in _iter_migration_files(base_directory):
        migration = load_migration_file(migration_file_path)
        if is_migration_applied(
            migration_name=migration.name,
            applied_migration_names=applied_migration_names,
        ):
            continue

        pending_migrations.append(migration)

    return pending_migrations


def load_migration_file(migration_file_path: Path) -> MigrationFile:
    migration = json.loads(migration_file_path.read_text(encoding="utf-8"))

    return MigrationFile(
        name=migration["name"],
        created_at=migration.get("created_at", ""),
        previous_migration_name=migration.get("previous"),
        snapshot=migration.get("snapshot", {}),
        operations=migration["operations"],
        path=str(migration_file_path),
    )
