from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .exceptions import PropertyDefinitionError

from .types import EngineType


@dataclass(frozen=True)
class PropertyOptions:
    index: bool = True
    nullable: bool = True
    default: Any = None
    name: str | None = None
    primary_key: bool = False


class PropertyDefinition:
    def __init__(
        self,
        engine_type: EngineType,
        *,
        index: bool = True,
        nullable: bool = True,
        default: Any = None,
        name: str | None = None,
        primary_key: bool = False,
    ) -> None:
        if primary_key:
            nullable = False

        self.engine_type = engine_type
        self.python_type: type[Any] | tuple[type[Any], ...] | None = None
        self.options = PropertyOptions(
            index=index,
            nullable=nullable,
            default=default,
            name=name,
            primary_key=primary_key,
        )
        self.attribute_name: str | None = None

    @property
    def resolved_name(self) -> str:
        if self.options.name:
            return self.options.name
        if self.attribute_name is None:
            raise PropertyDefinitionError(
                "Property name is not set. Make sure the property is declared on a document class."
            )
        return self.attribute_name

    @property
    def primary_key(self) -> bool:
        return self.options.primary_key

    def bind(
        self,
        *,
        attribute_name: str,
        python_type: type[Any] | tuple[type[Any], ...] | None,
    ) -> None:
        self.attribute_name = attribute_name
        self.python_type = python_type

    def get_default_value(self) -> Any:
        default_value = self.options.default
        if callable(default_value):
            return default_value()
        return default_value

    def validate(self, value: Any) -> Any:
        if value is None:
            if not self.options.nullable:
                raise PropertyDefinitionError(
                    f"Property '{self.attribute_name}' does not allow null values."
                )
            return value

        if self.python_type is None:
            return value

        if not isinstance(value, self.python_type):
            expected_type_name = self._get_expected_type_name()
            actual_type_name = type(value).__name__
            raise PropertyDefinitionError(
                f"Property '{self.attribute_name}' expected value of type "
                f"'{expected_type_name}', got '{actual_type_name}'."
            )

        return value

    def to_mapping(self) -> dict[str, Any]:
        mapping: dict[str, Any] = {
            "type": self.engine_type,
        }

        if not self.options.index:
            mapping["index"] = False

        return mapping

    def export_definition(self) -> dict[str, Any]:
        return {
            "attribute_name": self.attribute_name,
            "name": self.resolved_name,
            "engine_type": self.engine_type,
            "python_type": self._get_expected_type_name(),
            "index": self.options.index,
            "nullable": self.options.nullable,
            "default": self.options.default,
            "primary_key": self.options.primary_key,
        }

    def _get_expected_type_name(self) -> str | None:
        if self.python_type is None:
            return None

        if isinstance(self.python_type, tuple):
            return ", ".join(single_type.__name__ for single_type in self.python_type)

        return self.python_type.__name__


class BoundProperty:
    def __init__(self, definition: PropertyDefinition) -> None:
        self.definition = definition

    def __get__(self, instance: Any, owner: type[Any]) -> Any:
        if instance is None:
            return self.definition
        return instance._get_property_value(self.definition.attribute_name)

    def __set__(self, instance: Any, value: Any) -> None:
        validated_value = self.definition.validate(value)
        instance._set_property_value(self.definition.attribute_name, validated_value)


def Property(
    engine_type: EngineType,
    *,
    index: bool = True,
    nullable: bool = True,
    default: Any = None,
    name: str | None = None,
    primary_key: bool = False,
) -> Any:
    return PropertyDefinition(
        engine_type=engine_type,
        index=index,
        nullable=nullable,
        default=default,
        name=name,
        primary_key=primary_key,
    )
