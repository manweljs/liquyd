# src/liquyd/runtime.py
from __future__ import annotations

from threading import RLock
from typing import Any

from .config import (
    clear_configuration,
    configure,
    get_all_client_names,
    get_client_engine,
)
from .engines.registry import get_engine


class LiquydRuntimeState:
    def __init__(self) -> None:
        self._lock = RLock()
        self._started = False

    def start(self) -> None:
        with self._lock:
            if self._started:
                raise RuntimeError("Liquyd runtime is already started.")
            self._started = True

    def stop(self) -> None:
        with self._lock:
            self._started = False

    def is_started(self) -> bool:
        with self._lock:
            return self._started


_runtime_state = LiquydRuntimeState()


def ensure_runtime_started() -> None:
    if not _runtime_state.is_started():
        raise RuntimeError(
            "Liquyd runtime is not started. Create Liquyd(...) and await start() first."
        )


def is_runtime_started() -> bool:
    return _runtime_state.is_started()


class Liquyd:
    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
        clients: dict[str, dict[str, Any]] | None = None,
        default_client_name: str | None = None,
    ) -> None:
        if config is None and not clients:
            raise ValueError("Liquyd requires 'config' or 'clients'.")

        self._config = dict(config) if config is not None else None
        self._clients = dict(clients) if clients is not None else None
        self._default_client_name = default_client_name
        self._started = False

    async def start(self) -> None:
        if self._started:
            return

        _runtime_state.start()

        try:
            if self._config is not None:
                configure(default=self._config)
            else:
                configure(
                    clients=self._clients,
                    default_client_name=self._default_client_name,
                )
        except Exception:
            _runtime_state.stop()
            raise

        self._started = True

    async def close(self) -> None:
        if not self._started:
            return

        client_names = list(get_all_client_names())

        try:
            for client_name in client_names:
                engine_name = get_client_engine(client_name)
                engine = get_engine(engine_name)
                await engine.close_client(client_name)
        finally:
            clear_configuration()
            _runtime_state.stop()
            self._started = False
