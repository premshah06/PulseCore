from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class StreamEvent(BaseModel):
    """Canonical event schema. All phases consume this contract."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    domain: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metrics: dict[str, float]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id", "source_id")
    @classmethod
    def must_be_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must be a non-empty string")
        return v

    @field_validator("domain")
    @classmethod
    def domain_must_be_known(cls, v: str) -> str:
        allowed = {"infra", "ecommerce", "iot"}
        if v not in allowed:
            raise ValueError(f"domain must be one of {allowed}, got {v!r}")
        return v

    @field_validator("metrics")
    @classmethod
    def metrics_must_be_floats(cls, v: dict[str, float]) -> dict[str, float]:
        for key, val in v.items():
            if not isinstance(val, (int, float)):
                raise ValueError(f"metric {key!r} must be numeric, got {type(val)}")
        return {k: float(val) for k, val in v.items()}

    @model_validator(mode="after")
    def metrics_must_not_be_empty(self) -> StreamEvent:
        if not self.metrics:
            raise ValueError("metrics dict must contain at least one entry")
        return self

    model_config = {"frozen": True}
