"""DB query functions for aggregate stats (MongoDB)."""

from motor.motor_asyncio import AsyncIOMotorDatabase

_VALID_DOMAINS = {"infra", "ecommerce", "iot"}
_ALL_DOMAINS = sorted(_VALID_DOMAINS)


async def fetch_summary(
    db: AsyncIOMotorDatabase,
    domain: str | None,
) -> list[dict]:
    """Return a list of DomainSummary dicts (one per domain or just the requested one).

    Raises ValueError for unknown domain values.
    """
    if domain is not None and domain not in _VALID_DOMAINS:
        raise ValueError(
            f"Invalid domain: {domain!r}. Must be one of {sorted(_VALID_DOMAINS)}."
        )

    domains = [domain] if domain else _ALL_DOMAINS
    results = []
    for d in domains:
        event_count = await db.raw_events.count_documents({"domain": d})
        anomaly_count = await db.anomalies.count_documents({"domain": d})
        auto_flag_count = await db.anomalies.count_documents(
            {"domain": d, "confidence_tier": "auto_flag"}
        )

        avg_pipeline = [
            {"$match": {"domain": d}},
            {"$group": {"_id": None, "avg": {"$avg": "$anomaly_score"}}},
        ]
        avg_cursor = db.anomalies.aggregate(avg_pipeline)
        avg_docs = await avg_cursor.to_list(1)
        avg_score = float(avg_docs[0]["avg"]) if avg_docs else None

        results.append({
            "domain": d,
            "event_count": event_count,
            "anomaly_count": anomaly_count,
            "auto_flag_count": auto_flag_count,
            "avg_anomaly_score": avg_score,
        })
    return results
