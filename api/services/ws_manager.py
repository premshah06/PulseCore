"""WebSocket connection manager with optional domain-based filtering."""

import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Tracks active WebSocket connections, grouped by optional domain filter.

    Connections subscribed to domain=None receive all broadcasts.
    Connections subscribed to a specific domain receive only broadcasts for
    that domain AND all-domain broadcasts.
    """

    def __init__(self) -> None:
        # domain (str | None) → set of active WebSocket connections
        self._connections: dict[str | None, set[WebSocket]] = defaultdict(set)

    async def connect(self, ws: WebSocket, domain: str | None = None) -> None:
        await ws.accept()
        self._connections[domain].add(ws)
        logger.debug("WS connected: domain=%s total=%d", domain, self._total())

    def disconnect(self, ws: WebSocket, domain: str | None = None) -> None:
        self._connections[domain].discard(ws)
        logger.debug("WS disconnected: domain=%s total=%d", domain, self._total())

    async def broadcast(self, message: dict, domain: str | None = None) -> None:
        """Send message to all subscribers for `domain` and all wildcard (None) subscribers."""
        targets: set[WebSocket] = set()
        targets |= self._connections.get(domain, set()).copy()
        targets |= self._connections.get(None, set()).copy()

        dead: set[tuple[WebSocket, str | None]] = set()
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                # Stale connection — remove silently; do not re-raise
                key = domain if ws in self._connections.get(domain, set()) else None
                dead.add((ws, key))

        for ws, key in dead:
            self._connections[key].discard(ws)

    def connection_count(self, domain: str | None = None) -> int:
        return len(self._connections.get(domain, set()))

    def _total(self) -> int:
        return sum(len(v) for v in self._connections.values())
