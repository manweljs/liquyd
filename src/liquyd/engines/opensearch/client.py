from __future__ import annotations

from threading import RLock

from opensearchpy import AsyncOpenSearch

from ...config import get_client_config
from ...types import ClientName


class OpenSearchClientRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._clients: dict[ClientName, AsyncOpenSearch] = {}

    def get_client(self, client_name: ClientName | None = None) -> AsyncOpenSearch:
        resolved_client_name = client_name or "default"

        with self._lock:
            existing_client = self._clients.get(resolved_client_name)
            if existing_client is not None:
                return existing_client

            client_config = get_client_config(client_name)
            client = AsyncOpenSearch(**client_config)
            self._clients[resolved_client_name] = client
            return client

    async def close_client(self, client_name: ClientName | None = None) -> None:
        resolved_client_name = client_name or "default"

        with self._lock:
            client = self._clients.pop(resolved_client_name, None)

        if client is not None:
            await client.close()

    async def close_all(self) -> None:
        with self._lock:
            clients = list(self._clients.values())
            self._clients = {}

        for client in clients:
            await client.close()


_registry = OpenSearchClientRegistry()


def get_opensearch_client(client_name: ClientName | None = None) -> AsyncOpenSearch:
    return _registry.get_client(client_name)


async def close_opensearch_client(client_name: ClientName | None = None) -> None:
    await _registry.close_client(client_name)


async def close_all_opensearch_clients() -> None:
    await _registry.close_all()
