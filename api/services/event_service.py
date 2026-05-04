"""DB query functions for raw_events (MongoDB)."""

from motor.motor_asyncio import AsyncIOMotorDatabase

_VALID_DOMAINS = {"infra", "ecommerce", "iot"}

_PROJECT = {"_id": 0, "event_id": 1, "source_id": 1, "domain": 1,
            "timestamp": 1, "metrics": 1, "metadata": 1}


async def fetch_events(
    db: AsyncIOMotorDatabase,
    domain: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    """Return (items, total) for paginated event listing.

    Raises ValueError for unknown domain values so the router can return 422.
    """
    if domain is not None and domain not in _VALID_DOMAINS:
        raise ValueError(f"Invalid domain: {domain!r}. Must be one of {sorted(_VALID_DOMAINS)}.")

    filter_ = {"domain": domain} if domain else {}
    total = await db.raw_events.count_documents(filter_)
    cursor = (
        db.raw_events.find(filter_, _PROJECT)
        .sort("timestamp", -1)
        .skip(offset)
        .limit(limit)
    )
    docs = await cursor.to_list(None)
    return docs, total
