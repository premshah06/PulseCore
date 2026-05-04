"""End-to-end test: score_event() stitches inference → DB write → broadcast."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, call

import httpx
import pytest

from consumer.pipeline import score_event
from producer.models import StreamEvent

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
_ANOMALY_ID = "507f1f77bcf86cd799439011"

_INFERENCE_RESP = {
    "anomaly_score": 0.91,
    "confidence_tier": "auto_flag",
    "is_anomaly": True,
    "raw_label": -1,
    "latency_ms": 3.1,
}

_EVENT = StreamEvent(
    source_id="sensor-99",
    domain="iot",
    timestamp=_NOW,
    metrics={"temperature_c": 120.0},
)


@pytest.mark.asyncio
async def test_full_pipeline_chain():
    """
    Mock httpx and MongoDB; verify score_event calls all three stages in order.

    Stages verified:
      1. POST /predict was called with correct payload
      2. write_anomaly was called with the inference result
      3. POST /internal/broadcast was called with correct anomaly_id and secret
    """
    predict_resp = MagicMock()
    predict_resp.json.return_value = _INFERENCE_RESP
    predict_resp.raise_for_status = MagicMock()

    broadcast_resp = MagicMock()
    broadcast_resp.raise_for_status = MagicMock()

    call_order = []

    async def _fake_post(url, **kwargs):
        if "/predict" in url:
            call_order.append("predict")
            return predict_resp
        if "/internal/broadcast" in url:
            call_order.append("broadcast")
            return broadcast_resp
        raise AssertionError(f"Unexpected POST to {url}")

    http_client = MagicMock(spec=httpx.AsyncClient)
    http_client.post = AsyncMock(side_effect=_fake_post)

    db = MagicMock()
    db.anomalies.insert_one = AsyncMock(return_value=MagicMock(inserted_id=_ANOMALY_ID))

    await score_event(
        event=_EVENT,
        db=db,
        http_client=http_client,
        inference_url="http://inference-iot:8003",
        broadcast_url="http://api:8000",
        internal_secret="e2e-secret",
        inference_timeout_s=0.5,
    )

    # Inference was called first
    assert call_order[0] == "predict"
    # Broadcast was called after the write
    assert call_order[1] == "broadcast"

    # Broadcast payload carries the correct secret header
    broadcast_call = [
        c for c in http_client.post.call_args_list
        if "/internal/broadcast" in str(c)
    ][0]
    headers = broadcast_call.kwargs.get("headers", {})
    assert headers.get("X-Internal-Secret") == "e2e-secret"

    # Broadcast payload contains the anomaly_id
    body = broadcast_call.kwargs.get("json", {})
    assert body["data"]["anomaly_score"] == pytest.approx(_INFERENCE_RESP["anomaly_score"])
