"""Tests for BaseRepository ABC contract."""

import pytest
from unittest.mock import AsyncMock
from app.db.base_repository import BaseRepository


def test_cannot_instantiate_directly():
    """BaseRepository is abstract and cannot be instantiated."""
    with pytest.raises(TypeError):
        BaseRepository(db=AsyncMock())


def test_subclass_missing_methods_raises():
    """A subclass that doesn't implement all abstract methods raises TypeError."""

    class IncompleteRepo(BaseRepository):
        async def find_by_id(self, entity_id):
            return None

    with pytest.raises(TypeError):
        IncompleteRepo(db=AsyncMock())


def test_complete_subclass_can_be_instantiated():
    """A subclass implementing all four methods can be instantiated."""

    class CompleteRepo(BaseRepository):
        async def find_by_id(self, entity_id):
            return None

        async def find_all(self, **filters):
            return []

        async def save(self, entity):
            pass

        async def delete(self, entity_id):
            return False

    repo = CompleteRepo(db=AsyncMock())
    assert repo._db is not None
