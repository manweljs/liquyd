# makemigrations.py
from __future__ import annotations

from pathlib import Path

from liquyd.migrations.differ import diff_snapshot_states
from liquyd.migrations.loader import get_last_migration
from liquyd.migrations.planner import plan_operations
from liquyd.migrations.registry import get_client_settings
from liquyd.migrations.snapshot import (
    build_snapshot_state,
    build_snapshot_state_from_dict,
)
from liquyd.migrations.writer import write_migration_file


def makemigrations(
    client_name: str,
    name: str | None = None,
) -> Path | None:
    client_settings = get_client_settings(client_name)
    base_directory = Path(client_settings.migrations_directory)

    current_snapshot_state = build_snapshot_state(client_name=client_name)
    last_migration = get_last_migration(
        base_directory=base_directory,
        client_name=client_name,
    )

    previous_snapshot_state = None
    previous_migration_name = None

    if last_migration is not None:
        previous_snapshot_state = build_snapshot_state_from_dict(
            last_migration.snapshot
        )
        previous_migration_name = last_migration.name

    document_diffs = diff_snapshot_states(
        old_state=previous_snapshot_state,
        new_state=current_snapshot_state,
    )
    operations = plan_operations(document_diffs=document_diffs)

    if not operations:
        return None

    return write_migration_file(
        client_name=client_name,
        snapshot_state=current_snapshot_state,
        operations=operations,
        name=name,
        previous_migration_name=previous_migration_name,
        base_path=base_directory,
    )
