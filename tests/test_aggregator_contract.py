"""
Contract test: pins the AggregateWindow shape for Phase 4 (ML inference sidecar).

Phase 4 will receive AggregateWindow objects via dataclasses.asdict() and must
read these exact field names and types. Any breakage here means Phase 4 breaks.
"""

import dataclasses
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from consumer.aggregator import AggregateWindow, RollingAggregator
from producer.models import StreamEvent

_BASE_TIME = datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC)

_REQUIRED_TOP_LEVEL = {"source_id", "domain", "window_seconds", "computed_at", "event_count", "metrics"}
_REQUIRED_STAT_FIELDS = {"mean", "std", "min", "max", "p95", "count"}


def _build_window() -> AggregateWindow:
    agg = RollingAggregator(window_seconds=60, _clock=Mock(return_value=_BASE_TIME))
    for i in range(1, 11):
        event = StreamEvent(
            source_id="contract-src",
            domain="infra",
            metrics={
                "cpu_user_pct": float(i * 10),
                "mem_used_pct": float(i * 5),
            },
            timestamp=_BASE_TIME - timedelta(seconds=60 - i),
        )
        agg.ingest(event)
    result = agg.get_stats("contract-src")
    assert result is not None, "fixture setup failed"
    return result


class TestAggregateWindowContract:
    """Every assertion here is a Phase 4 dependency — do not remove without updating Phase 4."""

    def setup_method(self):
        self.window = _build_window()

    # ── Top-level fields ──────────────────────────────────────────────────────

    def test_all_required_top_level_fields_present(self):
        actual = {f.name for f in dataclasses.fields(self.window)}
        missing = _REQUIRED_TOP_LEVEL - actual
        assert not missing, f"Phase 4 contract broken — missing fields: {missing}"

    def test_source_id_is_str(self):
        assert isinstance(self.window.source_id, str)
        assert self.window.source_id != ""

    def test_domain_is_known_str(self):
        assert isinstance(self.window.domain, str)
        assert self.window.domain in {"infra", "ecommerce", "iot"}

    def test_window_seconds_is_int(self):
        assert isinstance(self.window.window_seconds, int)
        assert self.window.window_seconds > 0

    def test_computed_at_is_timezone_aware_datetime(self):
        assert isinstance(self.window.computed_at, datetime)
        assert self.window.computed_at.tzinfo is not None

    def test_event_count_is_positive_int(self):
        assert isinstance(self.window.event_count, int)
        assert self.window.event_count > 0

    def test_metrics_is_dict_with_string_keys(self):
        assert isinstance(self.window.metrics, dict)
        assert all(isinstance(k, str) for k in self.window.metrics)

    # ── MetricStats fields ────────────────────────────────────────────────────

    def test_each_metric_has_required_stat_fields(self):
        for metric_name, stats in self.window.metrics.items():
            actual = {f.name for f in dataclasses.fields(stats)}
            missing = _REQUIRED_STAT_FIELDS - actual
            assert not missing, f"MetricStats for {metric_name!r} missing: {missing}"

    def test_mean_is_float(self):
        for name, stats in self.window.metrics.items():
            assert isinstance(stats.mean, float), f"{name}.mean not float"

    def test_std_is_float_and_non_negative(self):
        for name, stats in self.window.metrics.items():
            assert isinstance(stats.std, float), f"{name}.std not float"
            assert stats.std >= 0.0, f"{name}.std is negative"

    def test_min_is_float(self):
        for name, stats in self.window.metrics.items():
            assert isinstance(stats.min, float), f"{name}.min not float"

    def test_max_is_float(self):
        for name, stats in self.window.metrics.items():
            assert isinstance(stats.max, float), f"{name}.max not float"

    def test_p95_is_float(self):
        for name, stats in self.window.metrics.items():
            assert isinstance(stats.p95, float), f"{name}.p95 not float"

    def test_count_is_int(self):
        for name, stats in self.window.metrics.items():
            assert isinstance(stats.count, int), f"{name}.count not int"
            assert stats.count > 0, f"{name}.count is zero"

    # ── Statistical invariants Phase 4 can rely on ────────────────────────────

    def test_min_lte_mean_lte_max(self):
        for name, stats in self.window.metrics.items():
            assert stats.min <= stats.mean <= stats.max, (
                f"Invariant min≤mean≤max violated for {name}: "
                f"{stats.min} ≤ {stats.mean} ≤ {stats.max}"
            )

    def test_p95_between_min_and_max(self):
        for name, stats in self.window.metrics.items():
            assert stats.min <= stats.p95 <= stats.max, (
                f"p95 out of [min,max] for {name}: {stats.p95}"
            )

    # ── Serialization (Phase 4 passes this over HTTP/IPC) ────────────────────

    def test_asdict_produces_plain_dict(self):
        d = dataclasses.asdict(self.window)
        assert isinstance(d, dict)

    def test_asdict_metrics_keys_match(self):
        d = dataclasses.asdict(self.window)
        assert set(d["metrics"].keys()) == set(self.window.metrics.keys())

    def test_asdict_stat_fields_match_contract(self):
        d = dataclasses.asdict(self.window)
        for metric_name, stat_dict in d["metrics"].items():
            assert set(stat_dict.keys()) == _REQUIRED_STAT_FIELDS, (
                f"Serialized MetricStats for {metric_name!r} has unexpected keys: "
                f"{set(stat_dict.keys())}"
            )

    def test_asdict_computed_at_is_datetime(self):
        d = dataclasses.asdict(self.window)
        assert isinstance(d["computed_at"], datetime)

    # ── Specific metric values for cpu_user_pct [10,20,...,100] ──────────────

    def test_cpu_mean_is_55(self):
        # inputs: 10,20,...,100 → mean=55
        stats = self.window.metrics["cpu_user_pct"]
        assert stats.mean == pytest.approx(55.0)

    def test_cpu_min_is_10(self):
        assert self.window.metrics["cpu_user_pct"].min == pytest.approx(10.0)

    def test_cpu_max_is_100(self):
        assert self.window.metrics["cpu_user_pct"].max == pytest.approx(100.0)

    def test_cpu_p95(self):
        # [10,20,...,100], n=10: ceil(0.95*10)-1 = 9 → sorted[9] = 100.0
        assert self.window.metrics["cpu_user_pct"].p95 == pytest.approx(100.0)
