"""Unit tests for all three domain generators."""

import pytest

from producer.generators import EcommerceGenerator, InfraGenerator, IotGenerator
from producer.generators.base import BaseGenerator
from producer.models import StreamEvent


def _assert_valid_event(event: StreamEvent, expected_domain: str) -> None:
    """Shared assertions that every generator must satisfy."""
    assert isinstance(event, StreamEvent), "generate() must return a StreamEvent"

    # event_id and source_id are non-empty strings
    assert event.event_id and isinstance(event.event_id, str), "event_id must be a non-empty string"
    assert event.source_id and isinstance(event.source_id, str), "source_id must be a non-empty string"

    # domain matches the generator
    assert event.domain == expected_domain, f"expected domain={expected_domain!r}, got {event.domain!r}"

    # all metric values are floats
    assert event.metrics, "metrics must not be empty"
    for key, val in event.metrics.items():
        assert isinstance(val, float), f"metric {key!r} must be float, got {type(val)}"

    # timestamp is present
    assert event.timestamp is not None


# ── InfraGenerator ─────────────────────────────────────────────────────────────

class TestInfraGenerator:
    def setup_method(self):
        self.gen = InfraGenerator()

    def test_returns_stream_event(self):
        _assert_valid_event(self.gen.generate(), "infra")

    def test_all_metrics_are_floats(self):
        event = self.gen.generate()
        for k, v in event.metrics.items():
            assert isinstance(v, float), f"{k} is not float"

    def test_source_id_non_empty(self):
        assert self.gen.generate().source_id.strip() != ""

    def test_event_id_non_empty(self):
        assert self.gen.generate().event_id.strip() != ""

    def test_domain_is_infra(self):
        assert self.gen.generate().domain == "infra"

    def test_cpu_metrics_sum_near_100(self):
        event = self.gen.generate()
        total = event.metrics["cpu_user_pct"] + event.metrics["cpu_system_pct"] + event.metrics["cpu_idle_pct"]
        assert abs(total - 100.0) < 0.1, f"CPU percentages don't sum to ~100: {total}"

    def test_mem_used_pct_in_range(self):
        for _ in range(20):
            val = self.gen.generate().metrics["mem_used_pct"]
            assert 0.0 <= val <= 100.0, f"mem_used_pct out of range: {val}"

    def test_custom_source_id(self):
        gen = InfraGenerator(source_id="my-custom-host")
        assert gen.generate().source_id == "my-custom-host"

    def test_generates_multiple_unique_event_ids(self):
        ids = {self.gen.generate().event_id for _ in range(50)}
        assert len(ids) == 50, "event_id values must be unique across calls"


# ── EcommerceGenerator ─────────────────────────────────────────────────────────

class TestEcommerceGenerator:
    def setup_method(self):
        self.gen = EcommerceGenerator()

    def test_returns_stream_event(self):
        _assert_valid_event(self.gen.generate(), "ecommerce")

    def test_all_metrics_are_floats(self):
        event = self.gen.generate()
        for k, v in event.metrics.items():
            assert isinstance(v, float), f"{k} is not float"

    def test_source_id_non_empty(self):
        assert self.gen.generate().source_id.strip() != ""

    def test_event_id_non_empty(self):
        assert self.gen.generate().event_id.strip() != ""

    def test_domain_is_ecommerce(self):
        assert self.gen.generate().domain == "ecommerce"

    def test_rates_between_0_and_1(self):
        for _ in range(20):
            event = self.gen.generate()
            assert 0.0 <= event.metrics["cart_abandonment_rate"] <= 1.0
            assert 0.0 <= event.metrics["bounce_rate"] <= 1.0
            assert 0.0 <= event.metrics["conversion_rate"] <= 1.0

    def test_revenue_non_negative(self):
        for _ in range(20):
            assert self.gen.generate().metrics["revenue_usd"] >= 0.0

    def test_custom_source_id(self):
        gen = EcommerceGenerator(source_id="store-test")
        assert gen.generate().source_id == "store-test"


# ── IotGenerator ───────────────────────────────────────────────────────────────

class TestIotGenerator:
    def setup_method(self):
        self.gen = IotGenerator()

    def test_returns_stream_event(self):
        _assert_valid_event(self.gen.generate(), "iot")

    def test_all_metrics_are_floats(self):
        event = self.gen.generate()
        for k, v in event.metrics.items():
            assert isinstance(v, float), f"{k} is not float"

    def test_source_id_non_empty(self):
        assert self.gen.generate().source_id.strip() != ""

    def test_event_id_non_empty(self):
        assert self.gen.generate().event_id.strip() != ""

    def test_domain_is_iot(self):
        assert self.gen.generate().domain == "iot"

    def test_battery_in_range(self):
        for _ in range(20):
            val = self.gen.generate().metrics["battery_pct"]
            assert 0.0 <= val <= 100.0, f"battery_pct out of range: {val}"

    def test_humidity_in_range(self):
        for _ in range(20):
            val = self.gen.generate().metrics["humidity_pct"]
            assert 0.0 <= val <= 100.0, f"humidity_pct out of range: {val}"

    def test_custom_source_id(self):
        gen = IotGenerator(source_id="sensor-9999")
        assert gen.generate().source_id == "sensor-9999"


# ── Factory ────────────────────────────────────────────────────────────────────

class TestGetGenerator:
    @pytest.mark.parametrize("domain", ["infra", "ecommerce", "iot"])
    def test_factory_returns_base_generator(self, domain):
        from producer.generators import get_generator
        gen = get_generator(domain)
        assert isinstance(gen, BaseGenerator)
        assert gen.domain == domain

    def test_factory_raises_on_unknown_domain(self):
        from producer.generators import get_generator
        with pytest.raises(ValueError, match="Unknown domain"):
            get_generator("blockchain")
