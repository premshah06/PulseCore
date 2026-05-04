"""Integration tests for GET /api/anomalies and POST /api/anomalies."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from api.dependencies import get_db, get_ws_manager
from api.main import app
from api.services.ws_manager import WebSocketManager

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
_NOW_ISO = _NOW.isoformat()
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

_ANOMALY_PAYLOAD = {
    "source_id": "host-1",
    "domain": "infra",
    "timestamp": _NOW_ISO,
    "anomaly_score": 0.92,
    "confidence_tier": "auto_flag",
    "is_anomaly": True,
    "raw_label": -1,
    "latency_ms": 1.5,
}


def _make_mock_db_list(count: int, docs: list[dict]) -> MagicMock:
    mock_db = MagicMock()
    mock_db.anomalies.count_documents = AsyncMock(return_value=count)
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=docs)
    mock_db.anomalies.find.return_value.sort.return_value.limit.return_value = mock_cursor
    return mock_db


def _make_mock_db_insert() -> MagicMock:
    mock_db = MagicMock()
    mock_db.anomalies.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=_MOCK_OID)
    )
    return mock_db


def _make_client(count: int, rows: list[dict]) -> TestClient:
    mock_db = _make_mock_db_list(count, rows)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ws_manager] = lambda: WebSocketManager()
    return TestClient(app, raise_server_exceptions=True)


def _teardown():
    app.dependency_overrides.clear()


# ── GET /api/anomalies happy path ──────────────────────────────────────────────

class TestGetAnomaliesHappyPath:
    def setup_method(self):
        self.client = _make_client(1, [_ANOMALY_ROW])

    def teardown_method(self):
        _teardown()

    def test_returns_200(self):
        assert self.client.get("/api/anomalies").status_code == 200

    def test_response_has_items_total_limit(self):
        data = self.client.get("/api/anomalies").json()
        assert "items" in data and "total" in data and "limit" in data

    def test_item_fields_present(self):
        data = self.client.get("/api/anomalies").json()
        item = data["items"][0]
        for field in ("id", "source_id", "domain", "timestamp", "anomaly_score",
                      "confidence_tier", "is_anomaly", "raw_label", "latency_ms"):
            assert field in item, f"Missing field: {field!r}"

    def test_tier_filter_accepted(self):
        assert self.client.get("/api/anomalies?tier=auto_flag").status_code == 200

    def test_since_filter_accepted(self):
        resp = self.client.get("/api/anomalies", params={"since": _NOW_ISO})
        assert resp.status_code == 200

    def test_limit_param_accepted(self):
        assert self.client.get("/api/anomalies?limit=10").status_code == 200


# ── GET /api/anomalies empty ───────────────────────────────────────────────────

class TestGetAnomaliesEmpty:
    def setup_method(self):
        self.client = _make_client(0, [])

    def teardown_method(self):
        _teardown()

    def test_returns_200(self):
        assert self.client.get("/api/anomalies").status_code == 200

    def test_empty_items(self):
        data = self.client.get("/api/anomalies").json()
        assert data["items"] == []

    def test_total_zero(self):
        data = self.client.get("/api/anomalies").json()
        assert data["total"] == 0


# ── GET /api/anomalies validation ─────────────────────────────────────────────

class TestGetAnomaliesValidation:
    def setup_method(self):
        self.client = _make_client(0, [])

    def teardown_method(self):
        _teardown()

    def test_invalid_tier_returns_422(self):
        assert self.client.get("/api/anomalies?tier=critical").status_code == 422

    def test_invalid_since_returns_422(self):
        assert self.client.get("/api/anomalies?since=not-a-date").status_code == 422

    def test_limit_zero_returns_422(self):
        assert self.client.get("/api/anomalies?limit=0").status_code == 422


# ── POST /api/anomalies happy path ─────────────────────────────────────────────

class TestPostAnomalyHappyPath:
    def setup_method(self):
        mock_db = _make_mock_db_insert()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_ws_manager] = lambda: WebSocketManager()
        self.client = TestClient(app, raise_server_exceptions=True)

    def teardown_method(self):
        _teardown()

    def test_returns_201(self):
        resp = self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD)
        assert resp.status_code == 201

    def test_response_is_anomaly_record(self):
        data = self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD).json()
        assert "id" in data

    def test_response_has_detected_at(self):
        data = self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD).json()
        assert "detected_at" in data

    def test_source_id_echoed(self):
        data = self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD).json()
        assert data["source_id"] == "host-1"

    def test_domain_echoed(self):
        data = self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD).json()
        assert data["domain"] == "infra"


# ── POST /api/anomalies validation ────────────────────────────────────────────

class TestPostAnomalyValidation:
    def setup_method(self):
        mock_db = _make_mock_db_insert()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_ws_manager] = lambda: WebSocketManager()
        self.client = TestClient(app, raise_server_exceptions=True)

    def teardown_method(self):
        _teardown()

    def test_missing_source_id_returns_422(self):
        payload = {**_ANOMALY_PAYLOAD}
        del payload["source_id"]
        assert self.client.post("/api/anomalies", json=payload).status_code == 422

    def test_invalid_domain_returns_422(self):
        payload = {**_ANOMALY_PAYLOAD, "domain": "blockchain"}
        assert self.client.post("/api/anomalies", json=payload).status_code == 422

    def test_score_out_of_range_returns_422(self):
        payload = {**_ANOMALY_PAYLOAD, "anomaly_score": 1.5}
        assert self.client.post("/api/anomalies", json=payload).status_code == 422

    def test_invalid_tier_returns_422(self):
        payload = {**_ANOMALY_PAYLOAD, "confidence_tier": "critical"}
        assert self.client.post("/api/anomalies", json=payload).status_code == 422

    def test_empty_body_returns_422(self):
        assert self.client.post("/api/anomalies", content=b"").status_code == 422
