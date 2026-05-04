"""Internal-only endpoints called by the consumer, not exposed externally."""

import os

from fastapi import APIRouter, Depends, Header, HTTPException

from api.dependencies import get_ws_manager
from api.schemas import LiveUpdate

router = APIRouter(prefix="/internal", tags=["internal"])


@router.post("/broadcast", status_code=200)
async def broadcast(
    body: LiveUpdate,
    x_internal_secret: str | None = Header(None),
    ws_manager=Depends(get_ws_manager),
) -> dict:
    """Fan-out a LiveUpdate to subscribed WebSocket clients.

    Rejects requests that are missing or present the wrong X-Internal-Secret.
    Only the consumer service (running inside the Docker network) should call this.
    """
    secret = os.getenv("INTERNAL_SECRET", "")
    if not secret or x_internal_secret != secret:
        raise HTTPException(status_code=403, detail="Forbidden")
    await ws_manager.broadcast(body.model_dump(mode="json"), domain=body.data.domain)
    return {"ok": True}
