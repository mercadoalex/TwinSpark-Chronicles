# Design Document: Database Migration

## Overview

This design introduces a lightweight migration framework and database abstraction layer for Twin Spark Chronicles. The system currently uses raw `aiosqlite` calls in `SiblingDB` and `WorldDB` with inline `CREATE TABLE IF NOT EXISTS` statements — no versioning, no migration history, no path to PostgreSQL.

The design adds four new modules under `backend/app/db/`:

1. **`backend/app/db/connection.py`** — `DatabaseConnection` class: async abstraction over aiosqlite / asyncpg, selected by connection URI.
2. **`backend/app/db/migration_runner.py`** — `MigrationRunner` class: discovers, orders, and applies versioned SQL scripts; tracks applied versions in a `schema_migrations` table.
3. **`backend/app/db/migrations/`** — directory of numbered `.sql` files, starting with `001_baseline.sql`.
4. **`backend/app/db/__main__.py`** — CLI entry point (`python3 -m app.db.migrate`).

`SiblingDB` and `WorldDB` are refactored to accept a `DatabaseConnection` instead of managing their own `aiosqlite.Connection`. Their `initialize()` methods become no-ops (schema is owned by migrations). The `AgentOrchestrator` creates a single `DatabaseConnection`, runs the startup migration check, and passes it to both DB services.

### Key Design Decisions

- **No ORM.** The codebase uses raw SQL throughout and the team is comfortable with it. Adding SQLAlchemy or similar would be a large scope change. The abstraction layer only normalizes connection management and parameter placeholders.
- **SQL-file migrations, not Python.** Keeps migrations declarative and reviewable. Each file is a single transaction.
- **Placeholder normalization.** Application code uses `?` (SQLite style). The abstraction layer rewrites to `$1, $2, ...` when the backend is PostgreSQL. This minimizes changes to existing SQL strings in SiblingDB/WorldDB.
- **asyncpg is optional.** It's only imported when a `postgresql://` URI is provided. SQLite-only environments (dev, test) don't need it installed.

## Architecture

```mermaid
graph TD
    subgraph "Application Layer"
        ORC[AgentOrchestrator]
        SDB[SiblingDB]
        WDB[WorldDB]
    end

    subgraph "backend/app/db/"
        DC[DatabaseConnection]
        MR[MigrationRunner]
        CLI[__main__.py CLI]
        MIG[migrations/*.sql]
    end

    subgraph "Drivers"
        SQLITE[aiosqlite]
        PG[asyncpg]
    end

    ORC -->|creates| DC
    ORC -->|passes| SDB
    ORC -->|passes| WDB
    SDB -->|uses| DC
    WDB -->|uses| DC
    MR -->|uses| DC
    MR -->|reads| MIG
    CLI -->|invokes| MR
    DC -->|sqlite URI| SQLITE
    DC -->|postgresql URI| PG
```

### Startup Sequence

```mermaid
sequenceDiagram
    participant App as FastAPI Startup
    participant ORC as Orchestrator
    participant DC as DatabaseConnection
    participant MR as MigrationRunner

    App->>ORC: __init__()
    ORC->>DC: DatabaseConnection(DATABASE_URL)
    ORC->>DC: connect()
    ORC->>MR: MigrationRunner(DC, migrations_dir)
    ORC->>MR: check_pending()
    alt AUTO_MIGRATE=true
        MR->>DC: apply pending migrations
    else
        MR-->>ORC: log warning with pending list
    end
    ORC->>SDB: SiblingDB(DC)
    ORC->>WDB: WorldDB(DC)
```

## Components and Interfaces

### DatabaseConnection (`backend/app/db/connection.py`)

```python
class DatabaseConnection:
    """Async database abstraction over aiosqlite and asyncpg."""

    def __init__(self, uri: str | None = None) -> None:
        """Parse URI to determine backend. Defaults to DATABASE_URL env var,
        then falls back to 'sqlite:///./sibling_data.db'."""

    async def connect(self) -> None:
        """Open the underlying driver connection."""

    async def close(self) -> None:
        """Close the underlying driver connection."""

    async def execute(self, sql: str, params: tuple = ()) -> None:
        """Execute a write statement (INSERT, UPDATE, DELETE, DDL)."""

    async def fetch_one(self, sql: str, params: tuple = ()) -> dict | None:
        """Execute a query and return the first row as a dict, or None."""

    async def fetch_all(self, sql: str, params: tuple = ()) -> list[dict]:
        """Execute a query and return all rows as list of dicts."""

    async def transaction(self) -> AsyncContextManager:
        """Context manager that wraps statements in BEGIN/COMMIT,
        rolling back on exception."""

    @property
    def backend(self) -> str:
        """Returns 'sqlite' or 'postgresql'."""
```

Placeholder normalization: internally rewrites `?` → `$N` for asyncpg. Application code always uses `?`.

Connection error handling: on failure, raises `DatabaseConnectionError` with the URI (credentials masked via regex replacing password portion) and the underlying driver exception message.

### MigrationRunner (`backend/app/db/migration_runner.py`)

```python
class MigrationRunner:
    """Discovers and applies versioned SQL migration scripts."""

    def __init__(self, db: DatabaseConnection, migrations_dir: str = None) -> None:
        """migrations_dir defaults to backend/app/db/migrations/."""

    async def ensure_migration_table(self) -> None:
        """Create schema_migrations table if it doesn't exist."""

    async def get_applied_versions(self) -> list[str]:
        """Return list of applied version identifiers, ordered ascending."""

    async def get_pending_migrations(self) -> list[tuple[str, str]]:
        """Return list of (version, filename) tuples for unapplied scripts."""

    async def apply_all(self, dry_run: bool = False) -> list[str]:
        """Apply all pending migrations in order. Returns list of applied script names.
        If dry_run=True, returns pending list without executing."""

    async def current_version(self) -> str | None:
        """Return the highest applied version, or None if no migrations applied."""
```

Migration file naming convention: `NNN_description.sql` where `NNN` is a zero-padded integer (e.g., `001_baseline.sql`, `002_add_indexes.sql`). The version prefix is extracted by splitting on `_` and taking the first segment.

Each migration script is executed within a single transaction. On failure, the transaction is rolled back and a `MigrationError` is raised with the script name and error details.

### CLI Entry Point (`backend/app/db/__main__.py`)

Invoked as `python3 -m app.db.migrate` from the `backend/` directory.

| Flag | Behavior |
|------|----------|
| *(none)* | Apply all pending migrations, print each applied name |
| `--status` | Print current version and list of applied migrations |
| `--dry-run` | Print pending migrations without executing |

### Migration Scripts (`backend/app/db/migrations/`)

#### `001_baseline.sql`

Contains `CREATE TABLE IF NOT EXISTS` for all 9 existing tables:
- `personality_profiles`
- `relationship_models`
- `skill_maps`
- `session_summaries`
- `initial_profiles`
- `world_locations`
- `world_location_history`
- `world_npcs`
- `world_items`

Uses `IF NOT EXISTS` so it's safe to run against databases that already have data (existing deployments get marked as migrated without data loss).

### Refactored SiblingDB and WorldDB

Both classes change their constructor signature:

```python
# Before
class SiblingDB:
    def __init__(self, db_path: str = "./sibling_data.db") -> None:

# After
class SiblingDB:
    def __init__(self, db: DatabaseConnection) -> None:
```

```python
# Before
class WorldDB:
    def __init__(self, sibling_db) -> None:

# After
class WorldDB:
    def __init__(self, db: DatabaseConnection) -> None:
```

- All `await db.execute(sql, params)` calls route through `DatabaseConnection` methods.
- `initialize()` becomes a no-op (or is removed). Schema creation is the migration runner's job.
- `_get_db()` is removed. The `DatabaseConnection` instance is used directly.
- `aiosqlite.Row` usage is replaced by `DatabaseConnection.fetch_all()` which returns `list[dict]`.

### Refactored AgentOrchestrator

```python
# In __init__ or an async init method:
from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner

db = DatabaseConnection()  # reads DATABASE_URL
await db.connect()

runner = MigrationRunner(db)
if os.getenv("AUTO_MIGRATE", "").lower() == "true":
    await runner.apply_all()
else:
    pending = await runner.get_pending_migrations()
    if pending:
        logger.warning("Unapplied migrations: %s", [name for _, name in pending])

self._sibling_db = SiblingDB(db)
self._world_db = WorldDB(db)
```

## Data Models

### schema_migrations Table

| Column | Type | Constraints |
|--------|------|-------------|
| version | TEXT | PRIMARY KEY |
| script_name | TEXT | NOT NULL |
| applied_at | TEXT | NOT NULL (ISO 8601 UTC) |

### Existing Tables (unchanged)

The 9 existing tables remain structurally identical. The baseline migration captures them as-is:

**SiblingDB tables:**
- `personality_profiles` (child_id PK, profile_json, created_at, updated_at)
- `relationship_models` (sibling_pair_id PK, model_json, created_at, updated_at)
- `skill_maps` (sibling_pair_id PK, skill_map_json, evaluated_at)
- `session_summaries` (session_id PK, sibling_pair_id, score, summary, suggestion, created_at)
- `initial_profiles` (child_id PK, profile_json, created_at)

**WorldDB tables:**
- `world_locations` (id PK, sibling_pair_id, name, description, state, discovered_at, updated_at; UNIQUE(sibling_pair_id, name))
- `world_location_history` (id PK, location_id FK, previous_state, previous_description, changed_at)
- `world_npcs` (id PK, sibling_pair_id, name, description, relationship_level, met_at, updated_at; UNIQUE(sibling_pair_id, name))
- `world_items` (id PK, sibling_pair_id, name, description, collected_at, session_id; UNIQUE(sibling_pair_id, name))

### Parameter Placeholder Mapping

| Application SQL | SQLite driver | PostgreSQL driver |
|----------------|---------------|-------------------|
| `?` | `?` (native) | `$1`, `$2`, ... (rewritten) |

The `DatabaseConnection` performs a left-to-right replacement of `?` with positional `$N` placeholders when `backend == 'postgresql'`. This is a simple regex/counter approach — no SQL parsing needed since the codebase doesn't use `?` in string literals.


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Migration discovery returns all files in version order

*For any* set of `.sql` files placed in the migrations directory with valid version prefixes (e.g., `001_`, `002_`), the `MigrationRunner.get_pending_migrations()` method should return all of them, sorted in ascending order by version prefix.

**Validates: Requirements 2.1, 2.2**

### Property 2: Only unapplied migrations execute, in order, and are recorded

*For any* set of migration scripts where a subset has already been applied, `apply_all()` should execute only the unapplied scripts in ascending version order, and after execution each newly applied script should have a corresponding record in `schema_migrations` with its version, script name, and a valid UTC timestamp.

**Validates: Requirements 1.2, 2.3, 2.4**

### Property 3: Current version is the highest applied version

*For any* non-empty set of applied migration version identifiers in the `schema_migrations` table, `current_version()` should return the lexicographically highest version string.

**Validates: Requirements 1.3**

### Property 4: Failed migration rolls back without leaving a record

*For any* migration script containing invalid SQL, when the `MigrationRunner` attempts to apply it, the transaction should be rolled back, the `schema_migrations` table should not contain a record for that version, and a `MigrationError` should be raised containing the script name.

**Validates: Requirements 2.5**

### Property 5: Baseline migration is idempotent with existing data

*For any* database that already contains the 9 application tables with data rows, applying the baseline migration (`001_baseline.sql`) should succeed without error and all pre-existing data should remain intact and unchanged.

**Validates: Requirements 3.2**

### Property 6: URI prefix determines backend

*For any* connection URI string, if the URI starts with `sqlite` the `DatabaseConnection.backend` property should return `'sqlite'`, and if the URI starts with `postgresql` it should return `'postgresql'`.

**Validates: Requirements 4.2, 4.3, 4.4**

### Property 7: Placeholder normalization round-trip

*For any* SQL string containing N `?` placeholders (where `?` does not appear inside single-quoted string literals), the PostgreSQL normalization should produce a string with exactly N positional placeholders `$1` through `$N`, in left-to-right order, and no remaining `?` characters.

**Validates: Requirements 4.5**

### Property 8: Credential masking in error messages

*For any* PostgreSQL connection URI containing a password component (e.g., `postgresql://user:secret@host/db`), when a `DatabaseConnectionError` is raised, the error message should contain the URI with the password portion replaced by `***` and should never contain the original password string.

**Validates: Requirements 4.6**

### Property 9: Dry-run does not modify the database

*For any* set of pending migrations, calling `apply_all(dry_run=True)` should return the list of pending migration names but the `schema_migrations` table should remain unchanged (same row count and same content as before the call).

**Validates: Requirements 7.4**

## Error Handling

| Scenario | Behavior |
|----------|----------|
| **Invalid DATABASE_URL** | `DatabaseConnection.__init__` raises `ValueError` with a message describing the expected URI format. |
| **Connection failure** | `DatabaseConnection.connect()` raises `DatabaseConnectionError` with masked URI and driver error message. |
| **Migration script SQL error** | `MigrationRunner` rolls back the script's transaction, raises `MigrationError(script_name, original_error)`. Subsequent migrations are not attempted. |
| **Missing migrations directory** | `MigrationRunner.__init__` raises `FileNotFoundError` with the expected path. |
| **Duplicate version prefix** | `MigrationRunner.get_pending_migrations()` raises `MigrationError` indicating the conflicting filenames. |
| **asyncpg not installed** | When a `postgresql://` URI is provided but `asyncpg` is not installed, `DatabaseConnection.connect()` raises `ImportError` with a message suggesting `pip install asyncpg`. |

Custom exception classes:

```python
class DatabaseConnectionError(Exception):
    """Raised when the database connection cannot be established."""

class MigrationError(Exception):
    """Raised when a migration script fails to apply."""
```

## Testing Strategy

### Dual Testing Approach

Both unit tests and property-based tests are used. Unit tests cover specific examples, edge cases, and integration points. Property-based tests verify universal properties across generated inputs.

### Property-Based Testing

- **Library:** [Hypothesis](https://hypothesis.readthedocs.io/) (already installed in the project — see `backend/.hypothesis/` directory and `conftest.py` strategies)
- **Minimum iterations:** 100 per property test
- **Tag format:** `# Feature: database-migration, Property N: <property text>`

Each correctness property above maps to a single Hypothesis test:

| Property | Test Focus | Key Generators |
|----------|-----------|----------------|
| P1: Discovery & ordering | Generate random sets of `NNN_name.sql` filenames in a temp dir | `st.lists(st.integers(1, 999))` for version numbers |
| P2: Only unapplied execute | Generate total migration set + applied subset, verify only complement runs | `st.lists()` + `st.sampled_from()` for subset selection |
| P3: Current version = max | Insert random version strings into schema_migrations, verify max | `st.lists(st.text(alphabet="0123456789", min_size=3, max_size=3))` |
| P4: Failed migration rollback | Generate invalid SQL strings, verify no record + exception | `st.text()` for bad SQL |
| P5: Baseline idempotence | Pre-populate tables with random rows, run baseline, verify data intact | Existing `st_personality_profile`, `st_relationship_model` strategies |
| P6: URI → backend | Generate random URIs with sqlite/postgresql prefixes | `st.sampled_from(["sqlite", "postgresql"])` + `st.text()` for path |
| P7: Placeholder normalization | Generate SQL strings with random numbers of `?` placeholders | `st.integers(1, 20)` for placeholder count, `st.text()` for SQL fragments |
| P8: Credential masking | Generate URIs with random passwords | `st.text(min_size=1)` for password component |
| P9: Dry-run no side effects | Generate pending migration sets, run dry-run, verify no DB changes | Reuse P2 generators |

### Unit Tests

Unit tests focus on:
- **Specific examples:** Baseline migration creates all 9 tables on empty DB (Req 3.1, 3.3)
- **Configuration:** `DATABASE_URL` env var is read correctly, default fallback works (Req 5.1, 5.2)
- **CLI behavior:** `--status` and `--dry-run` flags produce expected output (Req 7.2, 7.3)
- **Startup check:** FastAPI startup logs warning for pending migrations, auto-migrates when `AUTO_MIGRATE=true` (Req 8.1, 8.2, 8.3)
- **In-memory support:** `sqlite:///:memory:` URI works for test isolation (Req 9.1)
- **Edge cases:** No pending migrations prints "up to date" message (Req 7.5), empty migrations directory

### Test Fixtures

A shared `conftest.py` fixture provides:

```python
@pytest.fixture
async def db():
    """In-memory DatabaseConnection with all migrations applied."""
    conn = DatabaseConnection("sqlite:///:memory:")
    await conn.connect()
    runner = MigrationRunner(conn)
    await runner.apply_all()
    yield conn
    await conn.close()

@pytest.fixture
async def sibling_db(db):
    """SiblingDB backed by the in-memory test database."""
    return SiblingDB(db)

@pytest.fixture
async def world_db(db):
    """WorldDB backed by the in-memory test database."""
    return WorldDB(db)
```
