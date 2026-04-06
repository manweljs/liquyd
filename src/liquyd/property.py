from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .exceptions import PropertyDefinitionError


@dataclass(frozen=True)
class PropertyOptions:
    index: bool = True
    nullable: bool = True
    default: Any = None
    name: str | None = None
    primary_key: bool = False


class Property:
    def __init__(
        self,
        python_type: type[Any] | tuple[type[Any], ...] | None = None,
        *,
        index: bool = True,
        nullable: bool = True,
        default: Any = None,
        name: str | None = None,
        primary_key: bool = False,
    ) -> None:
        if primary_key:
            nullable = False
        if primary_key and nullable:
            raise PropertyDefinitionError("Primary key property cannot be nullable.")

        self.python_type = python_type
        self.options = PropertyOptions(
            index=index,
            nullable=nullable,
            default=default,
            name=name,
            primary_key=primary_key,
        )
        self.attribute_name: str | None = None

    def __set_name__(self, owner: type[Any], name: str) -> None:
        self.attribute_name = name

    def __get__(self, instance: Any, owner: type[Any]) -> Any:
        if instance is None:
            return self
        return instance._get_property_value(self.attribute_name)

    def __set__(self, instance: Any, value: Any) -> None:
        validated_value = self.validate(value)
        instance._set_property_value(self.attribute_name, validated_value)

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

    def export_definition(self) -> dict[str, Any]:
        return {
            "attribute_name": self.attribute_name,
            "name": self.resolved_name,
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
