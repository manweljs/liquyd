from __future__ import annotations

from typing import Literal, TypeAlias

ClientName: TypeAlias = str
ClientConfigKey: TypeAlias = str

PrimitiveValue: TypeAlias = str | int | float | bool | None
PropertyValue: TypeAlias = PrimitiveValue | list[PrimitiveValue]

DocumentData: TypeAlias = dict[str, object]
DocumentSource: TypeAlias = dict[str, object]

QueryOperator: TypeAlias = Literal[
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "contains",
    "exists",
]

EngineType: TypeAlias = Literal[
    "keyword",
    "text",
    "integer",
    "long",
    "short",
    "byte",
    "double",
    "float",
    "half_float",
    "scaled_float",
    "boolean",
    "date",
    "object",
    "nested",
]

ClientConfig: TypeAlias = dict[str, object]
ClientConfigMap: TypeAlias = dict[ClientName, ClientConfig]

EngineSearchParams: TypeAlias = dict[str, object]
EngineQueryBody: TypeAlias = dict[str, object]
