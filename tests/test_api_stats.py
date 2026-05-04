"""Integration tests for GET /api/stats/summary."""

from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from api.dependencies import get_db, get_ws_manager
from api.main import app
from api.services.ws_manager import WebSocketManager

_SUMMARY_ROW = {
    "domain": "infra",
    "event_count": 100,
    "anomaly_count": 5,
    "auto_flag_count": 2,
    "avg_anomaly_score": 0.75,
}

_ALL_SUMMARY_ROWS = [
    {"domain": "ecommerce", "event_count": 50, "anomaly_count": 3,
     "auto_flag_count": 1, "avg_anomaly_score": 0.65},
    {"domain": "infra", "event_count": 100, "anomaly_count": 5,
     "auto_flag_count": 2, "avg_anomaly_score": 0.75},
    {"domain": "iot", "event_count": 200, "anomaly_count": 10,
     "auto_flag_count": 4, "avg_anomaly_score": 0.80},
]


def _make_mock_db_single(row: dict) -> MagicMock:
    """Mock db for a single-domain summary query."""
    mock_db = MagicMock()
    mock_db.raw_events.count_documents = AsyncMock(return_value=row["event_count"])
    mock_db.anomalies.count_documents = AsyncMock(
        side_effect=[row["anomaly_count"], row["auto_flag_count"]]
    )
    avg_doc = [{"avg": row["avg_anomaly_score"]}] if row["avg_anomaly_score"] is not None else []
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=avg_doc)
    mock_db.anomalies.aggregate.return_value = mock_cursor
    return mock_db


def _make_mock_db_all(rows: list[dict]) -> MagicMock:
    """Mock db for all-domains summary query (3 domains)."""
    mock_db = MagicMock()

    event_counts = [r["event_count"] for r in rows]
    anomaly_counts = []
    auto_flag_counts = []
    for r in rows:
        anomaly_counts.append(r["anomaly_count"])
        auto_flag_counts.append(r["auto_flag_count"])

    # count_documents is called: event×3, anomaly×3, auto_flag×3 = 9 calls total
    # raw_events.count_documents called 3×, anomalies.count_documents called 6×
    mock_db.raw_events.count_documents = AsyncMock(side_effect=event_counts)
    mock_db.anomalies.count_documents = AsyncMock(
        side_effect=[v for pair in zip(anomaly_counts, auto_flag_counts) for v in pair]
    )

    # aggregate cursor called once per domain
    def _make_avg_cursor(row):
        c = MagicMock()
        avg = [{"avg": row["avg_anomaly_score"]}] if row["avg_anomaly_score"] is not None else []
        c.to_list = AsyncMock(return_value=avg)
        return c

    mock_db.anomalies.aggregate.side_effect = [_make_avg_cursor(r) for r in rows]
    return mock_db


def _make_client_single(row: dict) -> TestClient:
    mock_db = _make_mock_db_single(row)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ws_manager] = lambda: WebSocketManager()
    return TestClient(app, raise_server_exceptions=True)


def _make_client_all(rows: list[dict]) -> TestClient:
    mock_db = _make_mock_db_all(rows)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ws_manager] = lambda: WebSocketManager()
    return TestClient(app, raise_server_exceptions=True)


def _make_client_empty() -> TestClient:
    mock_db = MagicMock()
    mock_db.raw_events.count_documents = AsyncMock(return_value=0)
    mock_db.anomalies.count_documents = AsyncMock(return_value=0)
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    mock_db.anomalies.aggregate.return_value = mock_cursor
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_ws_manager] = lambda: WebSocketManager()
    return TestClient(app, raise_server_exceptions=True)


def _teardown():
    app.dependency_overrides.clear()


# ── All domains (no filter) ────────────────────────────────────────────────────

class TestGetStatsSummaryAllDomains:
    def setup_method(self):
        self.client = _make_client_all(_ALL_SUMMARY_ROWS)

    def teardown_method(self):
        _teardown()

    def test_returns_200(self):
        assert self.client.get("/api/stats/summary").status_code == 200

    def test_response_is_list(self):
        data = self.client.get("/api/stats/summary").json()
        assert isinstance(data, list)

    def test_returns_three_domains(self):
        data = self.client.get("/api/stats/summary").json()
        assert len(data) == 3

    def test_each_item_has_required_fields(self):
        data = self.client.get("/api/stats/summary").json()
        for item in data:
            for field in ("domain", "event_count", "anomaly_count",
                          "auto_flag_count", "avg_anomaly_score"):
                assert field in item, f"Missing field: {field!r}"

    def test_domain_values_are_valid(self):
        data = self.client.get("/api/stats/summary").json()
        for item in data:
            assert item["domain"] in {"infra", "ecommerce", "iot"}


# ── Single domain filter ───────────────────────────────────────────────────────

class TestGetStatsSummarySingleDomain:
    def setup_method(self):
        self.client = _make_client_single(_SUMMARY_ROW)

    def teardown_method(self):
        _teardown()

    def test_returns_200(self):
        assert self.client.get("/api/stats/summary?domain=infra").status_code == 200

    def test_returns_list_with_one_item(self):
        data = self.client.get("/api/stats/summary?domain=infra").json()
        assert isinstance(data, list) and len(data) == 1

    def test_domain_matches_filter(self):
        data = self.client.get("/api/stats/summary?domain=infra").json()
        assert data[0]["domain"] == "infra"

    def test_event_count_is_integer(self):
        data = self.client.get("/api/stats/summary?domain=infra").json()
        assert isinstance(data[0]["event_count"], int)

    def test_avg_score_is_float_or_null(self):
        data = self.client.get("/api/stats/summary?domain=infra").json()
        score = data[0]["avg_anomaly_score"]
        assert score is None or isinstance(score, float)


# ── Null avg_anomaly_score (no anomalies yet) ─────────────────────────────────

class TestGetStatsSummaryNullScore:
    def setup_method(self):
        row = {**_SUMMARY_ROW, "avg_anomaly_score": None}
        self.client = _make_client_single(row)

    def teardown_method(self):
        _teardown()

    def test_null_avg_score_is_accepted(self):
        data = self.client.get("/api/stats/summary?domain=infra").json()
        assert data[0]["avg_anomaly_score"] is None


# ── Invalid domain ─────────────────────────────────────────────────────────────

class TestGetStatsSummaryInvalidDomain:
    def setup_method(self):
        self.client = _make_client_empty()

    def teardown_method(self):
        _teardown()

    def test_invalid_domain_returns_422(self):
        assert self.client.get("/api/stats/summary?domain=blockchain").status_code == 422

    def test_invalid_domain_error_message(self):
        data = self.client.get("/api/stats/summary?domain=blockchain").json()
        assert "detail" in data
