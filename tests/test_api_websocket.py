"""Integration tests for the /ws WebSocket endpoint."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from api.dependencies import get_db, get_ws_manager
from api.main import app
from api.services.ws_manager import WebSocketManager

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

_ANOMALY_PAYLOAD = {
    "source_id": "host-1",
    "domain": "infra",
    "timestamp": _NOW.isoformat(),
    "anomaly_score": 0.92,
    "confidence_tier": "auto_flag",
    "is_anomaly": True,
    "raw_label": -1,
    "latency_ms": 1.5,
}


def _make_mock_db_insert() -> MagicMock:
    mock_db = MagicMock()
    mock_db.anomalies.insert_one = AsyncMock(
        return_value=MagicMock(inserted_id=_MOCK_OID)
    )
    return mock_db


def _teardown():
    app.dependency_overrides.clear()


# ── Connect / disconnect ───────────────────────────────────────────────────────

class TestWebSocketConnectDisconnect:
    def setup_method(self):
        app.state.ws_manager = WebSocketManager()
        app.dependency_overrides[get_db] = lambda: MagicMock()
        self.client = TestClient(app, raise_server_exceptions=True)

    def teardown_method(self):
        _teardown()
        if hasattr(app.state, "ws_manager"):
            del app.state.ws_manager

    def test_connect_succeeds(self):
        with self.client.websocket_connect("/ws"):
            pass

    def test_connect_with_valid_domain(self):
        with self.client.websocket_connect("/ws?domain=infra"):
            pass

    def test_connect_with_all_valid_domains(self):
        for domain in ("infra", "ecommerce", "iot"):
            with self.client.websocket_connect(f"/ws?domain={domain}"):
                pass

    def test_connect_without_domain(self):
        with self.client.websocket_connect("/ws"):
            pass


# ── Shared WebSocketManager — broadcast via POST ───────────────────────────────

class TestWebSocketBroadcast:
    def setup_method(self):
        self.ws_manager = WebSocketManager()
        app.state.ws_manager = self.ws_manager

        mock_db = _make_mock_db_insert()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_ws_manager] = lambda: self.ws_manager
        self.client = TestClient(app, raise_server_exceptions=True)

    def teardown_method(self):
        _teardown()
        if hasattr(app.state, "ws_manager"):
            del app.state.ws_manager

    def test_post_anomaly_triggers_broadcast_to_domain_subscriber(self):
        with self.client.websocket_connect("/ws?domain=infra") as ws:
            self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD)
            data = ws.receive_json()
            assert data["type"] == "anomaly"

    def test_broadcast_data_has_anomaly_record_shape(self):
        with self.client.websocket_connect("/ws?domain=infra") as ws:
            self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD)
            data = ws.receive_json()
            assert "data" in data
            for field in ("id", "source_id", "domain", "anomaly_score",
                          "confidence_tier", "is_anomaly"):
                assert field in data["data"], f"Missing broadcast field: {field!r}"

    def test_wildcard_subscriber_receives_broadcast(self):
        with self.client.websocket_connect("/ws") as ws:
            self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD)
            data = ws.receive_json()
            assert data["type"] == "anomaly"

    def test_broadcast_source_id_matches_posted(self):
        with self.client.websocket_connect("/ws?domain=infra") as ws:
            self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD)
            data = ws.receive_json()
            assert data["data"]["source_id"] == "host-1"

    def test_different_domain_subscriber_does_not_receive(self):
        """A subscriber to 'iot' should not get an 'infra' broadcast."""
        import threading
        received = []

        def _listen():
            try:
                with self.client.websocket_connect("/ws?domain=iot") as ws:
                    try:
                        ws.receive_json(timeout=0.2)
                        received.append(True)
                    except Exception:
                        received.append(False)
            except Exception:
                received.append(False)

        t = threading.Thread(target=_listen, daemon=True)
        t.start()
        self.client.post("/api/anomalies", json=_ANOMALY_PAYLOAD)
        t.join(timeout=1.0)
        assert received == [False]
