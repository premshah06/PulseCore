"""
Bootstrap script — creates PulseCore collections, indexes, and TTL policies.

Run once against any node (standalone or RS primary):
    python schema/init_mongo.py
    MONGODB_URL=mongodb+srv://... python schema/init_mongo.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Index design rationale
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

raw_events
  event_id          unique      — idempotent upserts (Kafka at-least-once)
  (domain, ts)      compound    — primary query pattern: domain filter + time sort
  ingested_at TTL   30 days     — auto-expire hot event log; cold data moves to S3/archive

anomalies
  (domain, ts)      compound    — GET /api/anomalies?domain= + ORDER BY ts DESC
  (tier, ts)        compound    — GET /api/anomalies?tier=auto_flag
  ts                descending  — full-table time-range scans (no domain filter)
  detected_at TTL   90 days     — regulatory / audit retention window

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sharding strategy (production — requires mongos + config servers)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

raw_events  → hashed shard key: { source_id: "hashed" }
              Rationale: source_id has high cardinality and near-uniform
              distribution across thousands of sensors/hosts. Hashed
              sharding eliminates hotspots on write-heavy ingest path.
              Each Kafka partition maps cleanly to a subset of source_ids.

anomalies   → ranged shard key: { domain: 1, timestamp: -1 }
              Rationale: the three domains (infra/ecommerce/iot) map to
              natural zone shards. Range queries ("last 24 h of infra
              anomalies") stay within a single shard; no scatter-gather.
              Monotonically decreasing timestamp prevents write hotspot
              on the max-key shard (descending avoids chunk imbalance).

Enable with:
  sh.enableSharding("pulsecore")
  sh.shardCollection("pulsecore.raw_events",  { source_id: "hashed" })
  sh.shardCollection("pulsecore.anomalies",   { domain: 1, timestamp: -1 })

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Replica set read preference
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Write concern  : majority   — durable once 2 of 3 nodes acknowledge
Read preference: primaryPreferred for anomaly writes + WS broadcast
                 secondaryPreferred for GET /api/events (read-heavy, can tolerate slight lag)
"""

import asyncio
import os

import motor.motor_asyncio

_DEFAULT_URL = "mongodb://pulse:pulse@localhost:27017/pulsecore?authSource=admin"

# TTL durations
_RAW_EVENTS_TTL_DAYS = 30
_ANOMALIES_TTL_DAYS  = 90


async def init(url: str) -> None:
    client = motor.motor_asyncio.AsyncIOMotorClient(url)
    db = client["pulsecore"]

    # ── raw_events ────────────────────────────────────────────────────────────
    await _ensure_collection(db, "raw_events")

    await db.raw_events.create_index(
        [("event_id", 1)],
        unique=True,
        name="event_id_unique",
    )
    await db.raw_events.create_index(
        [("domain", 1), ("timestamp", -1)],
        name="domain_time",
    )
    # TTL: auto-expire records older than 30 days
    await db.raw_events.create_index(
        [("ingested_at", 1)],
        expireAfterSeconds=_RAW_EVENTS_TTL_DAYS * 86_400,
        name="raw_events_ttl_30d",
    )
    print(f"raw_events  : 3 indexes created (unique, domain+time, TTL {_RAW_EVENTS_TTL_DAYS}d)")

    # ── anomalies ─────────────────────────────────────────────────────────────
    await _ensure_collection(db, "anomalies")

    await db.anomalies.create_index(
        [("domain", 1), ("timestamp", -1)],
        name="domain_time",
    )
    await db.anomalies.create_index(
        [("confidence_tier", 1), ("timestamp", -1)],
        name="tier_time",
    )
    await db.anomalies.create_index(
        [("timestamp", -1)],
        name="timestamp_desc",
    )
    # TTL: auto-expire anomaly records older than 90 days
    await db.anomalies.create_index(
        [("detected_at", 1)],
        expireAfterSeconds=_ANOMALIES_TTL_DAYS * 86_400,
        name="anomalies_ttl_90d",
    )
    print(f"anomalies   : 4 indexes created (domain+time, tier+time, time, TTL {_ANOMALIES_TTL_DAYS}d)")

    # ── print RS status if available ──────────────────────────────────────────
    try:
        status = await client.admin.command("replSetGetStatus")
        members = status.get("members", [])
        primary = next((m["name"] for m in members if m.get("stateStr") == "PRIMARY"), "—")
        print(f"Replica set : rs0  primary={primary}  members={len(members)}")
    except Exception:
        print("Replica set : standalone (not in RS mode)")

    client.close()
    print("Done.")


async def _ensure_collection(db, name: str) -> None:
    existing = await db.list_collection_names()
    if name not in existing:
        await db.create_collection(name)


if __name__ == "__main__":
    url = os.getenv("MONGODB_URL", _DEFAULT_URL)
    asyncio.run(init(url))
