-- PulseCore Phase 5 — anomalies table
-- Run after init.sql.

CREATE TABLE IF NOT EXISTS anomalies (
    id              BIGSERIAL        NOT NULL,
    source_id       TEXT             NOT NULL,
    domain          TEXT             NOT NULL CHECK (domain IN ('infra', 'ecommerce', 'iot')),
    timestamp       TIMESTAMPTZ      NOT NULL,
    anomaly_score   DOUBLE PRECISION NOT NULL CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    confidence_tier TEXT             NOT NULL CHECK (confidence_tier IN ('auto_flag', 'soft_alert', 'log_only')),
    is_anomaly      BOOLEAN          NOT NULL,
    raw_label       INTEGER          NOT NULL CHECK (raw_label IN (1, -1)),
    latency_ms      DOUBLE PRECISION NOT NULL,
    detected_at     TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

SELECT create_hypertable(
    'anomalies',
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_anomalies_domain_time
    ON anomalies (domain, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_anomalies_tier_time
    ON anomalies (confidence_tier, timestamp DESC);

COMMENT ON TABLE anomalies IS
    'Anomaly detection results written by the Phase 5 FastAPI backend after '
    'forwarding raw_events through the Phase 4 inference sidecar.';
