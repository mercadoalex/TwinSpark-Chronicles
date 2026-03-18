"""CLI entry point for database migrations.

Usage (from backend/ directory):
    python3 -m app.db            # apply pending migrations
    python3 -m app.db --status   # show current version + applied list
    python3 -m app.db --dry-run  # list pending without executing

Requirements: 7.1–7.5
"""

import argparse
import asyncio
import sys

from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner


async def _run(args: argparse.Namespace) -> None:
    db = DatabaseConnection()
    await db.connect()
    runner = MigrationRunner(db)

    try:
        if args.status:
            version = await runner.current_version()
            applied = await runner.get_applied_versions()
            if not applied:
                print("No migrations applied yet.")
            else:
                print(f"Current version: {version}")
                print("Applied migrations:")
                for v in applied:
                    print(f"  {v}")
        elif args.dry_run:
            pending = await runner.get_pending_migrations()
            if not pending:
                print("Database is up to date.")
            else:
                print("Pending migrations (dry run):")
                for _, fname in pending:
                    print(f"  {fname}")
        else:
            applied = await runner.apply_all()
            if not applied:
                print("Database is up to date.")
            else:
                for name in applied:
                    print(f"Applied: {name}")
                print(f"Done. {len(applied)} migration(s) applied.")
    finally:
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--status", action="store_true", help="Show current schema version")
    parser.add_argument("--dry-run", action="store_true", help="List pending migrations without executing")
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
