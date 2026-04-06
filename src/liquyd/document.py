from __future__ import annotations

from typing import Any, cast

from .config import get_client_engine, get_default_client_name
from .document_registry import register_document
from .engines.registry import get_engine
from .exceptions import DocumentDefinitionError
from .property import Property


class DocumentMeta(type):
    def __new__(
        cls,
        name: str,
        bases: tuple[type[Any], ...],
        attrs: dict[str, Any],
    ) -> type[Any]:
        document_class = cast(
            type[Any],
            super().__new__(cls, name, bases, attrs),
        )

        properties: dict[str, Property] = {}

        for base_class in reversed(bases):
            base_properties = getattr(base_class, "__properties__", None)
            if base_properties:
                properties.update(base_properties)

        for attribute_name, attribute_value in attrs.items():
            if isinstance(attribute_value, Property):
                properties[attribute_name] = attribute_value

        setattr(document_class, "__properties__", properties)

        meta = getattr(document_class, "Meta", None)
        index_name = getattr(meta, "index", None) if meta else None
        setattr(document_class, "__index_name__", index_name)

        if name != "BaseDocument":
            register_document(document_class)

        return document_class


class BaseDocument(metaclass=DocumentMeta):
    __properties__: dict[str, Property]
    __index_name__: str | None = None

    def __init__(self, **kwargs: Any) -> None:
        self._data: dict[str, Any] = {}
        self._is_persisted = False

        unknown_fields = set(kwargs) - set(self.__properties__)
        if unknown_fields:
            unknown_field_list = ", ".join(sorted(unknown_fields))
            raise DocumentDefinitionError(
                f"Unknown field(s) for document '{self.__class__.__name__}': "
                f"{unknown_field_list}."
            )

        for property_name, property_instance in self.__properties__.items():
            if property_name in kwargs:
                value = kwargs[property_name]
            else:
                value = property_instance.get_default_value()

            validated_value = property_instance.validate(value)
            self._data[property_name] = validated_value

    @classmethod
    def get_index_name(cls) -> str:
        if not cls.__index_name__:
            raise DocumentDefinitionError(
                f"Document '{cls.__name__}' does not define Meta.index."
            )
        return cls.__index_name__

    @classmethod
    def get_properties(cls) -> dict[str, Property]:
        return dict(cls.__properties__)

    @classmethod
    def get_property(cls, name: str) -> Property:
        property_instance = cls.__properties__.get(name)
        if property_instance is None:
            raise DocumentDefinitionError(
                f"Property '{name}' is not defined on document '{cls.__name__}'."
            )
        return property_instance

    @classmethod
    def get_primary_key_property(cls) -> Property:
        primary_key_properties = [
            property_instance
            for property_instance in cls.__properties__.values()
            if property_instance.primary_key
        ]

        if not primary_key_properties:
            raise DocumentDefinitionError(
                f"Document '{cls.__name__}' does not define a primary key property."
            )

        if len(primary_key_properties) > 1:
            raise DocumentDefinitionError(
                f"Document '{cls.__name__}' defines multiple primary key properties."
            )

        return primary_key_properties[0]

    @classmethod
    def get_primary_key_name(cls) -> str:
        primary_key_property = cls.get_primary_key_property()
        if primary_key_property.attribute_name is None:
            raise DocumentDefinitionError(
                f"Primary key property name is not set on document '{cls.__name__}'."
            )
        return primary_key_property.attribute_name

    def get_primary_key_value(self) -> Any:
        primary_key_name = self.__class__.get_primary_key_name()
        return self._data.get(primary_key_name)

    def set_primary_key_value(self, value: Any) -> None:
        primary_key_name = self.__class__.get_primary_key_name()
        primary_key_property = self.__class__.get_primary_key_property()
        self._data[primary_key_name] = primary_key_property.validate(value)

    @classmethod
    def using(cls, client_name: str):
        from .queryset import QuerySet

        return QuerySet(
            cls,
            client_name=client_name,
        )

    @classmethod
    def has_property(cls, name: str) -> bool:
        return name in cls.__properties__

    def _get_property_value(self, name: str | None) -> Any:
        if name is None:
            raise DocumentDefinitionError("Property name is not set.")
        return self._data.get(name)

    def _set_property_value(self, name: str | None, value: Any) -> None:
        if name is None:
            raise DocumentDefinitionError("Property name is not set.")
        self._data[name] = value

    def to_dict(
        self,
        *,
        by_name: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for property_name, property_instance in self.__properties__.items():
            value = self._data.get(property_name)

            if exclude_none and value is None:
                continue

            output_key = property_instance.resolved_name if by_name else property_name
            result[output_key] = value

        return result

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        by_name: bool = False,
        is_persisted: bool = False,
    ) -> BaseDocument:
        if not by_name:
            instance = cls(**data)
            instance._is_persisted = is_persisted
            return instance

        normalized_data: dict[str, Any] = {}

        for property_name, property_instance in cls.__properties__.items():
            resolved_name = property_instance.resolved_name
            if resolved_name in data:
                normalized_data[property_name] = data[resolved_name]

        instance = cls(**normalized_data)
        instance._is_persisted = is_persisted
        return instance

    @classmethod
    def schema(cls) -> dict[str, Any]:
        return {
            "document": cls.__name__,
            "index": cls.__index_name__,
            "properties": {
                property_name: property_instance.export_definition()
                for property_name, property_instance in cls.__properties__.items()
            },
        }

    async def save(self, *, client_name: str | None = None) -> BaseDocument:
        resolved_client_name = client_name or get_default_client_name()
        engine_name = get_client_engine(resolved_client_name)
        engine_adapter = get_engine(engine_name)

        result = await engine_adapter.save_document(
            document_class=self.__class__,
            client_name=resolved_client_name,
            document_id=self.get_primary_key_value(),
            source=self.to_dict(
                by_name=True,
                exclude_none=True,
            ),
        )

        returned_document_id = result.get("document_id")
        if returned_document_id is not None:
            self.set_primary_key_value(returned_document_id)

        self._is_persisted = True
        return self

    async def delete(self, *, client_name: str | None = None) -> None:
        resolved_client_name = client_name or get_default_client_name()
        engine_name = get_client_engine(resolved_client_name)
        engine_adapter = get_engine(engine_name)

        document_id = self.get_primary_key_value()
        if document_id is None:
            raise DocumentDefinitionError(
                f"Cannot delete document '{self.__class__.__name__}' without a primary key value."
            )

        await engine_adapter.delete_document(
            document_class=self.__class__,
            client_name=resolved_client_name,
            document_id=document_id,
        )

        self._is_persisted = False

    def __repr__(self) -> str:
        field_parts = []
        for property_name in self.__properties__:
            field_parts.append(f"{property_name}={self._data.get(property_name)!r}")
        field_text = ", ".join(field_parts)
        return f"{self.__class__.__name__}({field_text})"

    @classmethod
    def filter(cls, **kwargs: Any):
        from .queryset import QuerySet

        return QuerySet(cls).filter(**kwargs)

    @classmethod
    async def first(cls, **kwargs: Any):
        return await cls.filter(**kwargs).first()

    @classmethod
    async def get(cls, **kwargs: Any):
        return await cls.filter(**kwargs).get()

    @classmethod
    async def get_or_none(cls, **kwargs: Any):
        return await cls.filter(**kwargs).first()
