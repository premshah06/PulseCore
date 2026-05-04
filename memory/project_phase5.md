---
name: Phase 5 completion
description: Phase 5 FastAPI backend + WebSocket manager — completed, all tests passing
type: project
---

Phase 5 (FastAPI Backend + WebSocket) completed at 478 total tests.

**Why:** Building real-time telemetry streaming system PulseCore.

**How to apply:** Phase 6 (Next.js dashboard) is next. It consumes GET /api/events, GET /api/anomalies, GET /api/stats/summary, POST /api/anomalies, and WS /ws?domain=.

Key design decisions:
- WS endpoint accesses `ws.app.state.ws_manager` directly (not via Depends) because FastAPI Depends cannot inject Request-typed dependencies into WebSocket route handlers
- `inference.schemas.AnomalyResult.domain` changed to `Literal["infra","ecommerce","iot"]` in Phase 5 to enforce validation at POST /api/anomalies
- All SQL parameterized with $N placeholders; 4 explicit query variants for anomaly filters (avoids f-string SQL)
- Tests use `app.dependency_overrides` for HTTP routes; `app.state.ws_manager` is set directly for WebSocket tests
