"""
Consumer entry point.

Required env vars (with defaults):
  KAFKA_BROKER             - e.g. localhost:9092       (default: localhost:9092)
  KAFKA_TOPIC              - e.g. pulse.events         (default: pulse.events)
  KAFKA_GROUP_ID           - consumer group            (default: pulsecore-consumer)
  MONGODB_URL              - Motor DSN                 (default: mongodb://pulse:pulse@localhost:27017/pulsecore?authSource=admin)
  WINDOW_SECONDS           - rolling window length     (default: 60)
  LAG_THRESHOLD            - warn when lag exceeds N  (default: 1000)
  INFERENCE_URL_INFRA      - sidecar base URL          (default: http://inference-infra:8001)
  INFERENCE_URL_ECOMMERCE  - sidecar base URL          (default: http://inference-ecommerce:8002)
  INFERENCE_URL_IOT        - sidecar base URL          (default: http://inference-iot:8003)
  INFERENCE_TIMEOUT_MS     - per-call timeout ms       (default: 500)
  API_INTERNAL_URL         - FastAPI base URL          (default: http://api:8000)
  INTERNAL_SECRET          - shared secret for /internal/broadcast
"""

import asyncio
import logging
import os
import signal

import httpx
import motor.motor_asyncio
from aiokafka import AIOKafkaConsumer

from consumer.aggregator import RollingAggregator
from consumer.db import write_event
from consumer.pipeline import score_event
from consumer.processor import process

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_DOMAIN_INFERENCE_ENV = {
    "infra": "INFERENCE_URL_INFRA",
    "ecommerce": "INFERENCE_URL_ECOMMERCE",
    "iot": "INFERENCE_URL_IOT",
}
_DOMAIN_INFERENCE_DEFAULT = {
    "infra": "http://inference-infra:8001",
    "ecommerce": "http://inference-ecommerce:8002",
    "iot": "http://inference-iot:8003",
}


async def _check_lag(consumer: AIOKafkaConsumer, lag_threshold: int) -> None:
    try:
        partitions = consumer.assignment()
        if not partitions:
            return
        for tp in partitions:
            hw = consumer.highwater(tp)
            if hw is None:
                continue
            pos = await consumer.position(tp)
            lag = hw - pos
            if lag > lag_threshold:
                logger.warning(
                    "Consumer lag on %s[%d]: %d events (threshold: %d)",
                    tp.topic,
                    tp.partition,
                    lag,
                    lag_threshold,
                )
    except Exception as exc:
        logger.debug("Lag check skipped: %s", exc)


async def _sidecar_watchdog(
    http_client: httpx.AsyncClient,
    inference_urls: dict[str, str],
    stop_event: asyncio.Event,
) -> None:
    """Background task: warn every 60 s if any inference sidecar is unreachable."""
    while not stop_event.is_set():
        await asyncio.sleep(60)
        for domain, url in inference_urls.items():
            try:
                resp = await http_client.get(f"{url}/health", timeout=3.0)
                resp.raise_for_status()
            except Exception as exc:
                logger.warning("Sidecar unreachable domain=%s url=%s: %s", domain, url, exc)


async def main() -> None:
    broker = os.environ.get("KAFKA_BROKER", "localhost:9092")
    topic = os.environ.get("KAFKA_TOPIC", "pulse.events")
    group_id = os.environ.get("KAFKA_GROUP_ID", "pulsecore-consumer")
    mongo_url = os.environ.get(
        "MONGODB_URL",
        "mongodb://pulse:pulse@localhost:27017/pulsecore?authSource=admin",
    )
    window_seconds = int(os.environ.get("WINDOW_SECONDS", "60"))
    lag_threshold = int(os.environ.get("LAG_THRESHOLD", "1000"))
    inference_timeout_s = int(os.environ.get("INFERENCE_TIMEOUT_MS", "500")) / 1000.0
    api_internal_url = os.environ.get("API_INTERNAL_URL", "http://api:8000")
    internal_secret = os.environ.get("INTERNAL_SECRET", "")

    inference_urls = {
        domain: os.environ.get(env_key, _DOMAIN_INFERENCE_DEFAULT[domain])
        for domain, env_key in _DOMAIN_INFERENCE_ENV.items()
    }

    logger.info(
        "Starting consumer | broker=%s topic=%s group=%s window=%ds lag_threshold=%d",
        broker,
        topic,
        group_id,
        window_seconds,
        lag_threshold,
    )

    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
    db = mongo_client["pulsecore"]
    aggregator = RollingAggregator(window_seconds=window_seconds)

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=broker,
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig, _frame):
        logger.info("Shutdown signal received (%s), stopping…", sig)
        loop.call_soon_threadsafe(stop_event.set)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    await consumer.start()
    processed = skipped = db_failures = 0

    async with httpx.AsyncClient() as http_client:
        watchdog = asyncio.create_task(
            _sidecar_watchdog(http_client, inference_urls, stop_event)
        )
        try:
            while not stop_event.is_set():
                try:
                    batch = await asyncio.wait_for(
                        consumer.getmany(timeout_ms=1000, max_records=100),
                        timeout=2.0,
                    )
                except TimeoutError:
                    continue

                for _tp, messages in batch.items():
                    for msg in messages:
                        try:
                            event = process(msg.value)
                        except ValueError as exc:
                            logger.warning(
                                "Skipping message offset=%d: %s", msg.offset, exc
                            )
                            skipped += 1
                            continue

                        ok = await write_event(db, event)
                        if not ok:
                            db_failures += 1
                        else:
                            inference_url = inference_urls.get(
                                event.domain, inference_urls["infra"]
                            )
                            await score_event(
                                event=event,
                                db=db,
                                http_client=http_client,
                                inference_url=inference_url,
                                broadcast_url=api_internal_url,
                                internal_secret=internal_secret,
                                inference_timeout_s=inference_timeout_s,
                            )

                        aggregator.ingest(event)
                        processed += 1

                        if processed % 500 == 0:
                            logger.info(
                                "Progress: processed=%d skipped=%d db_failures=%d",
                                processed,
                                skipped,
                                db_failures,
                            )

                await _check_lag(consumer, lag_threshold)

        finally:
            watchdog.cancel()
            await consumer.stop()
            mongo_client.close()
            logger.info(
                "Consumer stopped. processed=%d skipped=%d db_failures=%d",
                processed,
                skipped,
                db_failures,
            )


if __name__ == "__main__":
    asyncio.run(main())
