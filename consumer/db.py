import logging
from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from producer.models import StreamEvent

logger = logging.getLogger(__name__)


async def write_event(db: AsyncIOMotorDatabase, event: StreamEvent) -> bool:
    """Upsert a StreamEvent into raw_events. Retries once on failure.

    Returns True on success, False if both attempts fail.
    Never raises — callers must not crash on DB errors.
    """
    doc = {
        "event_id": event.event_id,
        "source_id": event.source_id,
        "domain": event.domain,
        "timestamp": event.timestamp,
        "metrics": event.metrics,
        "metadata": event.metadata,
    }
    for attempt in range(2):
        try:
            await db.raw_events.update_one(
                {"event_id": event.event_id},
                {"$setOnInsert": doc},
                upsert=True,
            )
            return True
        except Exception as exc:
            if attempt == 0:
                logger.warning(
                    "DB write attempt 1 failed for event_id=%s: %s. Retrying…",
                    event.event_id,
                    exc,
                )
            else:
                logger.error(
                    "DB write failed after retry. event_id=%s domain=%s error=%s",
                    event.event_id,
                    event.domain,
                    exc,
                )
    return False


async def write_anomaly(
    db: AsyncIOMotorDatabase,
    event: StreamEvent,
    result: dict,
) -> str | None:
    """Insert one anomaly document into the anomalies collection.

    Pre-generates the ObjectId so the string id is stored inside the document
    itself (avoids a post-insert lookup).  Returns the id string on success,
    None on failure (already logged).  Never raises.
    """
    oid = ObjectId()
    doc = {
        "_id": oid,
        "id": str(oid),
        "source_id": event.source_id,
        "domain": event.domain,
        "timestamp": event.timestamp,
        "anomaly_score": float(result["anomaly_score"]),
        "confidence_tier": result["confidence_tier"],
        "is_anomaly": bool(result["is_anomaly"]),
        "raw_label": int(result.get("raw_label", 1)),
        "latency_ms": float(result["latency_ms"]),
        "detected_at": datetime.now(UTC),
    }
    try:
        await db.anomalies.insert_one(doc)
        return str(oid)
    except Exception as exc:
        logger.error(
            "Anomaly write failed source_id=%s domain=%s: %s",
            event.source_id, event.domain, exc,
        )
        return None
