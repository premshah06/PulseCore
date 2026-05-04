"""
Contract tests: verify producer output serializes and deserializes correctly
into the canonical StreamEvent Pydantic model.

These tests prove that whatever bytes the Kafka producer sends, a consumer
that calls StreamEvent.model_validate_json(bytes) will reconstruct an
identical, valid model — no data loss, no type coercion surprises.
"""

import json
from datetime import UTC

import pytest

from producer.generators import EcommerceGenerator, InfraGenerator, IotGenerator
from producer.models import StreamEvent


def _roundtrip(generator) -> tuple[StreamEvent, StreamEvent]:
    """Generate an event, serialize it to JSON (as the producer would), then parse it back."""
    original: StreamEvent = generator.generate()
    json_bytes: str = original.model_dump_json()  # what KafkaProducer.value_serializer emits
    restored: StreamEvent = StreamEvent.model_validate_json(json_bytes)
    return original, restored


@pytest.mark.parametrize(
    "generator_cls",
    [InfraGenerator, EcommerceGenerator, IotGenerator],
    ids=["infra", "ecommerce", "iot"],
)
class TestRoundtrip:
    def test_event_id_survives_roundtrip(self, generator_cls):
        original, restored = _roundtrip(generator_cls())
        assert restored.event_id == original.event_id

    def test_source_id_survives_roundtrip(self, generator_cls):
        original, restored = _roundtrip(generator_cls())
        assert restored.source_id == original.source_id

    def test_domain_survives_roundtrip(self, generator_cls):
        original, restored = _roundtrip(generator_cls())
        assert restored.domain == original.domain

    def test_timestamp_survives_roundtrip(self, generator_cls):
        original, restored = _roundtrip(generator_cls())
        # Timestamps must be equal to the microsecond.
        assert restored.timestamp == original.timestamp

    def test_all_metrics_survive_roundtrip(self, generator_cls):
        original, restored = _roundtrip(generator_cls())
        assert restored.metrics == original.metrics

    def test_metadata_survives_roundtrip(self, generator_cls):
        original, restored = _roundtrip(generator_cls())
        assert restored.metadata == original.metadata

    def test_all_restored_metric_values_are_floats(self, generator_cls):
        _, restored = _roundtrip(generator_cls())
        for k, v in restored.metrics.items():
            assert isinstance(v, float), f"After roundtrip, metric {k!r} is {type(v)}, not float"

    def test_restored_event_is_valid_stream_event(self, generator_cls):
        _, restored = _roundtrip(generator_cls())
        assert isinstance(restored, StreamEvent)

    def test_json_is_valid_utf8(self, generator_cls):
        event = generator_cls().generate()
        raw = event.model_dump_json()
        assert isinstance(raw, str)
        # Must be decodable as JSON with no errors.
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_json_contains_all_required_keys(self, generator_cls):
        event = generator_cls().generate()
        parsed = json.loads(event.model_dump_json())
        for required in ("event_id", "source_id", "domain", "timestamp", "metrics"):
            assert required in parsed, f"Required key {required!r} missing from serialized JSON"


# ── Manual field construction ──────────────────────────────────────────────────

class TestStreamEventValidation:
    def test_rejects_empty_event_id(self):
        with pytest.raises(Exception):
            StreamEvent(event_id="", source_id="s", domain="infra", metrics={"cpu": 1.0})

    def test_rejects_whitespace_source_id(self):
        with pytest.raises(Exception):
            StreamEvent(event_id="abc", source_id="   ", domain="infra", metrics={"cpu": 1.0})

    def test_rejects_unknown_domain(self):
        with pytest.raises(Exception):
            StreamEvent(source_id="s", domain="unknown", metrics={"cpu": 1.0})

    def test_rejects_empty_metrics(self):
        with pytest.raises(Exception):
            StreamEvent(source_id="s", domain="infra", metrics={})

    def test_accepts_integer_metrics_coerced_to_float(self):
        # Producer generators always pass floats, but validate coercion works.
        event = StreamEvent(source_id="s", domain="infra", metrics={"cpu": 42})
        assert event.metrics["cpu"] == 42.0
        assert isinstance(event.metrics["cpu"], float)

    def test_timestamp_defaults_to_utc(self):
        event = StreamEvent(source_id="s", domain="iot", metrics={"temp": 22.5})
        assert event.timestamp.tzinfo is not None
        assert event.timestamp.tzinfo == UTC
