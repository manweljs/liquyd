# src/liquyd/migrations/differ.py
from __future__ import annotations

from liquyd.migrations.types import (
    DocumentDiff,
    DocumentSnapshot,
    MigrationOperation,
    SnapshotState,
)


def _field_snapshot_to_dict(field_snapshot) -> dict:
    return {
        "name": field_snapshot.name,
        "python_type": field_snapshot.python_type,
        "engine_type": field_snapshot.engine_type,
        "nullable": field_snapshot.nullable,
        "primary_key": field_snapshot.primary_key,
    }


def _document_snapshot_to_dict(document_snapshot: DocumentSnapshot) -> dict:
    return {
        "document_name": document_snapshot.document_name,
        "index_name": document_snapshot.index_name,
        "fields": {
            field_name: _field_snapshot_to_dict(field_snapshot)
            for field_name, field_snapshot in document_snapshot.fields.items()
        },
    }


def _diff_document(
    old_document: DocumentSnapshot | None,
    new_document: DocumentSnapshot,
) -> DocumentDiff:
    operations: list[MigrationOperation] = []

    if old_document is None:
        operations.append(
            MigrationOperation(
                type="create_index",
                document_name=new_document.document_name,
                index_name=new_document.index_name,
                new_value=_document_snapshot_to_dict(new_document),
                message="Document is new and requires index creation.",
            )
        )
        return DocumentDiff(
            document_name=new_document.document_name,
            index_name=new_document.index_name,
            operations=operations,
        )

    old_field_names = set(old_document.fields.keys())
    new_field_names = set(new_document.fields.keys())

    added_fields = sorted(new_field_names - old_field_names)
    removed_fields = sorted(old_field_names - new_field_names)
    shared_fields = sorted(old_field_names & new_field_names)

    for field_name in added_fields:
        new_field = new_document.fields[field_name]
        operations.append(
            MigrationOperation(
                type="add_field",
                document_name=new_document.document_name,
                index_name=new_document.index_name,
                field_name=field_name,
                new_value=_field_snapshot_to_dict(new_field),
                message=f"Add field '{field_name}'.",
            )
        )

    for field_name in removed_fields:
        old_field = old_document.fields[field_name]
        operations.append(
            MigrationOperation(
                type="remove_field",
                document_name=new_document.document_name,
                index_name=new_document.index_name,
                field_name=field_name,
                old_value=_field_snapshot_to_dict(old_field),
                message=f"Field '{field_name}' was removed from the document.",
                breaking=True,
            )
        )

    for field_name in shared_fields:
        old_field = old_document.fields[field_name]
        new_field = new_document.fields[field_name]

        if old_field == new_field:
            continue

        operations.append(
            MigrationOperation(
                type="change_field",
                document_name=new_document.document_name,
                index_name=new_document.index_name,
                field_name=field_name,
                old_value=_field_snapshot_to_dict(old_field),
                new_value=_field_snapshot_to_dict(new_field),
                message=f"Field '{field_name}' changed.",
                breaking=True,
            )
        )

    return DocumentDiff(
        document_name=new_document.document_name,
        index_name=new_document.index_name,
        operations=operations,
    )


def _build_removed_document_diff(old_document: DocumentSnapshot) -> DocumentDiff:
    return DocumentDiff(
        document_name=old_document.document_name,
        index_name=old_document.index_name,
        operations=[
            MigrationOperation(
                type="delete_index",
                document_name=old_document.document_name,
                index_name=old_document.index_name,
                old_value=_document_snapshot_to_dict(old_document),
                message="Document was removed from the snapshot.",
                breaking=True,
            )
        ],
    )


def diff_snapshot_states(
    old_state: SnapshotState | None,
    new_state: SnapshotState,
) -> list[DocumentDiff]:
    document_diffs: list[DocumentDiff] = []

    old_documents = old_state.documents if old_state is not None else {}
    new_documents = new_state.documents

    all_document_names = sorted(set(old_documents.keys()) | set(new_documents.keys()))

    for document_name in all_document_names:
        old_document = old_documents.get(document_name)
        new_document = new_documents.get(document_name)

        if old_document is None and new_document is not None:
            document_diffs.append(
                _diff_document(
                    old_document=None,
                    new_document=new_document,
                )
            )
            continue

        if old_document is not None and new_document is None:
            document_diffs.append(_build_removed_document_diff(old_document))
            continue

        if old_document is not None and new_document is not None:
            document_diffs.append(
                _diff_document(
                    old_document=old_document,
                    new_document=new_document,
                )
            )

    return [
        document_diff for document_diff in document_diffs if not document_diff.is_empty
    ]
