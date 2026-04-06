from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Iterable, List


def get_migration_index_name(client_name: str) -> str:
    return f"liquyd_migrations_{client_name}"


@dataclass(frozen=True)
class AppliedMigrationRecord:
    migration_name: str
    client_name: str
    applied_at: str
    document_snapshot: dict[str, Any]
    operations: list[dict[str, Any]]

    def to_document(self) -> dict[str, Any]:
        return {
            "migration_name": self.migration_name,
            "client_name": self.client_name,
            "applied_at": self.applied_at,
            "document_snapshot": self.document_snapshot,
            "operations": self.operations,
        }


def build_applied_migration_record(
    migration_name: str,
    client_name: str,
    document_snapshot: dict[str, Any],
    operations: list[dict[str, Any]],
) -> AppliedMigrationRecord:
    return AppliedMigrationRecord(
        migration_name=migration_name,
        client_name=client_name,
        applied_at=datetime.now(UTC).isoformat(),
        document_snapshot=document_snapshot,
        operations=operations,
    )


def extract_applied_migration_names(
    migration_documents: Iterable[dict[str, Any]],
) -> List[str]:
    applied_migration_names: List[str] = []

    for migration_document in migration_documents:
        migration_name = migration_document.get("migration_name")
        if not migration_name:
            continue

        applied_migration_names.append(str(migration_name))

    return applied_migration_names


def is_migration_applied(
    migration_name: str,
    applied_migration_names: Iterable[str],
) -> bool:
    return migration_name in set(applied_migration_names)
