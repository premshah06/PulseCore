"""WebSocket endpoint — real-time anomaly push."""

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

_VALID_DOMAINS = {"infra", "ecommerce", "iot"}


@router.websocket("/ws")
async def websocket_endpoint(
    ws: WebSocket,
    domain: str | None = Query(None, description="Subscribe to a specific domain"),
) -> None:
    if domain is not None and domain not in _VALID_DOMAINS:
        await ws.close(code=4422, reason=f"Invalid domain: {domain!r}")
        return

    # Access the shared manager directly from app state; Depends() cannot inject
    # app-state singletons into WebSocket routes in the same way as HTTP routes.
    manager = ws.app.state.ws_manager
    await manager.connect(ws, domain=domain)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws, domain=domain)
