import logging
import time

from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

logger = logging.getLogger(__name__)

_RETRY_BASE_WAIT = 2  # seconds; doubles each attempt


def build_producer(broker: str, max_retries: int = 3) -> KafkaProducer:
    """Create a KafkaProducer, retrying up to max_retries times with exponential backoff."""
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=broker,
                value_serializer=lambda v: v.encode("utf-8"),
                acks="all",
                retries=5,
                max_block_ms=10_000,
                request_timeout_ms=15_000,
            )
            logger.info("Connected to Kafka broker at %s", broker)
            return producer
        except NoBrokersAvailable as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = _RETRY_BASE_WAIT**attempt
                logger.warning(
                    "Kafka broker unavailable (attempt %d/%d). Retrying in %ds…",
                    attempt,
                    max_retries,
                    wait,
                )
                time.sleep(wait)
            else:
                logger.error("Kafka broker unreachable after %d attempts.", max_retries)

    raise RuntimeError(
        f"Could not connect to Kafka at {broker!r} after {max_retries} attempts"
    ) from last_exc


def send_event(producer: KafkaProducer, topic: str, payload: str) -> None:
    """Send a pre-serialized JSON string to the given topic."""
    future = producer.send(topic, value=payload)
    try:
        future.get(timeout=10)
    except KafkaError as exc:
        logger.error("Failed to deliver message to topic %s: %s", topic, exc)
        raise
