"""Integration tests for POST /internal/broadcast."""

import os
from datetime import UTC, datetime
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from api.dependencies import get_ws_manager
from api.main import app
from api.services.ws_manager import WebSocketManager

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
_SECRET = "test-secret-abc"

_LIVE_UPDATE = {
    "type": "anomaly",
    "data": {
        "id": "507f1f77bcf86cd799439011",
        "source_id": "host-1",
        "domain": "infra",
        "timestamp": _NOW.isoformat(),
        "anomaly_score": 0.92,
        "confidence_tier": "auto_flag",
        "is_anomaly": True,
        "raw_label": -1,
        "latency_ms": 2.3,
        "detected_at": _NOW.isoformat(),
    },
}


def _teardown():
    app.dependency_overrides.clear()


class TestInternalBroadcast:
    def setup_method(self):
        self.ws_manager = WebSocketManager()
        app.state.ws_manager = self.ws_manager
        app.dependency_overrides[get_ws_manager] = lambda: self.ws_manager
        self.client = TestClient(app, raise_server_exceptions=True)

    def teardown_method(self):
        _teardown()
        if hasattr(app.state, "ws_manager"):
            del app.state.ws_manager

    def test_accepts_valid_secret(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_SECRET", _SECRET)
        resp = self.client.post(
            "/internal/broadcast",
            json=_LIVE_UPDATE,
            headers={"X-Internal-Secret": _SECRET},
        )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_rejects_missing_secret(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_SECRET", _SECRET)
        resp = self.client.post("/internal/broadcast", json=_LIVE_UPDATE)
        assert resp.status_code == 403

    def test_rejects_wrong_secret(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_SECRET", _SECRET)
        resp = self.client.post(
            "/internal/broadcast",
            json=_LIVE_UPDATE,
            headers={"X-Internal-Secret": "wrong-secret"},
        )
        assert resp.status_code == 403

    def test_broadcasts_to_ws_clients(self, monkeypatch):
        monkeypatch.setenv("INTERNAL_SECRET", _SECRET)
        with self.client.websocket_connect("/ws?domain=infra") as ws:
            resp = self.client.post(
                "/internal/broadcast",
                json=_LIVE_UPDATE,
                headers={"X-Internal-Secret": _SECRET},
            )
            assert resp.status_code == 200
            data = ws.receive_json()
            assert data["type"] == "anomaly"
            assert data["data"]["source_id"] == "host-1"
