# PulseCore — Inter-Service Contracts

All services communicate using these schemas. Do not change a field name or type
without updating every phase that produces or consumes it.

---

## Phase 1 → Phase 2: Kafka message (StreamEvent)

**Topic:** `pulse.events`  
**Encoding:** UTF-8 JSON  
**Schema:** `producer.models.StreamEvent`

```json
{
  "event_id":  "string (UUID)",
  "source_id": "string (non-empty)",
  "domain":    "infra | ecommerce | iot",
  "timestamp": "ISO-8601 datetime with UTC timezone",
  "metrics":   {"string": float},
  "metadata":  {"string": any}
}
```

---

## Phase 2 → Phase 4: AggregateWindow (sidecar input)

**Transport:** in-process Python call (Phase 5 mediates)  
**Schema:** `consumer.aggregator.AggregateWindow` (serialised via `dataclasses.asdict`)

```json
{
  "source_id":      "string",
  "domain":         "infra | ecommerce | iot",
  "window_seconds": "int",
  "computed_at":    "datetime (UTC)",
  "event_count":    "int ≥ 1",
  "metrics": {
    "<metric_name>": {
      "mean":  "float",
      "std":   "float (≥ 0)",
      "min":   "float",
      "max":   "float",
      "p95":   "float",
      "count": "int"
    }
  }
}
```

---

## Phase 4 (sidecar) — HTTP API

### POST /predict

**Request — PredictRequest:**
```json
{
  "source_id": "string (non-empty)",
  "domain":    "infra | ecommerce | iot",
  "metrics":   {"string": float},
  "timestamp": "ISO-8601 datetime with UTC timezone"
}
```

**Response — AnomalyResult:**
```json
{
  "source_id":       "string",
  "domain":          "infra | ecommerce | iot",
  "timestamp":       "ISO-8601 datetime with UTC timezone",
  "anomaly_score":   "float in [0.0, 1.0]  — 0 = normal, 1 = definitely anomalous",
  "confidence_tier": "auto_flag | soft_alert | log_only",
  "is_anomaly":      "bool  — true iff confidence_tier == auto_flag",
  "raw_label":       "int   — 1 (normal) or -1 (anomaly) from ONNX",
  "latency_ms":      "float — wall-clock inference time in milliseconds"
}
```

**Confidence tier thresholds (Phase 4 enforces, Phase 5 trusts):**

| Tier | Condition | Meaning |
|------|-----------|---------|
| `auto_flag` | `anomaly_score > 0.85` | Trigger alert / write to anomalies table |
| `soft_alert` | `0.60 ≤ anomaly_score ≤ 0.85` | Log + surface in dashboard |
| `log_only`  | `anomaly_score < 0.60` | Record for audit; no alert |

**Error responses:**
- `422 Unprocessable Entity` — missing/invalid field, domain mismatch, missing feature
- `503 Service Unavailable` — model not loaded

### GET /health

```json
{"status": "ok", "model_loaded": true, "domain": "infra"}
```

---

## Phase 4 → Phase 5: AnomalyResult (FastAPI ingestion)

Phase 5 receives the `AnomalyResult` JSON above via HTTP and may write it to the
`anomalies` TimescaleDB table. The `confidence_tier` field drives business logic;
Phase 5 must not re-implement the tier thresholds.

---

## Phase 5 — HTTP API

### GET /api/events

Query params: `domain` (optional, one of infra/ecommerce/iot), `limit` (1–500, default 50),
`offset` (≥0, default 0).

Response — EventPage:
```json
{
  "items":  [EventRecord],
  "total":  "int — unfiltered row count",
  "limit":  "int",
  "offset": "int"
}
```

### GET /api/anomalies

Query params: `tier` (optional), `since` (optional ISO-8601 lower bound), `limit` (1–500).

Response — AnomalyPage:
```json
{
  "items": [AnomalyRecord],
  "total": "int",
  "limit": "int"
}
```

### POST /api/anomalies

Body: `AnomalyResult` (from Phase 4 sidecar).  
Response `201`: `AnomalyRecord` (persisted row with `id` and `detected_at`).  
Side effect: broadcasts `LiveUpdate` to all matching WebSocket subscribers.

### GET /api/stats/summary

Query param: `domain` (optional). Returns all 3 domains when omitted.

Response — list[DomainSummary]:
```json
[{
  "domain":            "infra | ecommerce | iot",
  "event_count":       "int",
  "anomaly_count":     "int",
  "auto_flag_count":   "int",
  "avg_anomaly_score": "float | null"
}]
```

---

## Phase 5 → Phase 6: LiveUpdate (WebSocket broadcast)

**Endpoint:** `GET /ws?domain=<optional>`  
**Encoding:** JSON text frame

```json
{
  "type": "anomaly",
  "data": {
    "id":              "int",
    "source_id":       "string",
    "domain":          "infra | ecommerce | iot",
    "timestamp":       "ISO-8601 datetime with UTC timezone",
    "anomaly_score":   "float in [0.0, 1.0]",
    "confidence_tier": "auto_flag | soft_alert | log_only",
    "is_anomaly":      "bool",
    "raw_label":       "int — 1 or -1",
    "latency_ms":      "float",
    "detected_at":     "ISO-8601 datetime with UTC timezone"
  }
}
```

Subscription rules:
- `?domain=infra` — receives only `domain=infra` broadcasts
- No `domain` param — receives all broadcasts (wildcard)
- Invalid domain causes immediate close with code 4422
