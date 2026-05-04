"""Pydantic schemas for the Phase 5 FastAPI backend."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

_VALID_DOMAINS = {"infra", "ecommerce", "iot"}
_VALID_TIERS = {"auto_flag", "soft_alert", "log_only"}


class EventRecord(BaseModel):
    event_id: str
    source_id: str
    domain: str
    timestamp: datetime
    metrics: dict[str, Any]
    metadata: dict[str, Any]


class EventPage(BaseModel):
    items: list[EventRecord]
    total: int
    limit: int
    offset: int


class AnomalyRecord(BaseModel):
    id: str
    source_id: str
    domain: str
    timestamp: datetime
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    confidence_tier: Literal["auto_flag", "soft_alert", "log_only"]
    is_anomaly: bool
    raw_label: int
    latency_ms: float
    detected_at: datetime


class AnomalyPage(BaseModel):
    items: list[AnomalyRecord]
    total: int
    limit: int


class DomainSummary(BaseModel):
    domain: str
    event_count: int
    anomaly_count: int
    auto_flag_count: int
    avg_anomaly_score: float | None


class LiveUpdate(BaseModel):
    """WebSocket broadcast payload consumed by the Phase 6 dashboard."""
    type: Literal["anomaly"]
    data: AnomalyRecord
