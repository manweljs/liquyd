# src/liquyd/migrations/writer.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast


def _serialize_value(value: Any) -> Any:
    if not isinstance(value, type) and is_dataclass(value):
        return asdict(cast(Any, value))

    if isinstance(value, list):
        return [_serialize_value(item) for item in value]

    if isinstance(value, dict):
        return {key: _serialize_value(item_value) for key, item_value in value.items()}

    return value


def write_migration_file(
    snapshot_state: Any,
    operations: list[Any],
    base_path: Path,
    name: str | None = None,
    previous_migration_name: str | None = None,
) -> Path:
    created_at = datetime.now(UTC)
    timestamp = created_at.strftime("%Y%m%d_%H%M%S")

    migration_name = timestamp
    if name:
        migration_name = f"{migration_name}_{name}"

    migration_file_path = base_path / f"{migration_name}.json"

    migration_payload = {
        "name": migration_name,
        "created_at": created_at.isoformat(),
        "previous": previous_migration_name,
        "operations": _serialize_value(operations),
        "snapshot": {},
    }

    file_content = json.dumps(
        migration_payload,
        indent=4,
        ensure_ascii=False,
    )

    migration_file_path.write_text(file_content + "\n", encoding="utf-8")
    return migration_file_path
