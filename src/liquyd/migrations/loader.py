from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from .types import MigrationFile


def get_client_migrations_directory(base_directory: Path, client_name: str) -> Path:
    return base_directory / client_name


def ensure_client_migrations_directory(base_directory: Path, client_name: str) -> Path:
    client_migrations_directory = get_client_migrations_directory(
        base_directory=base_directory,
        client_name=client_name,
    )
    client_migrations_directory.mkdir(parents=True, exist_ok=True)
    return client_migrations_directory


def list_migration_paths(base_directory: Path, client_name: str) -> List[Path]:
    client_migrations_directory = get_client_migrations_directory(
        base_directory=base_directory,
        client_name=client_name,
    )

    if not client_migrations_directory.exists():
        return []

    migration_paths = [
        path
        for path in client_migrations_directory.iterdir()
        if path.is_file() and path.suffix == ".json"
    ]
    return sorted(migration_paths)


def load_migration_file(migration_path: Path) -> MigrationFile:
    migration_payload = json.loads(migration_path.read_text(encoding="utf-8"))

    return MigrationFile(
        name=migration_payload["name"],
        client_name=migration_payload["client_name"],
        created_at=migration_payload["created_at"],
        previous_migration_name=migration_payload.get("previous_migration_name"),
        snapshot=migration_payload["snapshot"],
        operations=migration_payload["operations"],
        path=str(migration_path),
    )


def load_client_migrations(
    base_directory: Path, client_name: str
) -> List[MigrationFile]:
    migration_paths = list_migration_paths(
        base_directory=base_directory,
        client_name=client_name,
    )
    return [load_migration_file(migration_path) for migration_path in migration_paths]


def get_last_migration(base_directory: Path, client_name: str) -> MigrationFile | None:
    migrations = load_client_migrations(
        base_directory=base_directory,
        client_name=client_name,
    )
    if not migrations:
        return None
    return migrations[-1]


def iter_pending_migrations(
    base_directory: Path,
    client_name: str,
    applied_migration_names: Iterable[str],
) -> List[MigrationFile]:
    applied_migration_name_set = set(applied_migration_names)
    migrations = load_client_migrations(
        base_directory=base_directory,
        client_name=client_name,
    )

    return [
        migration
        for migration in migrations
        if migration.name not in applied_migration_name_set
    ]
