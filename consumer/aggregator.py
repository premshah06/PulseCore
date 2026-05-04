import math
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from producer.models import StreamEvent


@dataclass(frozen=True)
class MetricStats:
    mean: float
    std: float
    min: float
    max: float
    p95: float
    count: int


@dataclass(frozen=True)
class AggregateWindow:
    source_id: str
    domain: str
    window_seconds: int
    computed_at: datetime
    event_count: int
    metrics: dict[str, MetricStats]


def _p95(sorted_values: list[float]) -> float:
    """Nearest-rank p95: index = ceil(0.95 * n) - 1."""
    idx = max(0, math.ceil(0.95 * len(sorted_values)) - 1)
    return sorted_values[idx]


def _compute_stats(values: list[float]) -> MetricStats:
    n = len(values)
    sorted_vals = sorted(values)
    mean = sum(values) / n
    std = (
        math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1)) if n >= 2 else 0.0
    )
    return MetricStats(
        mean=mean,
        std=std,
        min=sorted_vals[0],
        max=sorted_vals[-1],
        p95=_p95(sorted_vals),
        count=n,
    )


class RollingAggregator:
    """Maintains a per-source rolling window and computes live statistics.

    Window eviction is based on event.timestamp vs the injected clock,
    making the aggregator fully deterministic in tests.
    """

    def __init__(
        self,
        window_seconds: int = 60,
        _clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._window_seconds = window_seconds
        self._clock = _clock or (lambda: datetime.now(UTC))
        # source_id -> deque of (event.timestamp, StreamEvent)
        self._windows: dict[str, deque] = defaultdict(deque)

    def ingest(self, event: StreamEvent) -> None:
        self._windows[event.source_id].append((event.timestamp, event))

    def _evict(self, source_id: str) -> None:
        cutoff = self._clock().timestamp() - self._window_seconds
        window = self._windows[source_id]
        while window and window[0][0].timestamp() < cutoff:
            window.popleft()

    def get_stats(self, source_id: str) -> AggregateWindow | None:
        """Return aggregated statistics for all events in the current window.

        Returns None if the window is empty (no events, or all evicted).
        """
        self._evict(source_id)
        window = self._windows[source_id]
        if not window:
            return None

        events = [e for _, e in window]
        domain = events[-1].domain

        metric_values: dict[str, list[float]] = defaultdict(list)
        for event in events:
            for k, v in event.metrics.items():
                metric_values[k].append(v)

        return AggregateWindow(
            source_id=source_id,
            domain=domain,
            window_seconds=self._window_seconds,
            computed_at=self._clock(),
            event_count=len(events),
            metrics={name: _compute_stats(vals) for name, vals in metric_values.items()},
        )

    def all_source_ids(self) -> list[str]:
        return list(self._windows.keys())
