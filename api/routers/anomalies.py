"""GET /api/anomalies — filtered listing; POST /api/anomalies — ingest from sidecar."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_db, get_ws_manager
from api.schemas import AnomalyPage, AnomalyRecord, LiveUpdate
from api.services import anomaly_service
from inference.schemas import AnomalyResult

router = APIRouter(prefix="/api/anomalies", tags=["anomalies"])


@router.get("", response_model=AnomalyPage)
async def list_anomalies(
    tier: str | None = Query(None, description="Filter by confidence tier"),
    since: datetime | None = Query(None, description="ISO-8601 lower bound on timestamp"),
    limit: int = Query(50, ge=1, le=500),
    db=Depends(get_db),
) -> AnomalyPage:
    try:
        items, total = await anomaly_service.fetch_anomalies(db, tier, since, limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return AnomalyPage(
        items=[AnomalyRecord(**r) for r in items],
        total=total,
        limit=limit,
    )


@router.post("", response_model=AnomalyRecord, status_code=201)
async def ingest_anomaly(
    body: AnomalyResult,
    db=Depends(get_db),
    ws_manager=Depends(get_ws_manager),
) -> AnomalyRecord:
    record_dict = await anomaly_service.ingest_anomaly(db, body.model_dump())
    record = AnomalyRecord(**record_dict)

    update = LiveUpdate(type="anomaly", data=record)
    await ws_manager.broadcast(update.model_dump(mode="json"), domain=record.domain)

    return record
