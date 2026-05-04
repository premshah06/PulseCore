-- PulseCore Phase 1 — TimescaleDB schema
-- Run once against the pulsecore database.

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- raw_events mirrors StreamEvent exactly.
-- metrics and metadata are JSONB so queries can index into arbitrary keys.
CREATE TABLE IF NOT EXISTS raw_events (
    event_id        TEXT        NOT NULL,
    source_id       TEXT        NOT NULL,
    domain          TEXT        NOT NULL CHECK (domain IN ('infra', 'ecommerce', 'iot')),
    timestamp       TIMESTAMPTZ NOT NULL,
    metrics         JSONB       NOT NULL,
    metadata        JSONB       NOT NULL DEFAULT '{}',
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Convert to hypertable partitioned by time (7-day chunks).
SELECT create_hypertable(
    'raw_events',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- Composite index for domain + time range queries (most common access pattern).
CREATE INDEX IF NOT EXISTS idx_raw_events_domain_time
    ON raw_events (domain, timestamp DESC);

-- Index for per-source lookups.
CREATE INDEX IF NOT EXISTS idx_raw_events_source_time
    ON raw_events (source_id, timestamp DESC);

-- GIN index for arbitrary metric key lookups.
CREATE INDEX IF NOT EXISTS idx_raw_events_metrics_gin
    ON raw_events USING GIN (metrics);

-- Unique constraint to guard against duplicate event delivery.
CREATE UNIQUE INDEX IF NOT EXISTS idx_raw_events_event_id
    ON raw_events (event_id, timestamp);

COMMENT ON TABLE raw_events IS
    'Raw telemetry events ingested from the Kafka pulse.events topic. '
    'Schema mirrors the StreamEvent Pydantic model in producer/models.py.';
