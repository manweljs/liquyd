from __future__ import annotations

from typing import Any, Literal, Mapping, MutableMapping, TypeAlias


ClientName: TypeAlias = str
ClientConfigKey: TypeAlias = str

PrimitiveValue: TypeAlias = str | int | float | bool | None
PropertyValue: TypeAlias = PrimitiveValue | list[PrimitiveValue]

DocumentData: TypeAlias = dict[str, Any]
DocumentSource: TypeAlias = Mapping[str, Any]
MutableDocumentSource: TypeAlias = MutableMapping[str, Any]

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

ClientConfig: TypeAlias = dict[str, Any]
ClientConfigMap: TypeAlias = dict[ClientName, ClientConfig]

EngineSearchParams: TypeAlias = Mapping[str, Any]
EngineQueryBody: TypeAlias = Mapping[str, Any]
