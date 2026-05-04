"""Integration tests for GET /api/events."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from api.dependencies import get_db, get_ws_manager
from api.main import app
from api.services.ws_manager import WebSocketManager

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)

_EVENT_ROW = {
    "event_id": "evt-001",
    "source_id": "host-1",
    "domain": "infra",
    "timestamp": _NOW,
    "metrics": {"cpu_user_pct": 50.0},
    "metadata": {},
}


def _make_mock_db(count: int, docs: list[dict]) -> MagicMock:
    mock_db = MagicMock()
    mock_db.raw_events.count_documents = AsyncMock(return_value=count)
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=docs)
    mock_db.raw_events.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
    return mock_db


def _make_client(count: int, rows: list[dict]) -> TestClient:
    mock_db = _make_mock_db(count, rows)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ws_manager] = lambda: WebSocketManager()
    return TestClient(app, raise_server_exceptions=True)


def _teardown():
    app.dependency_overrides.clear()


# ── Happy path ─────────────────────────────────────────────────────────────────

class TestGetEventsHappyPath:
    def setup_method(self):
        self.client = _make_client(1, [_EVENT_ROW])

    def teardown_method(self):
        _teardown()

    def test_returns_200(self):
        resp = self.client.get("/api/events")
        assert resp.status_code == 200

    def test_response_is_event_page(self):
        data = self.client.get("/api/events").json()
        assert "items" in data and "total" in data and "limit" in data and "offset" in data

    def test_items_contains_event(self):
        data = self.client.get("/api/events").json()
        assert len(data["items"]) == 1
        assert data["items"][0]["event_id"] == "evt-001"

    def test_total_is_returned(self):
        data = self.client.get("/api/events").json()
        assert data["total"] == 1

    def test_domain_filter_accepted(self):
        resp = self.client.get("/api/events?domain=infra")
        assert resp.status_code == 200

    def test_limit_param_accepted(self):
        resp = self.client.get("/api/events?limit=10")
        assert resp.status_code == 200

    def test_offset_param_accepted(self):
        resp = self.client.get("/api/events?offset=5")
        assert resp.status_code == 200

    def test_limit_echoed_in_response(self):
        data = self.client.get("/api/events?limit=25").json()
        assert data["limit"] == 25

    def test_offset_echoed_in_response(self):
        data = self.client.get("/api/events?offset=10").json()
        assert data["offset"] == 10


# ── Empty result ───────────────────────────────────────────────────────────────

class TestGetEventsEmpty:
    def setup_method(self):
        self.client = _make_client(0, [])

    def teardown_method(self):
        _teardown()

    def test_returns_200_when_empty(self):
        assert self.client.get("/api/events").status_code == 200

    def test_items_empty_list(self):
        data = self.client.get("/api/events").json()
        assert data["items"] == []

    def test_total_zero(self):
        data = self.client.get("/api/events").json()
        assert data["total"] == 0


# ── Invalid inputs ─────────────────────────────────────────────────────────────

class TestGetEventsValidation:
    def setup_method(self):
        self.client = _make_client(0, [])

    def teardown_method(self):
        _teardown()

    def test_invalid_domain_returns_422(self):
        resp = self.client.get("/api/events?domain=blockchain")
        assert resp.status_code == 422

    def test_limit_zero_returns_422(self):
        resp = self.client.get("/api/events?limit=0")
        assert resp.status_code == 422

    def test_limit_over_500_returns_422(self):
        resp = self.client.get("/api/events?limit=501")
        assert resp.status_code == 422

    def test_negative_offset_returns_422(self):
        resp = self.client.get("/api/events?offset=-1")
        assert resp.status_code == 422
