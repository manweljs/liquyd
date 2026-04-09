# src/liquyd/migrations/types.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


OperationType = Literal[
    "create_index",
    "delete_index",
    "add_field",
    "remove_field",
    "change_field",
    "reindex_required",
]


@dataclass(frozen=True)
class FieldSnapshot:
    name: str
    python_type: str
    engine_type: str
    nullable: bool
    primary_key: bool = False


@dataclass(frozen=True)
class DocumentSnapshot:
    document_name: str
    index_name: str
    fields: dict[str, FieldSnapshot]


@dataclass(frozen=True)
class SnapshotState:
    documents: dict[str, DocumentSnapshot]


@dataclass(frozen=True)
class MigrationOperation:
    type: OperationType
    document_name: str
    index_name: str
    field_name: str | None = None
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    message: str | None = None
    breaking: bool = False


@dataclass(frozen=True)
class DocumentDiff:
    document_name: str
    index_name: str
    operations: list[MigrationOperation] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.operations) == 0

    @property
    def has_breaking_changes(self) -> bool:
        return any(operation.breaking for operation in self.operations)


SnapshotDict = Dict[str, Any]
OperationDict = Dict[str, Any]


@dataclass(frozen=True)
class MigrationFile:
    name: str
    created_at: str
    previous_migration_name: Optional[str]
    snapshot: SnapshotDict
    operations: List[OperationDict]
    path: str
