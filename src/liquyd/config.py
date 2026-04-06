from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any

from .exceptions import ClientNotConfiguredError, ConfigurationError
from .types import ClientConfigMap, ClientName


@dataclass(frozen=True)
class ClientDefinition:
    name: ClientName
    engine: str
    config: dict[str, Any]


class LiquydConfigRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._clients: dict[ClientName, ClientDefinition] = {}
        self._default_client_name: ClientName | None = None

    def configure(
        self,
        *,
        default: dict[str, Any] | None = None,
        clients: ClientConfigMap | None = None,
        default_client_name: ClientName | None = None,
    ) -> None:
        normalized_clients: dict[ClientName, ClientDefinition] = {}

        if default is not None:
            normalized_clients["default"] = self._build_client_definition(
                name="default",
                client_config=default,
            )

        if clients:
            for client_name, client_config in clients.items():
                normalized_clients[client_name] = self._build_client_definition(
                    name=client_name,
                    client_config=client_config,
                )

        if not normalized_clients:
            raise ConfigurationError(
                "Liquyd configure() requires at least one client configuration."
            )

        resolved_default_client_name = self._resolve_default_client_name(
            normalized_clients=normalized_clients,
            explicit_default_client_name=default_client_name,
            has_default_argument=default is not None,
        )

        with self._lock:
            self._clients = normalized_clients
            self._default_client_name = resolved_default_client_name

    def get_client_definition(self, name: ClientName | None = None) -> ClientDefinition:
        resolved_client_name = name or self._default_client_name
        if not resolved_client_name:
            raise ClientNotConfiguredError("Liquyd default client is not configured.")

        client_definition = self._clients.get(resolved_client_name)
        if client_definition is None:
            raise ClientNotConfiguredError(
                f"Liquyd client '{resolved_client_name}' is not configured."
            )

        return client_definition

    def get_client_config(self, name: ClientName | None = None) -> dict[str, Any]:
        return dict(self.get_client_definition(name).config)

    def get_client_engine(self, name: ClientName | None = None) -> str:
        return self.get_client_definition(name).engine

    def get_default_client_name(self) -> ClientName:
        if not self._default_client_name:
            raise ClientNotConfiguredError("Liquyd default client is not configured.")
        return self._default_client_name

    def get_all_client_names(self) -> list[ClientName]:
        return list(self._clients.keys())

    def has_client(self, name: ClientName) -> bool:
        return name in self._clients

    def is_configured(self) -> bool:
        return bool(self._clients)

    def clear(self) -> None:
        with self._lock:
            self._clients = {}
            self._default_client_name = None

    def _build_client_definition(
        self,
        *,
        name: ClientName,
        client_config: dict[str, Any],
    ) -> ClientDefinition:
        normalized_config = dict(client_config)
        engine_name = normalized_config.pop("engine", None)

        if not engine_name:
            raise ConfigurationError(f"Liquyd client '{name}' must define a engine.")

        return ClientDefinition(
            name=name,
            engine=engine_name,
            config=normalized_config,
        )

    def _resolve_default_client_name(
        self,
        *,
        normalized_clients: dict[ClientName, ClientDefinition],
        explicit_default_client_name: ClientName | None,
        has_default_argument: bool,
    ) -> ClientName:
        if explicit_default_client_name:
            if explicit_default_client_name not in normalized_clients:
                raise ConfigurationError(
                    f"Liquyd default client '{explicit_default_client_name}' is not configured."
                )
            return explicit_default_client_name

        if has_default_argument:
            return "default"

        if len(normalized_clients) == 1:
            return next(iter(normalized_clients))

        raise ConfigurationError(
            "Liquyd default client is ambiguous. Set default_client_name explicitly."
        )


_registry = LiquydConfigRegistry()


def configure(
    *,
    default: dict[str, Any] | None = None,
    clients: ClientConfigMap | None = None,
    default_client_name: ClientName | None = None,
) -> None:
    _registry.configure(
        default=default,
        clients=clients,
        default_client_name=default_client_name,
    )


def get_client_definition(name: ClientName | None = None) -> ClientDefinition:
    return _registry.get_client_definition(name)


def get_client_config(name: ClientName | None = None) -> dict[str, Any]:
    return _registry.get_client_config(name)


def get_client_engine(name: ClientName | None = None) -> str:
    return _registry.get_client_engine(name)


def get_default_client_name() -> ClientName:
    return _registry.get_default_client_name()


def get_all_client_names() -> list[ClientName]:
    return _registry.get_all_client_names()


def has_client(name: ClientName) -> bool:
    return _registry.has_client(name)


def is_configured() -> bool:
    return _registry.is_configured()


def clear_configuration() -> None:
    _registry.clear()
