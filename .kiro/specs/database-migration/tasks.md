# Implementation Plan: Database Migration

## Overview

Introduce a migration framework and database abstraction layer under `backend/app/db/`, refactor SiblingDB and WorldDB to use it, create a baseline migration capturing all 9 existing tables, wire everything into the orchestrator startup, and add a CLI entry point. All code is Python 3.11 with async/await.

## Tasks

- [x] 1. Create the database abstraction layer
  - [x] 1.1 Create `backend/app/db/__init__.py` and custom exceptions (`DatabaseConnectionError`, `MigrationError`)
    - Define both exception classes in `backend/app/db/__init__.py`
    - _Requirements: 4.6 (error handling), 2.5 (migration error reporting)_

  - [x] 1.2 Implement `DatabaseConnection` in `backend/app/db/connection.py`
    - Parse URI to determine backend (`sqlite` or `postgresql`), default to `DATABASE_URL` env var, fallback to `sqlite:///./sibling_data.db`
    - Implement `connect()`, `close()`, `execute()`, `fetch_one()`, `fetch_all()`, `transaction()` context manager
    - Implement `?` → `$N` placeholder normalization for PostgreSQL backend
    - Mask credentials in error messages using regex on the password portion
    - Import `asyncpg` lazily only when a `postgresql://` URI is provided
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3_

  - [ ]* 1.3 Write property test: URI prefix determines backend
    - **Property 6: URI prefix determines backend**
    - **Validates: Requirements 4.2, 4.3, 4.4**

  - [ ]* 1.4 Write property test: Placeholder normalization round-trip
    - **Property 7: Placeholder normalization round-trip**
    - **Validates: Requirements 4.5**

  - [ ]* 1.5 Write property test: Credential masking in error messages
    - **Property 8: Credential masking in error messages**
    - **Validates: Requirements 4.6**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Create the migration runner and baseline migration
  - [x] 3.1 Implement `MigrationRunner` in `backend/app/db/migration_runner.py`
    - Create `schema_migrations` table (version TEXT PK, script_name TEXT, applied_at TEXT)
    - Discover `.sql` files in `migrations/` directory, order by version prefix
    - Skip already-applied versions, execute unapplied scripts in order within a transaction per script
    - Roll back and raise `MigrationError` on failure with script name and error details
    - Implement `get_applied_versions()`, `get_pending_migrations()`, `apply_all(dry_run)`, `current_version()`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.2 Create `backend/app/db/migrations/001_baseline.sql`
    - `CREATE TABLE IF NOT EXISTS` for all 9 tables: `personality_profiles`, `relationship_models`, `skill_maps`, `session_summaries`, `initial_profiles`, `world_locations`, `world_location_history`, `world_npcs`, `world_items`
    - Match exact column definitions from current `SiblingDB.initialize()` and `WorldDB.initialize()`
    - _Requirements: 3.1, 3.2, 3.3_

  - [ ]* 3.3 Write property test: Migration discovery returns all files in version order
    - **Property 1: Migration discovery returns all files in version order**
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 3.4 Write property test: Only unapplied migrations execute, in order, and are recorded
    - **Property 2: Only unapplied migrations execute, in order, and are recorded**
    - **Validates: Requirements 1.2, 2.3, 2.4**

  - [ ]* 3.5 Write property test: Current version is the highest applied version
    - **Property 3: Current version is the highest applied version**
    - **Validates: Requirements 1.3**

  - [ ]* 3.6 Write property test: Failed migration rolls back without leaving a record
    - **Property 4: Failed migration rolls back without leaving a record**
    - **Validates: Requirements 2.5**

  - [ ]* 3.7 Write property test: Baseline migration is idempotent with existing data
    - **Property 5: Baseline migration is idempotent with existing data**
    - **Validates: Requirements 3.2**

  - [ ]* 3.8 Write property test: Dry-run does not modify the database
    - **Property 9: Dry-run does not modify the database**
    - **Validates: Requirements 7.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Create the migration CLI entry point
  - [x] 5.1 Implement `backend/app/db/__main__.py`
    - Invocable via `python3 -m app.db.migrate` from `backend/` directory
    - No arguments: apply all pending migrations, print each applied name
    - `--status`: print current schema version and list of applied migrations
    - `--dry-run`: print pending migrations without executing
    - Print "up to date" message when no pending migrations exist
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 5.2 Write unit tests for CLI flags (`--status`, `--dry-run`, no-args, up-to-date message)
    - Test each CLI flag produces expected output
    - _Requirements: 7.2, 7.3, 7.4, 7.5_

- [x] 6. Refactor SiblingDB to use DatabaseConnection
  - [x] 6.1 Update `backend/app/services/sibling_db.py`
    - Change constructor to accept `DatabaseConnection` instead of `db_path`
    - Replace all `await self._get_db()` + raw `aiosqlite` calls with `DatabaseConnection` methods (`execute`, `fetch_one`, `fetch_all`)
    - Remove `_get_db()` method and `aiosqlite` import
    - Remove inline `CREATE TABLE` statements from `initialize()` (make it a no-op or remove it)
    - Remove `close()` method (connection lifecycle owned by `DatabaseConnection`)
    - _Requirements: 6.1, 6.3, 6.4_

  - [ ]* 6.2 Write unit tests for refactored SiblingDB
    - Verify all CRUD operations work through `DatabaseConnection` with in-memory SQLite
    - _Requirements: 6.1, 9.1, 9.2, 9.3_

- [x] 7. Refactor WorldDB to use DatabaseConnection
  - [x] 7.1 Update `backend/app/services/world_db.py`
    - Change constructor to accept `DatabaseConnection` instead of `sibling_db`
    - Replace all `await self._get_db()` + raw `aiosqlite` calls with `DatabaseConnection` methods
    - Remove `_get_db()` method and `aiosqlite` import
    - Remove inline `CREATE TABLE` statements from `initialize()` (make it a no-op or remove it)
    - Remove `close()` no-op method
    - _Requirements: 6.2, 6.3, 6.5_

  - [ ]* 7.2 Write unit tests for refactored WorldDB
    - Verify all CRUD operations work through `DatabaseConnection` with in-memory SQLite
    - _Requirements: 6.2, 9.1, 9.2, 9.3_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Wire into AgentOrchestrator and FastAPI startup
  - [x] 9.1 Update `backend/app/agents/orchestrator.py`
    - Import `DatabaseConnection` and `MigrationRunner`
    - Create a single `DatabaseConnection` instance (reads `DATABASE_URL`)
    - Run startup migration check: auto-apply if `AUTO_MIGRATE=true`, otherwise log warning for pending migrations
    - Pass `DatabaseConnection` to `SiblingDB` and `WorldDB` constructors
    - Remove old `_ensure_db_initialized()` inline table creation logic
    - _Requirements: 8.1, 8.2, 8.3, 5.1, 5.2, 5.3_

  - [ ]* 9.2 Write unit tests for startup migration check
    - Test warning is logged when pending migrations exist
    - Test auto-migration runs when `AUTO_MIGRATE=true`
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 10. Add test fixtures for database isolation
  - [x] 10.1 Create or update `backend/tests/conftest.py` with shared fixtures
    - Add `db` fixture: in-memory `DatabaseConnection` with all migrations applied
    - Add `sibling_db` fixture: `SiblingDB` backed by the in-memory test database
    - Add `world_db` fixture: `WorldDB` backed by the in-memory test database
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ]* 10.2 Write unit test verifying in-memory SQLite URI support
    - Confirm `sqlite:///:memory:` URI works and migrations apply cleanly
    - _Requirements: 9.1_

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (already in the project)
- Checkpoints ensure incremental validation
- `asyncpg` is only needed for PostgreSQL; SQLite-only environments skip it
