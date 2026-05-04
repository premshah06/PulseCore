"""GET /api/stats/summary — per-domain aggregate statistics."""

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_db
from api.schemas import DomainSummary
from api.services import stats_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary", response_model=list[DomainSummary])
async def get_summary(
    domain: str | None = Query(None, description="Filter to a single domain"),
    db=Depends(get_db),
) -> list[DomainSummary]:
    try:
        rows = await stats_service.fetch_summary(db, domain)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return [DomainSummary(**r) for r in rows]
