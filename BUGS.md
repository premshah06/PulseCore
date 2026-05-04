# BUGS.md — PulseCore known issues

## Phase 1

### BUG-001 — Kafka advertised listener is localhost-only
**Severity:** Low (Phase 1 only)
**Description:** `KAFKA_CFG_ADVERTISED_LISTENERS` is set to `PLAINTEXT://localhost:9092`.
This means the producer and any consumer must run on the same machine as Docker.
Running the producer inside a Docker network (e.g., a `producer` service in docker-compose)
will fail because the broker advertises `localhost`, not its container hostname.
**Workaround:** Run the producer outside Docker (on the host) for Phase 1.
**Fix for Phase 2:** Add a second listener (`EXTERNAL://0.0.0.0:9093`) advertised as the
host IP or a DNS name, and expose port 9093. Update `KAFKA_BROKER` env var accordingly.

### BUG-002 — TimescaleDB schema is applied only on first container start
**Severity:** Informational
**Description:** `docker-entrypoint-initdb.d/` scripts only run when the data volume is empty
(i.e., fresh container). If you change `schema/init.sql` after the volume exists, the changes
will not be applied automatically.
**Workaround:** `docker compose down -v && docker compose up -d` to recreate volumes.

### BUG-003 — EcommerceGenerator: avg_order_value is 0.0 when orders == 0
**Severity:** Low / expected
**Description:** When `orders_count == 0`, `avg_order_value_usd` is set to `0.0` by design.
Downstream aggregations should treat this as "no orders in window", not as "average is $0".
**Fix:** Phase 2 consumer should filter `avg_order_value_usd` where `orders_count == 0`.

## Phase 2

### BUG-004 — RollingAggregator is not thread-safe
**Severity:** Medium
**Description:** `RollingAggregator._windows` (a `defaultdict` of `deque`) is mutated by
`ingest()` and read/mutated by `get_stats()`. Both are called from the single async consumer
loop, so no data races exist today. If Phase 5 (FastAPI) calls `get_stats()` concurrently
from a different task or thread, races are possible.
**Fix:** Wrap `ingest()` and `get_stats()` with `asyncio.Lock` before Phase 5 integration.

### BUG-005 — Consumer lag check uses highwater() which may lag one fetch cycle
**Severity:** Low / informational
**Description:** `consumer.highwater(tp)` is updated after each broker fetch, not in real time.
A lag spike that resolves before the next fetch cycle will not be logged. The lag warning is
therefore a trailing indicator, not an instantaneous one.
**Workaround:** Reduce `timeout_ms` in `consumer.getmany()` for lower-latency lag detection
at the cost of more broker round-trips.

## Phase 3

### BUG-006 — IsolationForest training data uses Python random, not numpy seeded rng
**Severity:** Low / reproducibility
**Description:** The domain generators use `random.random()` (stdlib) which is not seeded
by the `RANDOM_SEED` env var passed to `generate_training_data()`. Two runs with the same
`RANDOM_SEED` may produce different training data, leading to slightly different ONNX models.
**Fix:** Seed the stdlib `random` module at the start of `ml/train.py:main()` via
`import random; random.seed(RANDOM_SEED)`. Generators would then be deterministic.

### BUG-007 — ONNX export target_opset is hardcoded to ai.onnx.ml: 3
**Severity:** Low
**Description:** `convert_sklearn` is called with `target_opset={"": 17, "ai.onnx.ml": 3}`.
If a future version of skl2onnx raises the minimum required opset above 3, the export will
break silently or require a code change rather than a config change.
**Fix:** Expose `ONNX_OPSET` and `ONNX_ML_OPSET` as env vars in `ml/export_onnx.py`.

## Phase 7

### ~~BUG-009~~ — Consumer does not call inference sidecars ✓ RESOLVED (Phase 9)
**Resolved in Phase 9.**
`consumer/pipeline.py` implements `score_event()` which: POSTs to the domain-specific
inference sidecar (`/predict`), writes the `AnomalyResult` to MongoDB `anomalies` via
`consumer/db.write_anomaly()`, then POSTs a `LiveUpdate` to `POST /internal/broadcast`
for WebSocket fan-out. The consumer falls back to a `log_only` placeholder when the
sidecar is unreachable, so the loop never crashes. `POST /internal/broadcast` is
protected by `X-Internal-Secret`; consumers outside the Docker network cannot call it.

---

## Phase 3

### BUG-008 — F1 score is moderate (avg ~0.64) due to generator value ranges
**Severity:** Informational
**Description:** The Isolation Forest is trained and evaluated on data from the same generators.
Some metric ranges overlap between normal and anomalous distributions (e.g., `net_rx_mb_s`
0–1000 vs 15x spike = 0–15000), making some anomalies hard to detect. The anomaly injection
multiplier (15–30x) works well for bounded metrics but less so for already-wide-range metrics.
**Fix:** Use domain-specific anomaly injection strategies in Phase 3 or increase N_SAMPLES.
