# Requirements: Repository Pattern

## Requirement 1: Base Repository Abstract Class

### Acceptance Criteria

1.1 Given the repository layer, when a new `BaseRepository` ABC is defined in `backend/app/db/base_repository.py`, then it must declare abstract methods `find_by_id`, `find_all`, `save`, and `delete`.

1.2 Given `BaseRepository`, when instantiated with a `DatabaseConnection`, then it stores the connection as `self._db` for use by subclasses.

1.3 Given any concrete repository class, when it extends `BaseRepository`, then it must implement all four abstract methods or raise `TypeError` on instantiation.

## Requirement 2: PhotoRepository

### Acceptance Criteria

2.1 Given `PhotoRepository(db)`, when `find_by_id(photo_id)` is called, then it returns the photo row as a dict or `None` — identical to the current `SELECT * FROM photos WHERE photo_id = ?` behavior.

2.2 Given `PhotoRepository(db)`, when `find_all(sibling_pair_id=pair_id)` is called, then it returns all photo rows for that pair ordered by `uploaded_at ASC` — identical to current `PhotoService.get_photos` query.

2.3 Given `PhotoRepository(db)`, when `save(photo_dict)` is called with a valid photo dict, then it inserts a row into the `photos` table with all provided fields.

2.4 Given `PhotoRepository(db)`, when `delete(photo_id)` is called, then it deletes the photo row and returns `True`, or returns `False` if no row existed.

2.5 Given `PhotoRepository(db)`, when face portrait methods are called (`find_faces_by_photo`, `save_face`, `delete_faces_by_photo`, `update_face_label`), then they produce identical results to the current inline SQL in `PhotoService`.

2.6 Given `PhotoRepository(db)`, when character mapping methods are called (`find_mappings`, `save_mapping`, `delete_mapping`, `nullify_face_in_mappings`), then they produce identical results to the current inline SQL in `PhotoService`.

2.7 Given `PhotoRepository(db)`, when `get_storage_stats(sibling_pair_id)` is called, then it returns `{photo_count, face_count, total_size_bytes}` — identical to current `PhotoService.get_storage_stats` queries.

## Requirement 3: VoiceRecordingRepository

### Acceptance Criteria

3.1 Given `VoiceRecordingRepository(db)`, when `find_by_id(recording_id)` is called, then it returns the recording row as a dict or `None`.

3.2 Given `VoiceRecordingRepository(db)`, when `find_all(sibling_pair_id, message_type, recorder_name)` is called with optional filters, then it dynamically builds the WHERE clause and returns rows ordered by `recorder_name ASC, created_at ASC`.

3.3 Given `VoiceRecordingRepository(db)`, when `save(recording_dict)` is called, then it inserts a row into `voice_recordings` with all provided fields.

3.4 Given `VoiceRecordingRepository(db)`, when `delete(recording_id)` is called, then it deletes the row and returns `True`, or `False` if not found.

3.5 Given `VoiceRecordingRepository(db)`, when `count_by_pair(sibling_pair_id)` is called, then it returns the exact count of recordings for that pair.

3.6 Given `VoiceRecordingRepository(db)`, when `save_event(event_dict)` is called, then it inserts a row into `voice_recording_events`.

3.7 Given `VoiceRecordingRepository(db)`, when `get_voice_commands(sibling_pair_id)` is called, then it returns voice command rows identical to the current `VoiceRecordingService.get_voice_commands` query.

## Requirement 4: WorldRepository

### Acceptance Criteria

4.1 Given `WorldRepository(db)`, when location methods are called (`save_location`, `load_locations`, `update_location_state`), then they produce identical results to current `WorldDB` methods.

4.2 Given `WorldRepository(db)`, when NPC methods are called (`save_npc`, `load_npcs`, `update_npc_relationship`), then they produce identical results to current `WorldDB` methods.

4.3 Given `WorldRepository(db)`, when item methods are called (`save_item`, `load_items`), then they produce identical results to current `WorldDB` methods.

4.4 Given `WorldRepository(db)`, when `load_world_state(sibling_pair_id)` is called, then it returns `{locations, npcs, items}` — identical to current `WorldDB.load_world_state`.

4.5 Given `WorldDB` after refactoring, when any of its public methods are called, then it delegates to `WorldRepository` and returns the same result as before.

## Requirement 5: SessionRepository

### Acceptance Criteria

5.1 Given `SessionRepository(db)`, when `find_by_pair_id(sibling_pair_id)` is called, then it returns the snapshot row as a dict or `None`.

5.2 Given `SessionRepository(db)`, when `save(snapshot_dict)` is called, then it upserts into `session_snapshots` using `ON CONFLICT(sibling_pair_id)`.

5.3 Given `SessionRepository(db)`, when `delete_by_pair_id(sibling_pair_id)` is called, then it deletes the row and returns `True`, or `False` if not found.

5.4 Given `SessionRepository(db)`, when `delete_stale(threshold_iso)` is called, then it deletes all snapshots with `updated_at < threshold` and returns the count.

## Requirement 6: Service Refactoring

### Acceptance Criteria

6.1 Given `PhotoService` after refactoring, when constructed, then it accepts a `PhotoRepository` (instead of or in addition to `DatabaseConnection`) and delegates all SQL operations to it.

6.2 Given `VoiceRecordingService` after refactoring, when constructed, then it accepts a `VoiceRecordingRepository` and delegates all SQL operations to it.

6.3 Given `WorldDB` after refactoring, when constructed, then it accepts a `WorldRepository` and delegates all SQL operations to it.

6.4 Given `SessionService` after refactoring, when constructed, then it accepts a `SessionRepository` and delegates all SQL operations to it.

6.5 Given any refactored service, when its methods are called, then the service contains zero raw SQL strings — all SQL lives in the repository.

6.6 Given `SiblingDB`, then it is NOT modified — it remains as-is since it's already a well-structured data access layer.

## Requirement 7: Dependency Injection & Wiring

### Acceptance Criteria

7.1 Given `main.py` factory functions (e.g., `_get_photo_service`), when they create service instances, then they first create the appropriate repository with `DatabaseConnection` and pass it to the service constructor.

7.2 Given any repository, when instantiated, then it receives `DatabaseConnection` as a constructor parameter — it never creates its own connection.

## Requirement 8: Backward Compatibility

### Acceptance Criteria

8.1 Given the full test suite (610+ tests), when run after refactoring, then all tests pass with no failures.

8.2 Given the refactoring, then no new external dependencies are introduced (no changes to requirements.txt or new pip installs).

8.3 Given the refactoring, then no database schema changes are made — repositories use existing tables as-is.

8.4 Given the refactoring, then all existing API endpoints return identical responses for identical inputs.

## Correctness Properties

### Property 1: Round-Trip Consistency
For any valid entity dict `e` with a unique ID, `repo.save(e)` followed by `repo.find_by_id(e.id)` returns a dict equivalent to `e`.

### Property 2: Filter Satisfaction
For any `find_all(**filters)` call, every dict in the returned list satisfies all provided filter predicates.

### Property 3: Delete Idempotency
For any entity ID `id`, after `repo.delete(id)` returns `True`, a subsequent `repo.delete(id)` returns `False`.

### Property 4: Behavioral Equivalence
For any service method `m` and input `i`, the output of `m(i)` before refactoring equals the output of `m(i)` after refactoring, given identical database state.

### Property 5: Repository Isolation
No repository module imports `os`, `shutil`, `io`, or any file I/O library. Repositories only call `self._db.fetch_all`, `self._db.fetch_one`, `self._db.execute`, and `self._db.transaction`.
