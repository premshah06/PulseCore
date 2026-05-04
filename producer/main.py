"""
Producer entry point.

Required env vars:
  DOMAIN            - one of: infra, ecommerce, iot
  KAFKA_BROKER      - e.g. localhost:9092
  KAFKA_TOPIC       - e.g. pulse.events
  EVENTS_PER_SECOND - float, default 1.0
"""

import logging
import os
import signal
import sys
import time

from producer.generators import get_generator
from producer.kafka_client import build_producer, send_event

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_running = True


def _handle_shutdown(signum, frame):  # noqa: ANN001
    global _running
    logger.info("Shutdown signal received, stopping producer…")
    _running = False


def main() -> None:
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    domain = os.environ.get("DOMAIN", "infra")
    broker = os.environ.get("KAFKA_BROKER", "localhost:9092")
    topic = os.environ.get("KAFKA_TOPIC", "pulse.events")
    eps = float(os.environ.get("EVENTS_PER_SECOND", "1.0"))

    if eps <= 0:
        logger.error("EVENTS_PER_SECOND must be > 0, got %s", eps)
        sys.exit(1)

    interval = 1.0 / eps

    logger.info(
        "Starting producer | domain=%s broker=%s topic=%s eps=%.2f",
        domain,
        broker,
        topic,
        eps,
    )

    generator = get_generator(domain)
    producer = build_producer(broker)

    sent = 0
    try:
        while _running:
            event = generator.generate()
            payload = event.model_dump_json()
            send_event(producer, topic, payload)
            sent += 1
            if sent % 100 == 0:
                logger.info("Sent %d events to topic %s", sent, topic)
            time.sleep(interval)
    finally:
        producer.flush()
        producer.close()
        logger.info("Producer stopped. Total events sent: %d", sent)


if __name__ == "__main__":
    main()
