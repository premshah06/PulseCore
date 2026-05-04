import random

from producer.generators.base import BaseGenerator
from producer.models import StreamEvent

_DEVICES = [f"sensor-{i:04d}" for i in range(1, 51)]
_DEVICE_TYPES = ["thermostat", "weather_station", "industrial_monitor", "smart_meter"]


class IotGenerator(BaseGenerator):
    """Simulates IoT sensor telemetry: environmental and power metrics."""

    domain = "iot"

    def __init__(self, source_id: str | None = None) -> None:
        self._source_id = source_id or random.choice(_DEVICES)
        self._device_type = random.choice(_DEVICE_TYPES)

    def generate(self) -> StreamEvent:
        return StreamEvent(
            source_id=self._source_id,
            domain=self.domain,
            metrics={
                "temperature_celsius": round(random.uniform(-10.0, 55.0), 2),
                "humidity_pct": round(random.uniform(10.0, 99.0), 2),
                "pressure_hpa": round(random.uniform(870.0, 1084.0), 2),
                "battery_pct": round(random.uniform(5.0, 100.0), 2),
                "signal_rssi_dbm": round(random.uniform(-110.0, -30.0), 2),
                "uptime_seconds": round(random.uniform(0.0, 86400.0 * 365), 2),
                "error_count": float(random.randint(0, 10)),
                "voltage_v": round(random.uniform(3.0, 5.5), 3),
            },
            metadata={"device_type": self._device_type, "firmware": "1.4.2"},
        )
