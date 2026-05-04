import json
import logging

from producer.models import StreamEvent

logger = logging.getLogger(__name__)


def process(raw: bytes) -> StreamEvent:
    """Deserialize Kafka message bytes into a validated StreamEvent.

    Raises ValueError for malformed JSON, missing fields, or unknown domain.
    Never raises any other exception — callers can safely skip on ValueError.
    """
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"Malformed JSON payload: {exc}") from exc

    try:
        event = StreamEvent.model_validate(data)
    except Exception as exc:
        raise ValueError(f"Invalid StreamEvent: {exc}") from exc

    return event
