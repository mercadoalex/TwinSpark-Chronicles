"""Discovers and applies versioned SQL migration scripts.

Migration files live in ``backend/app/db/migrations/`` and follow the naming
convention ``NNN_description.sql`` where NNN is a zero-padded integer version.

Requirements: 1.1–1.4, 2.1–2.5
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from app.db import MigrationError
from app.db.connection import DatabaseConnection

logger = logging.getLogger(__name__)

_DEFAULT_MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


class MigrationRunner:
    """Discovers and applies versioned SQL migration scripts."""

    def __init__(
        self,
        db: DatabaseConnection,
        migrations_dir: str | None = None,
    ) -> None:
        self._db = db
        self._dir = migrations_dir or _DEFAULT_MIGRATIONS_DIR
        if not os.path.isdir(self._dir):
            raise FileNotFoundError(
                f"Migrations directory not found: {self._dir}"
            )

    async def ensure_migration_table(self) -> None:
        """Create schema_migrations table if it doesn't exist."""
        await self._db.execute(
            """CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                script_name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )"""
        )

    async def get_applied_versions(self) -> list[str]:
        """Return list of applied version identifiers, ascending."""
        await self.ensure_migration_table()
        rows = await self._db.fetch_all(
            "SELECT version FROM schema_migrations ORDER BY version ASC"
        )
        return [r["version"] for r in rows]

    def _discover_scripts(self) -> list[tuple[str, str]]:
        """Return sorted list of (version, filename) from migrations dir."""
        scripts: list[tuple[str, str]] = []
        for fname in sorted(os.listdir(self._dir)):
            if not fname.endswith(".sql"):
                continue
            version = fname.split("_", 1)[0]
            scripts.append((version, fname))
        # Check for duplicate versions
        versions = [v for v, _ in scripts]
        seen: set[str] = set()
        for v in versions:
            if v in seen:
                dupes = [f for ver, f in scripts if ver == v]
                raise MigrationError(
                    f"Duplicate migration version '{v}': {dupes}"
                )
            seen.add(v)
        return scripts

    async def get_pending_migrations(self) -> list[tuple[str, str]]:
        """Return (version, filename) tuples for unapplied scripts."""
        applied = set(await self.get_applied_versions())
        return [
            (v, f) for v, f in self._discover_scripts() if v not in applied
        ]

    async def apply_all(self, dry_run: bool = False) -> list[str]:
        """Apply all pending migrations in order.

        Returns list of applied script names. If dry_run is True, returns
        the pending list without executing.
        """
        pending = await self.get_pending_migrations()
        if not pending:
            return []

        if dry_run:
            return [fname for _, fname in pending]

        applied: list[str] = []
        for version, fname in pending:
            fpath = os.path.join(self._dir, fname)
            sql = Path(fpath).read_text(encoding="utf-8")
            try:
                await self._db.execute_script(sql)
                now = datetime.now(timezone.utc).isoformat()
                await self._db.execute(
                    "INSERT INTO schema_migrations (version, script_name, applied_at) VALUES (?, ?, ?)",
                    (version, fname, now),
                )
                applied.append(fname)
                logger.info("Applied migration: %s", fname)
            except Exception as exc:
                raise MigrationError(
                    f"Migration '{fname}' failed: {exc}"
                ) from exc
        return applied

    async def current_version(self) -> str | None:
        """Return the highest applied version, or None."""
        row = await self._db.fetch_one(
            "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
        )
        return row["version"] if row else None
