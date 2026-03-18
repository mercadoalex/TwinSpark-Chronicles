# Requirements Document

## Introduction

Twin Spark Chronicles currently uses raw SQL with aiosqlite for all persistence (SiblingDB and WorldDB). There are no versioned migrations, no schema tracking, and no abstraction that would allow swapping SQLite for PostgreSQL in production. This feature introduces a proper migration framework, a database abstraction layer, and a clear upgrade path from SQLite (development) to PostgreSQL (production).

## Glossary

- **Migration_Runner**: The component responsible for discovering, ordering, and executing database migration scripts against the target database.
- **Migration_Script**: A versioned, timestamped file containing SQL statements that move the database schema from one version to the next.
- **Schema_Version_Tracker**: The component that records which migrations have been applied and the current schema version.
- **Database_Abstraction_Layer**: The module that provides a uniform async interface for database operations, hiding whether the underlying engine is SQLite or PostgreSQL.
- **SiblingDB**: The existing persistence layer storing personality profiles, relationship models, skill maps, session summaries, and initial profiles.
- **WorldDB**: The existing persistence layer storing world locations, NPCs, and items, sharing the SiblingDB connection.
- **Baseline_Migration**: The initial migration script that captures the current schema (all 9 existing tables) as version 1.

## Requirements

### Requirement 1: Schema Version Tracking

**User Story:** As a developer, I want the database to track which schema version it is on, so that I can determine which migrations still need to run.

#### Acceptance Criteria

1. THE Schema_Version_Tracker SHALL maintain a `schema_migrations` table with columns for version identifier, script name, and applied-at timestamp.
2. WHEN a Migration_Script is executed successfully, THE Schema_Version_Tracker SHALL insert a record with the migration version, script name, and current UTC timestamp.
3. WHEN the application queries the current schema version, THE Schema_Version_Tracker SHALL return the highest applied version identifier.
4. THE Schema_Version_Tracker SHALL use the same database connection as the application data tables.

### Requirement 2: Migration Script Discovery and Ordering

**User Story:** As a developer, I want migration scripts to be automatically discovered and run in order, so that I do not have to manually track which scripts to execute.

#### Acceptance Criteria

1. THE Migration_Runner SHALL discover all Migration_Script files in a designated `migrations/` directory.
2. THE Migration_Runner SHALL order Migration_Script files by their version prefix in ascending order.
3. WHEN the Migration_Runner executes, THE Migration_Runner SHALL skip Migration_Script files whose version is already recorded in the Schema_Version_Tracker.
4. THE Migration_Runner SHALL execute only unapplied Migration_Script files, in version order, within a single transaction per script.
5. IF a Migration_Script fails during execution, THEN THE Migration_Runner SHALL roll back that script's transaction and report the error with the failing script name and error details.

### Requirement 3: Baseline Migration

**User Story:** As a developer, I want the existing schema captured as the first migration, so that new environments start from a known state and existing databases can be marked as already migrated.

#### Acceptance Criteria

1. THE Baseline_Migration SHALL contain CREATE TABLE statements for all 9 existing tables: `personality_profiles`, `relationship_models`, `skill_maps`, `session_summaries`, `initial_profiles`, `world_locations`, `world_location_history`, `world_npcs`, and `world_items`.
2. THE Baseline_Migration SHALL use `CREATE TABLE IF NOT EXISTS` so that running the baseline against an existing database with data does not fail.
3. WHEN the Baseline_Migration is applied to an empty database, THE Migration_Runner SHALL produce a schema identical to the current production schema.

### Requirement 4: Database Abstraction Layer

**User Story:** As a developer, I want a single async interface for database operations, so that I can switch between SQLite and PostgreSQL without changing application code.

#### Acceptance Criteria

1. THE Database_Abstraction_Layer SHALL expose async methods for `execute`, `fetch_one`, `fetch_all`, and `transaction` that accept parameterized SQL.
2. THE Database_Abstraction_Layer SHALL accept a connection URI string to determine the database engine (SQLite or PostgreSQL).
3. WHEN the connection URI starts with `sqlite`, THE Database_Abstraction_Layer SHALL use aiosqlite as the backend driver.
4. WHEN the connection URI starts with `postgresql`, THE Database_Abstraction_Layer SHALL use asyncpg as the backend driver.
5. THE Database_Abstraction_Layer SHALL normalize parameter placeholders so that application code uses a single placeholder style regardless of backend.
6. IF the database connection fails, THEN THE Database_Abstraction_Layer SHALL raise a descriptive error including the connection URI (with credentials masked) and the underlying driver error message.

### Requirement 5: Configuration-Driven Database Selection

**User Story:** As a developer, I want to configure the database backend via environment variables, so that I can use SQLite locally and PostgreSQL in production without code changes.

#### Acceptance Criteria

1. THE Database_Abstraction_Layer SHALL read the database connection URI from the `DATABASE_URL` environment variable.
2. WHEN `DATABASE_URL` is not set, THE Database_Abstraction_Layer SHALL default to `sqlite:///./sibling_data.db`.
3. WHEN `DATABASE_URL` is set to a PostgreSQL URI, THE Database_Abstraction_Layer SHALL connect to the specified PostgreSQL instance.

### Requirement 6: SiblingDB and WorldDB Refactoring

**User Story:** As a developer, I want SiblingDB and WorldDB to use the Database Abstraction Layer, so that both services work transparently with either SQLite or PostgreSQL.

#### Acceptance Criteria

1. THE SiblingDB SHALL use the Database_Abstraction_Layer for all database operations instead of directly using aiosqlite.
2. THE WorldDB SHALL use the Database_Abstraction_Layer for all database operations instead of directly using aiosqlite.
3. WHEN SiblingDB or WorldDB perform an upsert, THE Database_Abstraction_Layer SHALL translate the upsert syntax to the appropriate dialect (SQLite `ON CONFLICT` or PostgreSQL `ON CONFLICT`).
4. THE SiblingDB SHALL remove its `initialize()` method's inline `CREATE TABLE` statements, relying on the Migration_Runner for schema creation.
5. THE WorldDB SHALL remove its `initialize()` method's inline `CREATE TABLE` statements, relying on the Migration_Runner for schema creation.

### Requirement 7: Migration CLI Command

**User Story:** As a developer, I want a CLI command to run migrations, so that I can apply schema changes during deployment or local setup.

#### Acceptance Criteria

1. THE Migration_Runner SHALL be invocable via `python3 -m app.db.migrate` from the backend directory.
2. WHEN invoked with no arguments, THE Migration_Runner SHALL apply all pending migrations and print each applied migration name.
3. WHEN invoked with a `--status` flag, THE Migration_Runner SHALL print the current schema version and list of applied migrations.
4. WHEN invoked with a `--dry-run` flag, THE Migration_Runner SHALL print the list of pending migrations without executing them.
5. IF no pending migrations exist, THEN THE Migration_Runner SHALL print a message indicating the database is up to date.

### Requirement 8: Startup Migration Check

**User Story:** As a developer, I want the application to verify the database schema is current on startup, so that I am alerted to unapplied migrations before serving requests.

#### Acceptance Criteria

1. WHEN the FastAPI application starts, THE Migration_Runner SHALL check for unapplied migrations.
2. IF unapplied migrations exist at startup, THEN THE Migration_Runner SHALL log a warning listing the pending migration names.
3. WHERE the `AUTO_MIGRATE` environment variable is set to `true`, THE Migration_Runner SHALL automatically apply pending migrations at startup.

### Requirement 9: Test Isolation

**User Story:** As a developer, I want tests to run against a clean in-memory database with migrations applied, so that tests are fast and isolated.

#### Acceptance Criteria

1. WHEN running tests, THE Database_Abstraction_Layer SHALL support in-memory SQLite databases via the URI `sqlite:///:memory:`.
2. THE test fixtures SHALL apply all migrations to the in-memory database before each test that requires database access.
3. THE test fixtures SHALL provide a pre-configured Database_Abstraction_Layer instance to SiblingDB and WorldDB.
