"""DB query functions for anomalies (MongoDB)."""

from datetime import UTC, datetime

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

_VALID_TIERS = {"auto_flag", "soft_alert", "log_only"}

_PROJECT = {
    "_id": 0, "id": 1, "source_id": 1, "domain": 1, "timestamp": 1,
    "anomaly_score": 1, "confidence_tier": 1, "is_anomaly": 1,
    "raw_label": 1, "latency_ms": 1, "detected_at": 1,
}


async def fetch_anomalies(
    db: AsyncIOMotorDatabase,
    tier: str | None,
    since: datetime | None,
    limit: int,
) -> tuple[list[dict], int]:
    """Return (items, total) for filtered anomaly listing.

    Raises ValueError for unknown tier values so the router can return 422.
    """
    if tier is not None and tier not in _VALID_TIERS:
        raise ValueError(
            f"Invalid tier: {tier!r}. Must be one of {sorted(_VALID_TIERS)}."
        )

    filter_: dict = {}
    if tier:
        filter_["confidence_tier"] = tier
    if since:
        filter_["timestamp"] = {"$gte": since}

    total = await db.anomalies.count_documents(filter_)
    cursor = db.anomalies.find(filter_, _PROJECT).sort("timestamp", -1).limit(limit)
    docs = await cursor.to_list(None)
    return docs, total


async def ingest_anomaly(db: AsyncIOMotorDatabase, data: dict) -> dict:
    """Insert one anomaly and return the persisted record."""
    oid = ObjectId()
    doc = {
        "_id": oid,
        "id": str(oid),
        "source_id": data["source_id"],
        "domain": data["domain"],
        "timestamp": data["timestamp"],
        "anomaly_score": float(data["anomaly_score"]),
        "confidence_tier": data["confidence_tier"],
        "is_anomaly": bool(data["is_anomaly"]),
        "raw_label": int(data["raw_label"]),
        "latency_ms": float(data["latency_ms"]),
        "detected_at": datetime.now(UTC),
    }
    await db.anomalies.insert_one(doc)
    return doc
