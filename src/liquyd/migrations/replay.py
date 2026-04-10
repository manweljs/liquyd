# src/liquyd/migrations/replay.py
from __future__ import annotations

from liquyd.migrations.types import (
    DocumentSnapshot,
    FieldSnapshot,
    MigrationFile,
    SnapshotState,
)


def _field_snapshot_from_dict(field_data: dict) -> FieldSnapshot:
    return FieldSnapshot(
        name=field_data["name"],
        python_type=field_data["python_type"],
        engine_type=field_data["engine_type"],
        nullable=field_data["nullable"],
        primary_key=field_data.get("primary_key", False),
    )


def _document_snapshot_from_dict(document_data: dict) -> DocumentSnapshot:
    return DocumentSnapshot(
        document_name=document_data["document_name"],
        index_name=document_data["index_name"],
        fields={
            field_name: _field_snapshot_from_dict(field_snapshot)
            for field_name, field_snapshot in document_data.get("fields", {}).items()
        },
    )


def reconstruct_snapshot_state(migrations: list[MigrationFile]) -> SnapshotState:
    documents: dict[str, DocumentSnapshot] = {}

    for migration in migrations:
        for operation in migration.operations:
            operation_type = operation["type"]
            document_name = operation["document_name"]

            if operation_type == "create_index":
                new_document = operation.get("new_value")
                if not new_document:
                    raise ValueError(
                        f"Migration '{migration.name}' create_index is missing new_value"
                    )

                documents[document_name] = _document_snapshot_from_dict(new_document)
                continue

            if operation_type == "delete_index":
                documents.pop(document_name, None)
                continue

            if operation_type == "reindex_required":
                continue

            document_snapshot = documents.get(document_name)
            if document_snapshot is None:
                raise ValueError(
                    f"Migration '{migration.name}' references document "
                    f"'{document_name}' before it exists in replay state"
                )

            if operation_type == "add_field":
                field_name = operation.get("field_name")
                new_field = operation.get("new_value")
                if not field_name or not new_field:
                    raise ValueError(
                        f"Migration '{migration.name}' add_field is incomplete"
                    )

                document_snapshot.fields[field_name] = _field_snapshot_from_dict(
                    new_field
                )
                continue

            if operation_type == "remove_field":
                field_name = operation.get("field_name")
                if not field_name:
                    raise ValueError(
                        f"Migration '{migration.name}' remove_field is missing field_name"
                    )

                document_snapshot.fields.pop(field_name, None)
                continue

            if operation_type == "change_field":
                field_name = operation.get("field_name")
                new_field = operation.get("new_value")
                if not field_name or not new_field:
                    raise ValueError(
                        f"Migration '{migration.name}' change_field is incomplete"
                    )

                document_snapshot.fields[field_name] = _field_snapshot_from_dict(
                    new_field
                )
                continue

            raise ValueError(
                f"Migration '{migration.name}' has unsupported operation type '{operation_type}'"
            )

    return SnapshotState(documents=documents)
