# src/liquyd/cli/commands/makemigrations.py
from __future__ import annotations

from pathlib import Path

from liquyd.migrations.differ import diff_snapshot_states
from liquyd.migrations.discovery import iter_documents
from liquyd.migrations.loader import get_last_migration, load_client_migrations
from liquyd.migrations.planner import plan_operations
from liquyd.migrations.replay import reconstruct_snapshot_state
from liquyd.migrations.snapshot import build_snapshot_state
from liquyd.migrations.writer import write_migration_file


def makemigrations(
    base_directory: Path,
    name: str | None = None,
) -> Path | None:
    discovered_documents = list(iter_documents())

    print("Discovered documents:")
    if not discovered_documents:
        print("  - <none>")
    else:
        for document_class in discovered_documents:
            print(f"  - {document_class.__module__}.{document_class.__name__}")

    current_snapshot_state = build_snapshot_state()
    migration_chain = load_client_migrations(base_directory=base_directory)
    last_migration = get_last_migration(base_directory=base_directory)

    previous_snapshot_state = None
    previous_migration_name = None

    if migration_chain:
        previous_snapshot_state = reconstruct_snapshot_state(migration_chain)

    if last_migration is not None:
        previous_migration_name = last_migration.name

    document_diffs = diff_snapshot_states(
        old_state=previous_snapshot_state,
        new_state=current_snapshot_state,
    )
    operations = plan_operations(document_diffs=document_diffs)

    if not operations:
        return None

    return write_migration_file(
        snapshot_state=current_snapshot_state,
        operations=operations,
        name=name,
        previous_migration_name=previous_migration_name,
        base_path=base_directory,
    )
