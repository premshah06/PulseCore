"""Unit tests for consumer.processor.process()."""

import json
from datetime import UTC, datetime

import pytest

from consumer.processor import process
from producer.models import StreamEvent


def _payload(**overrides) -> bytes:
    base = {
        "event_id": "test-event-001",
        "source_id": "test-src",
        "domain": "infra",
        "timestamp": datetime.now(UTC).isoformat(),
        "metrics": {"cpu_user_pct": 42.0},
        "metadata": {},
    }
    base.update(overrides)
    return json.dumps(base).encode()


class TestProcessValid:
    def test_returns_stream_event_instance(self):
        event = process(_payload())
        assert isinstance(event, StreamEvent)

    def test_source_id_preserved(self):
        assert process(_payload(source_id="my-host")).source_id == "my-host"

    def test_event_id_preserved(self):
        assert process(_payload(event_id="fixed-id-123")).event_id == "fixed-id-123"

    def test_domain_infra(self):
        assert process(_payload(domain="infra")).domain == "infra"

    def test_domain_ecommerce(self):
        event = process(_payload(domain="ecommerce", metrics={"revenue_usd": 99.9}))
        assert event.domain == "ecommerce"

    def test_domain_iot(self):
        event = process(_payload(domain="iot", metrics={"temperature_celsius": 22.5}))
        assert event.domain == "iot"

    def test_metrics_values_are_floats(self):
        event = process(_payload(metrics={"cpu_user_pct": 55.5, "mem_used_pct": 70.0}))
        for v in event.metrics.values():
            assert isinstance(v, float)

    def test_timestamp_parsed(self):
        ts = datetime(2024, 3, 15, 10, 30, 0, tzinfo=UTC)
        event = process(_payload(timestamp=ts.isoformat()))
        assert event.timestamp == ts

    def test_metadata_preserved(self):
        event = process(_payload(metadata={"region": "us-east-1"}))
        assert event.metadata["region"] == "us-east-1"


class TestProcessInvalid:
    def test_malformed_json_raises_value_error(self):
        with pytest.raises(ValueError, match="Malformed JSON"):
            process(b"{not valid json{")

    def test_empty_bytes_raises_value_error(self):
        with pytest.raises(ValueError):
            process(b"")

    def test_non_json_bytes_raises_value_error(self):
        with pytest.raises(ValueError, match="Malformed JSON"):
            process(b"hello world")

    def test_unknown_domain_raises_value_error(self):
        with pytest.raises(ValueError):
            process(_payload(domain="blockchain"))

    def test_missing_source_id_raises_value_error(self):
        data = {"domain": "infra", "metrics": {"cpu": 1.0}}
        with pytest.raises(ValueError, match="Invalid StreamEvent"):
            process(json.dumps(data).encode())

    def test_empty_metrics_raises_value_error(self):
        with pytest.raises(ValueError):
            process(_payload(metrics={}))

    def test_empty_source_id_raises_value_error(self):
        with pytest.raises(ValueError):
            process(_payload(source_id=""))

    def test_null_value_raises_value_error(self):
        with pytest.raises(ValueError):
            process(b"null")
