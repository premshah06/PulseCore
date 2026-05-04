"""GET /api/events — paginated event listing."""

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_db
from api.schemas import EventPage, EventRecord
from api.services import event_service

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=EventPage)
async def list_events(
    domain: str | None = Query(None, description="Filter by domain"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
) -> EventPage:
    try:
        items, total = await event_service.fetch_events(db, domain, limit, offset)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return EventPage(
        items=[EventRecord(**r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )
