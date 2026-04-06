from __future__ import annotations

from threading import RLock

from ..exceptions import BindingError
from .base import EngineAdapter


class EngineRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._engines: dict[str, EngineAdapter] = {}

    def register(self, engine: EngineAdapter) -> None:
        engine_name = engine.name.strip()

        if not engine_name:
            raise BindingError("Engine name cannot be empty.")

        with self._lock:
            self._engines[engine_name] = engine

    def get(self, engine_name: str) -> EngineAdapter:
        engine = self._engines.get(engine_name)
        if engine is None:
            raise BindingError(f"Engine '{engine_name}' is not registered.")
        return engine

    def has(self, engine_name: str) -> bool:
        return engine_name in self._engines

    def unregister(self, engine_name: str) -> None:
        with self._lock:
            self._engines.pop(engine_name, None)

    def clear(self) -> None:
        with self._lock:
            self._engines = {}

    def list_names(self) -> list[str]:
        return list(self._engines.keys())


_registry = EngineRegistry()


def register_engine(engine: EngineAdapter) -> None:
    _registry.register(engine)


def get_engine(engine_name: str) -> EngineAdapter:
    return _registry.get(engine_name)


def has_engine(engine_name: str) -> bool:
    return _registry.has(engine_name)


def unregister_engine(engine_name: str) -> None:
    _registry.unregister(engine_name)


def clear_engines() -> None:
    _registry.clear()


def list_engine_names() -> list[str]:
    return _registry.list_names()
