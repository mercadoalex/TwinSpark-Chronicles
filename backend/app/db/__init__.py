"""Database abstraction layer for Twin Spark Chronicles.

Provides a backend-agnostic async interface over aiosqlite (dev) and
asyncpg (production), plus a lightweight SQL migration runner.
"""


class DatabaseConnectionError(Exception):
    """Raised when the database connection cannot be established."""


class MigrationError(Exception):
    """Raised when a migration script fails to apply."""
