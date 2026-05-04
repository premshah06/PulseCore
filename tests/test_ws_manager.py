"""Unit tests for api/services/ws_manager.py."""

from unittest.mock import AsyncMock

import pytest

from api.services.ws_manager import WebSocketManager


def _make_ws(side_effect=None):
    ws = AsyncMock()
    ws.accept = AsyncMock()
    if side_effect:
        ws.send_json = AsyncMock(side_effect=side_effect)
    else:
        ws.send_json = AsyncMock()
    return ws


# ── connect / disconnect ───────────────────────────────────────────────────────

class TestConnectDisconnect:
    @pytest.mark.asyncio
    async def test_connect_calls_accept(self):
        mgr = WebSocketManager()
        ws = _make_ws()
        await mgr.connect(ws)
        ws.accept.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_connect_increments_count(self):
        mgr = WebSocketManager()
        ws = _make_ws()
        await mgr.connect(ws, domain="infra")
        assert mgr.connection_count("infra") == 1

    @pytest.mark.asyncio
    async def test_connect_two_same_domain(self):
        mgr = WebSocketManager()
        ws1, ws2 = _make_ws(), _make_ws()
        await mgr.connect(ws1, domain="infra")
        await mgr.connect(ws2, domain="infra")
        assert mgr.connection_count("infra") == 2

    @pytest.mark.asyncio
    async def test_disconnect_reduces_count(self):
        mgr = WebSocketManager()
        ws = _make_ws()
        await mgr.connect(ws, domain="infra")
        mgr.disconnect(ws, domain="infra")
        assert mgr.connection_count("infra") == 0

    def test_disconnect_nonexistent_is_noop(self):
        mgr = WebSocketManager()
        ws = _make_ws()
        mgr.disconnect(ws, domain="infra")  # should not raise


# ── broadcast ─────────────────────────────────────────────────────────────────

class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_reaches_domain_subscriber(self):
        mgr = WebSocketManager()
        ws = _make_ws()
        await mgr.connect(ws, domain="infra")
        msg = {"type": "anomaly", "data": {}}
        await mgr.broadcast(msg, domain="infra")
        ws.send_json.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_wildcard_subscriber_receives_all_domains(self):
        mgr = WebSocketManager()
        ws = _make_ws()
        await mgr.connect(ws, domain=None)
        msg = {"type": "anomaly"}
        await mgr.broadcast(msg, domain="infra")
        ws.send_json.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_other_domain_subscriber_does_not_receive(self):
        mgr = WebSocketManager()
        ws = _make_ws()
        await mgr.connect(ws, domain="iot")
        await mgr.broadcast({"type": "anomaly"}, domain="infra")
        ws.send_json.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_subscribers(self):
        mgr = WebSocketManager()
        ws1, ws2 = _make_ws(), _make_ws()
        await mgr.connect(ws1, domain="infra")
        await mgr.connect(ws2, domain="infra")
        msg = {"type": "anomaly"}
        await mgr.broadcast(msg, domain="infra")
        ws1.send_json.assert_awaited_once_with(msg)
        ws2.send_json.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_broadcast_empty_no_error(self):
        mgr = WebSocketManager()
        await mgr.broadcast({"type": "anomaly"}, domain="infra")  # no subscribers

    @pytest.mark.asyncio
    async def test_stale_connection_removed_silently(self):
        mgr = WebSocketManager()
        ws = _make_ws(side_effect=RuntimeError("connection closed"))
        await mgr.connect(ws, domain="infra")
        # Should not raise despite send_json failing
        await mgr.broadcast({"type": "anomaly"}, domain="infra")

    @pytest.mark.asyncio
    async def test_good_subscribers_still_receive_after_stale_removed(self):
        mgr = WebSocketManager()
        bad_ws = _make_ws(side_effect=RuntimeError("dead"))
        good_ws = _make_ws()
        await mgr.connect(bad_ws, domain="infra")
        await mgr.connect(good_ws, domain="infra")
        msg = {"type": "anomaly"}
        await mgr.broadcast(msg, domain="infra")
        good_ws.send_json.assert_awaited_once_with(msg)

    @pytest.mark.asyncio
    async def test_domain_and_wildcard_not_double_counted(self):
        """A WS subscribed to None should receive exactly one message per broadcast."""
        mgr = WebSocketManager()
        ws = _make_ws()
        await mgr.connect(ws, domain=None)
        await mgr.broadcast({"type": "anomaly"}, domain="infra")
        assert ws.send_json.await_count == 1
