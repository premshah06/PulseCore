"""PredictRequest and AnomalyResult — canonical contract from CONTRACTS.md.

Phase 5 depends on AnomalyResult's field names and types verbatim.
Any change here must be reflected in CONTRACTS.md and Phase 5 simultaneously.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Input to POST /predict.  metrics must contain all keys required by
    the model's feature_map.json entry for the specified domain."""

    source_id: str = Field(..., min_length=1)
    domain: Literal["infra", "ecommerce", "iot"]
    metrics: dict[str, float]
    timestamp: datetime


class AnomalyResult(BaseModel):
    """Output of POST /predict.  Shape is pinned by test_anomaly_result_contract.py."""

    source_id: str
    domain: Literal["infra", "ecommerce", "iot"]
    timestamp: datetime
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="0=normal, 1=anomalous")
    confidence_tier: Literal["auto_flag", "soft_alert", "log_only"]
    is_anomaly: bool = Field(..., description="True iff confidence_tier == 'auto_flag'")
    raw_label: int = Field(..., description="ONNX output label: 1=normal, -1=anomaly")
    latency_ms: float = Field(..., description="Wall-clock inference time in milliseconds")
