"""Abstract base repository defining the common CRUD contract.

All concrete repositories extend this class and receive a
DatabaseConnection via constructor injection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.db.connection import DatabaseConnection


class BaseRepository(ABC):
    """Abstract base for all repositories. Receives DatabaseConnection via DI."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    @abstractmethod
    async def find_by_id(self, entity_id: str) -> dict | None:
        """Fetch a single entity by primary key."""
        ...

    @abstractmethod
    async def find_all(self, **filters: Any) -> list[dict]:
        """Fetch all entities, optionally filtered."""
        ...

    @abstractmethod
    async def save(self, entity: dict) -> None:
        """Insert or update an entity."""
        ...

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by primary key. Returns True if deleted."""
        ...
