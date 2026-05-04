"""Unit tests for consumer/pipeline.py — no Kafka, no real HTTP, no real DB."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from consumer.pipeline import _FALLBACK_RESULT, score_event
from producer.models import StreamEvent

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

_EVENT = StreamEvent(
    source_id="host-1",
    domain="infra",
    timestamp=_NOW,
    metrics={"cpu_percent": 45.0},
)

_INFERENCE_RESULT = {
    "anomaly_score": 0.92,
    "confidence_tier": "auto_flag",
    "is_anomaly": True,
    "raw_label": -1,
    "latency_ms": 2.3,
}

_ANOMALY_ID = "507f1f77bcf86cd799439011"


def _make_http_client(status_code: int = 200, json_body: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body or _INFERENCE_RESULT
    resp.raise_for_status = MagicMock()

    client = MagicMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=resp)
    client.get = AsyncMock(return_value=resp)
    return client


def _make_db() -> MagicMock:
    db = MagicMock()
    db.anomalies.insert_one = AsyncMock(return_value=MagicMock(inserted_id=_ANOMALY_ID))
    return db


class TestScoreEvent:
    @pytest.mark.asyncio
    async def test_calls_inference_sidecar(self):
        http = _make_http_client()
        db = _make_db()

        with patch("consumer.pipeline.write_anomaly", new=AsyncMock(return_value=_ANOMALY_ID)):
            await score_event(_EVENT, db, http, "http://sidecar:8001",
                              "http://api:8000", "secret", 0.5)

        http.post.assert_any_await(
            "http://sidecar:8001/predict",
            json={
                "source_id": "host-1",
                "domain": "infra",
                "metrics": {"cpu_percent": 45.0},
                "timestamp": _NOW.isoformat(),
            },
            timeout=0.5,
        )

    @pytest.mark.asyncio
    async def test_writes_anomaly_after_inference(self):
        http = _make_http_client()
        db = _make_db()

        with patch("consumer.pipeline.write_anomaly", new=AsyncMock(return_value=_ANOMALY_ID)) as mock_write:
            await score_event(_EVENT, db, http, "http://sidecar:8001",
                              "http://api:8000", "secret", 0.5)

        mock_write.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcasts_after_successful_write(self):
        http = _make_http_client()
        db = _make_db()

        with patch("consumer.pipeline.write_anomaly", new=AsyncMock(return_value=_ANOMALY_ID)):
            await score_event(_EVENT, db, http, "http://sidecar:8001",
                              "http://api:8000", "secret", 0.5)

        broadcast_calls = [
            call for call in http.post.call_args_list
            if "/internal/broadcast" in str(call)
        ]
        assert len(broadcast_calls) == 1

    @pytest.mark.asyncio
    async def test_continues_on_inference_timeout(self):
        http = MagicMock(spec=httpx.AsyncClient)
        http.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        db = _make_db()

        with patch("consumer.pipeline.write_anomaly", new=AsyncMock(return_value=_ANOMALY_ID)):
            await score_event(_EVENT, db, http, "http://sidecar:8001",
                              "http://api:8000", "secret", 0.5)

    @pytest.mark.asyncio
    async def test_continues_on_inference_connect_error(self):
        http = MagicMock(spec=httpx.AsyncClient)
        http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        db = _make_db()

        with patch("consumer.pipeline.write_anomaly", new=AsyncMock(return_value=_ANOMALY_ID)):
            await score_event(_EVENT, db, http, "http://sidecar:8001",
                              "http://api:8000", "secret", 0.5)

    @pytest.mark.asyncio
    async def test_fallback_used_when_inference_fails(self):
        http = MagicMock(spec=httpx.AsyncClient)
        http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))
        db = _make_db()

        written_results = []

        async def _capture_write(db, event, result):
            written_results.append(result)
            return _ANOMALY_ID

        with patch("consumer.pipeline.write_anomaly", new=_capture_write):
            await score_event(_EVENT, db, http, "http://sidecar:8001",
                              "http://api:8000", "secret", 0.5)

        assert written_results[0]["confidence_tier"] == "log_only"
        assert written_results[0]["is_anomaly"] is False

    @pytest.mark.asyncio
    async def test_skips_broadcast_when_write_fails(self):
        http = _make_http_client()
        db = _make_db()

        with patch("consumer.pipeline.write_anomaly", new=AsyncMock(return_value=None)):
            await score_event(_EVENT, db, http, "http://sidecar:8001",
                              "http://api:8000", "secret", 0.5)

        broadcast_calls = [
            call for call in http.post.call_args_list
            if "/internal/broadcast" in str(call)
        ]
        assert len(broadcast_calls) == 0
