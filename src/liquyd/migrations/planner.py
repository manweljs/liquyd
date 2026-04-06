from __future__ import annotations

from liquyd.migrations.types import DocumentDiff, MigrationOperation


def plan_operations(document_diffs: list[DocumentDiff]) -> list[MigrationOperation]:
    operations: list[MigrationOperation] = []

    for document_diff in document_diffs:
        operations.extend(document_diff.operations)

        if document_diff.has_breaking_changes:
            operations.append(
                MigrationOperation(
                    type="reindex_required",
                    document_name=document_diff.document_name,
                    index_name=document_diff.index_name,
                    message=(
                        f"Document '{document_diff.document_name}' has breaking "
                        "changes and may require reindex."
                    ),
                    breaking=True,
                )
            )

    return operations
