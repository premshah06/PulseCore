"""Unit tests for consumer.aggregator."""

import math
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from consumer.aggregator import (
    AggregateWindow,
    MetricStats,
    RollingAggregator,
    _compute_stats,
    _p95,
)
from producer.models import StreamEvent

_BASE_TIME = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _clock(ts: datetime = _BASE_TIME) -> Mock:
    return Mock(return_value=ts)


def _event(
    source_id: str = "src",
    domain: str = "infra",
    metrics: dict | None = None,
    ts: datetime | None = None,
) -> StreamEvent:
    return StreamEvent(
        source_id=source_id,
        domain=domain,
        metrics=metrics or {"cpu_user_pct": 50.0},
        timestamp=ts or (_BASE_TIME - timedelta(seconds=5)),
    )


# ── _p95 ───────────────────────────────────────────────────────────────────────

class TestP95:
    def test_single_value(self):
        assert _p95([42.0]) == 42.0

    def test_10_values_p95_is_last(self):
        # ceil(0.95 * 10) - 1 = 10 - 1 = 9 → index 9 = 10.0
        vals = [float(i) for i in range(1, 11)]
        assert _p95(vals) == 10.0

    def test_20_values(self):
        # ceil(0.95 * 20) - 1 = 19 - 1 = 18 → index 18 = 19.0
        vals = [float(i) for i in range(1, 21)]
        assert _p95(vals) == 19.0

    def test_100_values(self):
        # ceil(0.95 * 100) - 1 = 95 - 1 = 94 → index 94 = 95.0
        vals = [float(i) for i in range(1, 101)]
        assert _p95(vals) == 95.0

    def test_two_values(self):
        # ceil(0.95 * 2) - 1 = 2 - 1 = 1 → index 1 = larger value
        assert _p95([1.0, 2.0]) == 2.0


# ── _compute_stats ─────────────────────────────────────────────────────────────

class TestComputeStats:
    def test_single_value_std_is_zero(self):
        stats = _compute_stats([7.0])
        assert stats.std == 0.0
        assert stats.mean == 7.0
        assert stats.min == 7.0
        assert stats.max == 7.0
        assert stats.p95 == 7.0
        assert stats.count == 1

    def test_symmetric_range(self):
        # [1, 2, 3, 4, 5]: mean=3, sample std=√2.5
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = _compute_stats(vals)
        assert stats.mean == pytest.approx(3.0)
        assert stats.std == pytest.approx(math.sqrt(2.5))
        assert stats.min == 1.0
        assert stats.max == 5.0
        assert stats.count == 5

    def test_returns_metric_stats_type(self):
        assert isinstance(_compute_stats([1.0, 2.0]), MetricStats)

    def test_std_non_negative(self):
        for vals in [[1.0], [1.0, 1.0], [0.0, 100.0], list(range(50))]:
            assert _compute_stats([float(v) for v in vals]).std >= 0.0

    def test_min_lte_mean_lte_max(self):
        import random
        random.seed(42)
        vals = [random.uniform(0, 100) for _ in range(30)]
        stats = _compute_stats(vals)
        assert stats.min <= stats.mean <= stats.max

    def test_p95_between_min_and_max(self):
        vals = [float(i) for i in range(1, 21)]
        stats = _compute_stats(vals)
        assert stats.min <= stats.p95 <= stats.max


# ── RollingAggregator ──────────────────────────────────────────────────────────

class TestRollingAggregator:
    def test_empty_window_returns_none(self):
        agg = RollingAggregator(window_seconds=60, _clock=_clock())
        assert agg.get_stats("nonexistent") is None

    def test_single_event_returns_aggregate_window(self):
        agg = RollingAggregator(window_seconds=60, _clock=_clock())
        agg.ingest(_event())
        stats = agg.get_stats("src")
        assert isinstance(stats, AggregateWindow)

    def test_event_count_correct(self):
        agg = RollingAggregator(window_seconds=60, _clock=_clock())
        for _ in range(5):
            agg.ingest(_event())
        assert agg.get_stats("src").event_count == 5

    def test_stale_events_evicted(self):
        # Event is 65s old; window is 60s → should be evicted
        agg = RollingAggregator(window_seconds=60, _clock=_clock(_BASE_TIME))
        agg.ingest(_event(ts=_BASE_TIME - timedelta(seconds=65)))
        assert agg.get_stats("src") is None

    def test_boundary_event_just_inside_window(self):
        # Event is exactly 59s old; window is 60s → should be kept
        agg = RollingAggregator(window_seconds=60, _clock=_clock(_BASE_TIME))
        agg.ingest(_event(ts=_BASE_TIME - timedelta(seconds=59)))
        assert agg.get_stats("src") is not None

    def test_boundary_event_just_outside_window(self):
        # Event is exactly 61s old; window is 60s → should be evicted
        agg = RollingAggregator(window_seconds=60, _clock=_clock(_BASE_TIME))
        agg.ingest(_event(ts=_BASE_TIME - timedelta(seconds=61)))
        assert agg.get_stats("src") is None

    def test_mixed_old_and_recent_events(self):
        agg = RollingAggregator(window_seconds=60, _clock=_clock(_BASE_TIME))
        agg.ingest(_event(metrics={"cpu": 99.0}, ts=_BASE_TIME - timedelta(seconds=90)))
        agg.ingest(_event(metrics={"cpu": 10.0}, ts=_BASE_TIME - timedelta(seconds=10)))
        stats = agg.get_stats("src")
        assert stats is not None
        assert stats.event_count == 1
        assert stats.metrics["cpu"].mean == pytest.approx(10.0)

    def test_p95_accuracy_against_known_input(self):
        # Insert 20 events with values 1.0..20.0; p95 = 19.0
        agg = RollingAggregator(window_seconds=3600, _clock=_clock(_BASE_TIME))
        for i in range(1, 21):
            ts = _BASE_TIME - timedelta(seconds=3600 - i)
            agg.ingest(_event(source_id="p95-src", metrics={"value": float(i)}, ts=ts))

        stats = agg.get_stats("p95-src")
        assert stats is not None
        assert stats.metrics["value"].p95 == 19.0

    def test_multiple_metrics_per_event(self):
        agg = RollingAggregator(window_seconds=60, _clock=_clock(_BASE_TIME))
        agg.ingest(_event(metrics={"cpu": 40.0, "mem": 70.0}))
        agg.ingest(_event(metrics={"cpu": 60.0, "mem": 80.0}))
        stats = agg.get_stats("src")
        assert stats.metrics["cpu"].mean == pytest.approx(50.0)
        assert stats.metrics["mem"].mean == pytest.approx(75.0)

    def test_multiple_sources_are_independent(self):
        agg = RollingAggregator(window_seconds=60, _clock=_clock(_BASE_TIME))
        ts = _BASE_TIME - timedelta(seconds=5)
        agg.ingest(_event(source_id="src-A", metrics={"m": 1.0}, ts=ts))
        agg.ingest(_event(source_id="src-B", metrics={"m": 99.0}, ts=ts))
        assert agg.get_stats("src-A").metrics["m"].mean == 1.0
        assert agg.get_stats("src-B").metrics["m"].mean == 99.0

    def test_domain_comes_from_most_recent_event(self):
        agg = RollingAggregator(window_seconds=60, _clock=_clock(_BASE_TIME))
        agg.ingest(_event(domain="infra", ts=_BASE_TIME - timedelta(seconds=20)))
        assert agg.get_stats("src").domain == "infra"

    def test_computed_at_matches_clock(self):
        fixed = datetime(2024, 1, 1, tzinfo=UTC)
        agg = RollingAggregator(window_seconds=60, _clock=Mock(return_value=fixed))
        agg.ingest(_event(ts=fixed - timedelta(seconds=5)))
        assert agg.get_stats("src").computed_at == fixed

    def test_window_seconds_preserved_in_output(self):
        agg = RollingAggregator(window_seconds=120, _clock=_clock())
        agg.ingest(_event())
        assert agg.get_stats("src").window_seconds == 120

    def test_all_source_ids(self):
        agg = RollingAggregator(window_seconds=60, _clock=_clock())
        agg.ingest(_event(source_id="a"))
        agg.ingest(_event(source_id="b"))
        assert set(agg.all_source_ids()) == {"a", "b"}

    def test_configurable_window_size(self):
        # 30s window; event 35s old should be evicted
        agg = RollingAggregator(window_seconds=30, _clock=_clock(_BASE_TIME))
        agg.ingest(_event(ts=_BASE_TIME - timedelta(seconds=35)))
        assert agg.get_stats("src") is None
