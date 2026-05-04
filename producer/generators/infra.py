import random

from producer.generators.base import BaseGenerator
from producer.models import StreamEvent

_HOSTS = [f"host-{i:03d}" for i in range(1, 21)]


class InfraGenerator(BaseGenerator):
    """Simulates server/VM telemetry: CPU, memory, disk, and network metrics."""

    domain = "infra"

    def __init__(self, source_id: str | None = None) -> None:
        self._source_id = source_id or random.choice(_HOSTS)

    def generate(self) -> StreamEvent:
        cpu_user = random.uniform(0.0, 85.0)
        cpu_system = random.uniform(0.0, 15.0)

        return StreamEvent(
            source_id=self._source_id,
            domain=self.domain,
            metrics={
                "cpu_user_pct": round(cpu_user, 2),
                "cpu_system_pct": round(cpu_system, 2),
                "cpu_idle_pct": round(max(0.0, 100.0 - cpu_user - cpu_system), 2),
                "mem_used_pct": round(random.uniform(20.0, 95.0), 2),
                "mem_available_mb": round(random.uniform(512.0, 32768.0), 2),
                "disk_read_mb_s": round(random.uniform(0.0, 500.0), 2),
                "disk_write_mb_s": round(random.uniform(0.0, 300.0), 2),
                "disk_used_pct": round(random.uniform(10.0, 90.0), 2),
                "net_rx_mb_s": round(random.uniform(0.0, 1000.0), 2),
                "net_tx_mb_s": round(random.uniform(0.0, 1000.0), 2),
                "load_avg_1m": round(random.uniform(0.0, 16.0), 2),
            },
            metadata={"region": random.choice(["us-east-1", "us-west-2", "eu-west-1"])},
        )
