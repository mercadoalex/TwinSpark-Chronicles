"""Async database abstraction over aiosqlite and asyncpg.

Application code uses ``?`` placeholders everywhere. When the backend is
PostgreSQL the connection rewrites them to ``$1, $2, ...`` automatically.

Requirements: 4.1–4.6, 5.1–5.3
"""

from __future__ import annotations

import logging
import os
import re
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import aiosqlite

from app.db import DatabaseConnectionError

logger = logging.getLogger(__name__)

_DEFAULT_URI = "sqlite:///./sibling_data.db"
_PASSWORD_RE = re.compile(r"://([^:]+):([^@]+)@")


def _mask_uri(uri: str) -> str:
    """Replace password portion of a URI with '***'."""
    return _PASSWORD_RE.sub(r"://\1:***@", uri)


def _normalize_placeholders(sql: str) -> str:
    """Rewrite ``?`` placeholders to ``$1, $2, ...`` for asyncpg."""
    counter = 0

    def _replace(_match: re.Match) -> str:
        nonlocal counter
        counter += 1
        return f"${counter}"

    return re.sub(r"\?", _replace, sql)


class DatabaseConnection:
    """Async database abstraction over aiosqlite and asyncpg."""

    def __init__(self, uri: str | None = None) -> None:
        self._uri = uri or os.getenv("DATABASE_URL") or _DEFAULT_URI
        if self._uri.startswith("sqlite"):
            self._backend = "sqlite"
        elif self._uri.startswith("postgresql"):
            self._backend = "postgresql"
        else:
            raise ValueError(
                f"Unsupported DATABASE_URL scheme. Expected 'sqlite://...' or "
                f"'postgresql://...', got: {_mask_uri(self._uri)}"
            )
        self._conn: Any = None

    @property
    def backend(self) -> str:
        return self._backend

    # ── lifecycle ─────────────────────────────────────────────────

    async def connect(self) -> None:
        """Open the underlying driver connection."""
        try:
            if self._backend == "sqlite":
                # Extract path from sqlite:///path or sqlite:///:memory:
                path = self._uri.split("sqlite:///", 1)[-1] or ":memory:"
                self._conn = await aiosqlite.connect(path)
                self._conn.row_factory = aiosqlite.Row
            else:
                try:
                    import asyncpg  # lazy import
                except ImportError as exc:
                    raise ImportError(
                        "asyncpg is required for PostgreSQL. Install with: pip install asyncpg"
                    ) from exc
                self._conn = await asyncpg.connect(self._uri)
        except ImportError:
            raise
        except Exception as exc:
            raise DatabaseConnectionError(
                f"Failed to connect to {_mask_uri(self._uri)}: {exc}"
            ) from exc

    async def close(self) -> None:
        """Close the underlying driver connection."""
        if self._conn is None:
            return
        try:
            await self._conn.close()
        except Exception:
            pass
        self._conn = None

    # ── query helpers ─────────────────────────────────────────────

    async def execute(self, sql: str, params: tuple = ()) -> None:
        """Execute a write statement (INSERT/UPDATE/DELETE/DDL)."""
        if self._backend == "sqlite":
            await self._conn.execute(sql, params)
            await self._conn.commit()
        else:
            await self._conn.execute(_normalize_placeholders(sql), *params)

    async def execute_script(self, sql: str) -> None:
        """Execute a multi-statement SQL script (used by migration runner)."""
        if self._backend == "sqlite":
            await self._conn.executescript(sql)
            await self._conn.commit()
        else:
            await self._conn.execute(sql)

    async def fetch_one(self, sql: str, params: tuple = ()) -> dict | None:
        """Execute a query and return the first row as a dict, or None."""
        if self._backend == "sqlite":
            cursor = await self._conn.execute(sql, params)
            row = await cursor.fetchone()
            return dict(row) if row else None
        else:
            row = await self._conn.fetchrow(
                _normalize_placeholders(sql), *params
            )
            return dict(row) if row else None

    async def fetch_all(self, sql: str, params: tuple = ()) -> list[dict]:
        """Execute a query and return all rows as list of dicts."""
        if self._backend == "sqlite":
            cursor = await self._conn.execute(sql, params)
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
        else:
            rows = await self._conn.fetch(
                _normalize_placeholders(sql), *params
            )
            return [dict(r) for r in rows]

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """Context manager wrapping statements in BEGIN/COMMIT."""
        if self._backend == "sqlite":
            # aiosqlite auto-commits; we use manual transaction control
            await self._conn.execute("BEGIN")
            try:
                yield
                await self._conn.commit()
            except Exception:
                await self._conn.rollback()
                raise
        else:
            tr = self._conn.transaction()
            async with tr:
                yield
