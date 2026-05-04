"""Per-event scoring pipeline: inference → anomaly write → WebSocket broadcast.

Extracted from consumer/main.py so it can be unit-tested without Kafka or
a real asyncio event loop.  consumer/main.py calls score_event() once per
processed StreamEvent after the raw_events write succeeds.
"""

import logging
from datetime import UTC, datetime

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from consumer.db import write_anomaly
from producer.models import StreamEvent

logger = logging.getLogger(__name__)

# Placeholder written to anomalies when the inference sidecar is unreachable.
# confidence_tier="log_only" ensures it never triggers an alert.
_FALLBACK_RESULT: dict = {
    "anomaly_score": 0.0,
    "confidence_tier": "log_only",
    "is_anomaly": False,
    "raw_label": 1,
    "latency_ms": 0.0,
}


async def score_event(
    event: StreamEvent,
    db: AsyncIOMotorDatabase,
    http_client: httpx.AsyncClient,
    inference_url: str,
    broadcast_url: str,
    internal_secret: str,
    inference_timeout_s: float,
) -> None:
    """Score one event end-to-end.

    1. POST to inference sidecar → AnomalyResult (or fallback on failure)
    2. Write anomaly to MongoDB anomalies collection
    3. POST LiveUpdate to /internal/broadcast → WebSocket fan-out

    Never raises.  All failures are logged and the consumer loop continues.
    """
    result = await _call_inference(http_client, inference_url, event, inference_timeout_s)

    anomaly_id = await write_anomaly(db, event, result)
    if anomaly_id is None:
        # write_anomaly already logged the error
        return

    await _broadcast(http_client, broadcast_url, internal_secret, anomaly_id, event, result)


async def _call_inference(
    client: httpx.AsyncClient,
    url: str,
    event: StreamEvent,
    timeout_s: float,
) -> dict:
    """POST /predict and return the AnomalyResult dict.

    Returns _FALLBACK_RESULT on any network or application error.
    """
    payload = {
        "source_id": event.source_id,
        "domain": event.domain,
        "metrics": event.metrics,
        "timestamp": event.timestamp.isoformat(),
    }
    try:
        resp = await client.post(f"{url}/predict", json=payload, timeout=timeout_s)
        resp.raise_for_status()
        return resp.json()
    except httpx.TimeoutException:
        logger.warning(
            "Inference timeout domain=%s source_id=%s url=%s",
            event.domain, event.source_id, url,
        )
    except httpx.ConnectError as exc:
        logger.warning(
            "Inference connection error domain=%s: %s", event.domain, exc
        )
    except Exception as exc:
        logger.warning(
            "Inference error domain=%s source_id=%s: %s",
            event.domain, event.source_id, exc,
        )
    return dict(_FALLBACK_RESULT)


async def _broadcast(
    client: httpx.AsyncClient,
    url: str,
    secret: str,
    anomaly_id: str,
    event: StreamEvent,
    result: dict,
) -> None:
    """POST LiveUpdate payload to /internal/broadcast.

    Logs a warning on failure; never raises.
    """
    payload = {
        "type": "anomaly",
        "data": {
            "id": anomaly_id,
            "source_id": event.source_id,
            "domain": event.domain,
            "timestamp": event.timestamp.isoformat(),
            "anomaly_score": result["anomaly_score"],
            "confidence_tier": result["confidence_tier"],
            "is_anomaly": result["is_anomaly"],
            "raw_label": result.get("raw_label", 1),
            "latency_ms": result["latency_ms"],
            "detected_at": datetime.now(UTC).isoformat(),
        },
    }
    try:
        resp = await client.post(
            f"{url}/internal/broadcast",
            json=payload,
            headers={"X-Internal-Secret": secret},
            timeout=3.0,
        )
        resp.raise_for_status()
    except Exception as exc:
        logger.warning("Broadcast failed anomaly_id=%s: %s", anomaly_id, exc)
