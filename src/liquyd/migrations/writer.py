from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from liquyd.migrations.types import (
    MigrationFile,
    MigrationOperation,
    SnapshotState,
)


def get_migrations_root(base_path: str | Path | None = None) -> Path:
    if base_path is not None:
        return Path(base_path)

    return Path.cwd() / "migrations"


def ensure_client_directory(
    client_name: str,
    base_path: str | Path | None = None,
) -> Path:
    client_directory = get_migrations_root(base_path=base_path) / client_name
    client_directory.mkdir(parents=True, exist_ok=True)
    return client_directory


def build_migration_name(name: str | None = None) -> tuple[str, str]:
    created_at = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    suffix = name or "auto"
    migration_name = f"{created_at}_{suffix}"
    return migration_name, created_at


def write_migration_file(
    client_name: str,
    snapshot_state: SnapshotState,
    operations: list[MigrationOperation],
    name: str | None = None,
    previous_migration_name: Optional[str] = None,
    base_path: str | Path | None = None,
) -> Path:
    migration_name, created_at = build_migration_name(name=name)
    client_directory = ensure_client_directory(
        client_name=client_name,
        base_path=base_path,
    )
    output_path = client_directory / f"{migration_name}.json"

    migration_file = MigrationFile(
        name=migration_name,
        client_name=client_name,
        created_at=created_at,
        previous_migration_name=previous_migration_name,
        snapshot=asdict(snapshot_state),
        operations=[asdict(operation) for operation in operations],
        path=str(output_path),
    )

    output_path.write_text(
        json.dumps(asdict(migration_file), indent=4, sort_keys=True),
        encoding="utf-8",
    )
    return output_path
