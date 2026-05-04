"""Unit tests for api/services/event_service.py (MongoDB/motor)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from api.services.event_service import fetch_events


def _make_db(count: int, docs: list[dict]) -> MagicMock:
    mock_db = MagicMock()
    mock_db.raw_events.count_documents = AsyncMock(return_value=count)
    mock_cursor = MagicMock()
    mock_cursor.to_list = AsyncMock(return_value=docs)
    mock_db.raw_events.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
    return mock_db


_ROW = {"event_id": "a", "source_id": "s", "domain": "infra",
        "timestamp": None, "metrics": {}, "metadata": {}}


# ── Happy path ─────────────────────────────────────────────────────────────────

class TestFetchEventsHappyPath:
    @pytest.mark.asyncio
    async def test_returns_tuple(self):
        db = _make_db(3, [_ROW] * 3)
        items, total = await fetch_events(db, None, 50, 0)
        assert isinstance(items, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_total_matches_count(self):
        db = _make_db(42, [])
        _, total = await fetch_events(db, None, 50, 0)
        assert total == 42

    @pytest.mark.asyncio
    async def test_items_are_dicts(self):
        db = _make_db(1, [_ROW])
        items, _ = await fetch_events(db, None, 50, 0)
        assert isinstance(items[0], dict)

    @pytest.mark.asyncio
    async def test_domain_filter_passed_to_count(self):
        db = _make_db(0, [])
        await fetch_events(db, "infra", 50, 0)
        db.raw_events.count_documents.assert_awaited_once_with({"domain": "infra"})

    @pytest.mark.asyncio
    async def test_no_domain_filter_uses_empty_filter(self):
        db = _make_db(0, [])
        await fetch_events(db, None, 50, 0)
        db.raw_events.count_documents.assert_awaited_once_with({})

    @pytest.mark.asyncio
    async def test_limit_and_offset_forwarded(self):
        db = _make_db(0, [])
        await fetch_events(db, None, 100, 200)
        chain = db.raw_events.find.return_value.sort.return_value.skip.return_value
        chain.limit.assert_called_once_with(100)
        db.raw_events.find.return_value.sort.return_value.skip.assert_called_once_with(200)


# ── Empty result ───────────────────────────────────────────────────────────────

class TestFetchEventsEmpty:
    @pytest.mark.asyncio
    async def test_empty_items_when_no_rows(self):
        db = _make_db(0, [])
        items, total = await fetch_events(db, None, 50, 0)
        assert items == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_total_zero_when_no_rows(self):
        db = _make_db(0, [])
        _, total = await fetch_events(db, None, 50, 0)
        assert total == 0


# ── Invalid domain ─────────────────────────────────────────────────────────────

class TestFetchEventsInvalidDomain:
    @pytest.mark.asyncio
    async def test_invalid_domain_raises_value_error(self):
        db = _make_db(0, [])
        with pytest.raises(ValueError, match="Invalid domain"):
            await fetch_events(db, "blockchain", 50, 0)

    @pytest.mark.asyncio
    async def test_invalid_domain_error_names_the_value(self):
        db = _make_db(0, [])
        with pytest.raises(ValueError, match="blockchain"):
            await fetch_events(db, "blockchain", 50, 0)

    @pytest.mark.asyncio
    async def test_invalid_domain_does_not_call_db(self):
        db = _make_db(0, [])
        try:
            await fetch_events(db, "bad", 50, 0)
        except ValueError:
            pass
        db.raw_events.count_documents.assert_not_awaited()


# ── Pagination ─────────────────────────────────────────────────────────────────

class TestFetchEventsPagination:
    @pytest.mark.asyncio
    async def test_large_offset_returns_empty_items(self):
        db = _make_db(5, [])
        items, total = await fetch_events(db, None, 50, 1000)
        assert items == []
        assert total == 5

    @pytest.mark.asyncio
    async def test_limit_1_returns_at_most_1(self):
        db = _make_db(10, [_ROW])
        items, _ = await fetch_events(db, None, 1, 0)
        assert len(items) == 1
