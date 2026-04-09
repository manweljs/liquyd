# src/liquyd/migrations/snapshot.py
from __future__ import annotations

from typing import Any, get_args, get_origin

from liquyd.migrations.discovery import iter_documents
from liquyd.migrations.types import DocumentSnapshot, FieldSnapshot, SnapshotState


def _normalize_python_type(annotation: Any) -> str:
    if annotation is None:
        return "None"

    origin = get_origin(annotation)
    if origin is None:
        if hasattr(annotation, "__name__"):
            return annotation.__name__
        return str(annotation)

    origin_name = getattr(origin, "__name__", str(origin))
    args = ", ".join(
        _normalize_python_type(argument) for argument in get_args(annotation)
    )
    return f"{origin_name}[{args}]"


def _build_field_snapshot(
    field_name: str,
    property_instance: Any,
    annotation: Any,
) -> FieldSnapshot:
    return FieldSnapshot(
        name=property_instance.resolved_name,
        python_type=_normalize_python_type(annotation),
        engine_type=property_instance.engine_type,
        nullable=property_instance.options.nullable,
        primary_key=property_instance.primary_key,
    )


def _build_field_snapshot_from_dict(payload: dict[str, Any]) -> FieldSnapshot:
    return FieldSnapshot(
        name=payload["name"],
        python_type=payload["python_type"],
        engine_type=payload["engine_type"],
        nullable=payload["nullable"],
        primary_key=payload.get("primary_key", False),
    )


def _build_document_snapshot_from_dict(payload: dict[str, Any]) -> DocumentSnapshot:
    return DocumentSnapshot(
        document_name=payload["document_name"],
        index_name=payload["index_name"],
        fields={
            field_name: _build_field_snapshot_from_dict(field_payload)
            for field_name, field_payload in payload["fields"].items()
        },
    )


def build_document_snapshot(document_class: type) -> DocumentSnapshot:
    annotations = getattr(document_class, "__annotations__", {})
    declared_properties = getattr(document_class, "__properties__", {})
    index_name = document_class.get_index_name()

    fields: dict[str, FieldSnapshot] = {}
    for field_name, property_instance in declared_properties.items():
        annotation = annotations.get(field_name)
        fields[field_name] = _build_field_snapshot(
            field_name=field_name,
            property_instance=property_instance,
            annotation=annotation,
        )

    return DocumentSnapshot(
        document_name=document_class.__name__,
        index_name=index_name,
        fields=fields,
    )


def build_snapshot_state() -> SnapshotState:
    documents: dict[str, DocumentSnapshot] = {}

    for document_class in iter_documents():
        snapshot = build_document_snapshot(document_class=document_class)
        documents[snapshot.document_name] = snapshot

    return SnapshotState(documents=documents)


def build_snapshot_state_from_dict(payload: dict[str, Any]) -> SnapshotState:
    return SnapshotState(
        documents={
            document_name: _build_document_snapshot_from_dict(document_payload)
            for document_name, document_payload in payload["documents"].items()
        }
    )
