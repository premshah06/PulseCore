"""Unit tests for api/services/anomaly_service.py (MongoDB/motor)."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.services.anomaly_service import fetch_anomalies, ingest_anomaly

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
_MOCK_OID = "507f1f77bcf86cd799439011"

_ANOMALY_ROW = {
    "id": _MOCK_OID,
    "source_id": "host-1",
    "domain": "infra",
    "timestamp": _NOW,
    "anomaly_score": 0.92,
    "confidence_tier": "auto_flag",
    "is_anomaly": True,
    "raw_label": -1,
    "latency_ms": 1.5,
    "detected_at": _NOW,
}


def _make_db_list(count: int, docs: list[dict]) -> MagicMock:
    mock_db = MagicMock()
    mock_db.anomalies.count_documents = AsyncMock(return_value=count)
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=docs)
    mock_db.anomalies.find.return_value.sort.return_value.limit.return_value = mock_cursor
    return mock_db


def _make_db_insert() -> MagicMock:
    mock_db = MagicMock()
    mock_db.anomalies.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=_MOCK_OID)
    )
    return mock_db


# ── fetch_anomalies happy path ─────────────────────────────────────────────────

class TestFetchAnomaliesHappyPath:
    @pytest.mark.asyncio
    async def test_returns_tuple(self):
        db = _make_db_list(1, [_ANOMALY_ROW])
        items, total = await fetch_anomalies(db, None, None, 50)
        assert isinstance(items, list) and isinstance(total, int)

    @pytest.mark.asyncio
    async def test_total_matches_count(self):
        db = _make_db_list(7, [])
        _, total = await fetch_anomalies(db, None, None, 50)
        assert total == 7

    @pytest.mark.asyncio
    async def test_items_are_dicts(self):
        db = _make_db_list(1, [_ANOMALY_ROW])
        items, _ = await fetch_anomalies(db, None, None, 50)
        assert isinstance(items[0], dict)

    @pytest.mark.asyncio
    async def test_tier_filter_passed_to_count(self):
        db = _make_db_list(0, [])
        await fetch_anomalies(db, "auto_flag", None, 50)
        db.anomalies.count_documents.assert_awaited_once_with(
            {"confidence_tier": "auto_flag"}
        )

    @pytest.mark.asyncio
    async def test_since_filter_passed_to_count(self):
        db = _make_db_list(0, [])
        await fetch_anomalies(db, None, _NOW, 50)
        db.anomalies.count_documents.assert_awaited_once_with(
            {"timestamp": {"$gte": _NOW}}
        )

    @pytest.mark.asyncio
    async def test_both_filters_forwarded(self):
        db = _make_db_list(0, [])
        await fetch_anomalies(db, "soft_alert", _NOW, 50)
        db.anomalies.count_documents.assert_awaited_once_with(
            {"confidence_tier": "soft_alert", "timestamp": {"$gte": _NOW}}
        )


# ── fetch_anomalies empty ──────────────────────────────────────────────────────

class TestFetchAnomaliesEmpty:
    @pytest.mark.asyncio
    async def test_empty_items_and_zero_total(self):
        db = _make_db_list(0, [])
        items, total = await fetch_anomalies(db, None, None, 50)
        assert items == [] and total == 0


# ── fetch_anomalies invalid tier ───────────────────────────────────────────────

class TestFetchAnomaliesInvalidTier:
    @pytest.mark.asyncio
    async def test_invalid_tier_raises_value_error(self):
        db = _make_db_list(0, [])
        with pytest.raises(ValueError, match="Invalid tier"):
            await fetch_anomalies(db, "critical", None, 50)

    @pytest.mark.asyncio
    async def test_invalid_tier_names_the_value(self):
        db = _make_db_list(0, [])
        with pytest.raises(ValueError, match="critical"):
            await fetch_anomalies(db, "critical", None, 50)

    @pytest.mark.asyncio
    async def test_invalid_tier_does_not_call_db(self):
        db = _make_db_list(0, [])
        try:
            await fetch_anomalies(db, "bad", None, 50)
        except ValueError:
            pass
        db.anomalies.count_documents.assert_not_awaited()


# ── ingest_anomaly ─────────────────────────────────────────────────────────────

class TestIngestAnomaly:
    @pytest.mark.asyncio
    async def test_returns_dict(self):
        db = _make_db_insert()
        data = {
            "source_id": "host-1", "domain": "infra", "timestamp": _NOW,
            "anomaly_score": 0.92, "confidence_tier": "auto_flag",
            "is_anomaly": True, "raw_label": -1, "latency_ms": 1.5,
        }
        result = await ingest_anomaly(db, data)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_result_has_id(self):
        db = _make_db_insert()
        data = {
            "source_id": "h", "domain": "infra", "timestamp": _NOW,
            "anomaly_score": 0.9, "confidence_tier": "auto_flag",
            "is_anomaly": True, "raw_label": -1, "latency_ms": 1.0,
        }
        result = await ingest_anomaly(db, data)
        assert "id" in result

    @pytest.mark.asyncio
    async def test_insert_called_once(self):
        db = _make_db_insert()
        data = {
            "source_id": "h", "domain": "infra", "timestamp": _NOW,
            "anomaly_score": 0.9, "confidence_tier": "auto_flag",
            "is_anomaly": True, "raw_label": -1, "latency_ms": 1.0,
        }
        await ingest_anomaly(db, data)
        db.anomalies.insert_one.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_result_id_is_string(self):
        db = _make_db_insert()
        data = {
            "source_id": "h", "domain": "infra", "timestamp": _NOW,
            "anomaly_score": 0.9, "confidence_tier": "auto_flag",
            "is_anomaly": True, "raw_label": -1, "latency_ms": 1.0,
        }
        result = await ingest_anomaly(db, data)
        assert isinstance(result["id"], str)
