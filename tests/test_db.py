"""Unit tests for consumer.db.write_event (motor/MongoDB)."""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from consumer.db import write_event
from producer.models import StreamEvent


def _event() -> StreamEvent:
    return StreamEvent(
        source_id="db-test-src",
        domain="infra",
        metrics={"cpu_user_pct": 45.0},
    )


def _make_db(side_effect=None) -> MagicMock:
    """Return a mock AsyncIOMotorDatabase whose raw_events.update_one is an AsyncMock."""
    db = MagicMock()
    db.raw_events.update_one = AsyncMock(side_effect=side_effect)
    return db


@pytest.mark.asyncio
async def test_write_event_success():
    db = _make_db()
    result = await write_event(db, _event())
    assert result is True
    db.raw_events.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_write_event_passes_correct_event_id():
    event = _event()
    db = _make_db()
    await write_event(db, event)
    call_args = db.raw_events.update_one.call_args
    # First positional arg is the filter dict {"event_id": ...}
    filter_doc = call_args[0][0]
    assert filter_doc["event_id"] == event.event_id


@pytest.mark.asyncio
async def test_write_event_retries_once_on_failure(caplog):
    db = _make_db(side_effect=RuntimeError("connection reset"))
    with caplog.at_level(logging.WARNING, logger="consumer.db"):
        result = await write_event(db, _event())
    assert result is False
    assert db.raw_events.update_one.call_count == 2


@pytest.mark.asyncio
async def test_write_event_logs_warning_on_first_failure(caplog):
    db = _make_db(side_effect=Exception("timeout"))
    with caplog.at_level(logging.WARNING, logger="consumer.db"):
        await write_event(db, _event())
    assert any("Retrying" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_write_event_logs_error_after_second_failure(caplog):
    db = _make_db(side_effect=Exception("disk full"))
    with caplog.at_level(logging.ERROR, logger="consumer.db"):
        await write_event(db, _event())
    error_records = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(error_records) == 1
    assert "failed after retry" in error_records[0].message


@pytest.mark.asyncio
async def test_write_event_does_not_raise_on_failure():
    db = _make_db(side_effect=Exception("catastrophic failure"))
    result = await write_event(db, _event())
    assert result is False


@pytest.mark.asyncio
async def test_write_event_succeed_on_second_attempt(caplog):
    db = _make_db(side_effect=[Exception("transient error"), None])
    with caplog.at_level(logging.WARNING, logger="consumer.db"):
        result = await write_event(db, _event())
    assert result is True
    assert db.raw_events.update_one.call_count == 2
