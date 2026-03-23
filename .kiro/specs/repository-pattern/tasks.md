# Tasks: Repository Pattern

## Task 1: Create BaseRepository ABC
- [x] 1.1 Create `backend/app/db/base_repository.py` with `BaseRepository` abstract class defining `find_by_id`, `find_all`, `save`, `delete` abstract methods and `__init__(self, db: DatabaseConnection)` constructor [requirement 1.1, 1.2, 1.3]
- [x] 1.2 Write unit tests in `backend/tests/test_base_repository.py` verifying that `BaseRepository` cannot be instantiated directly and that a concrete subclass missing methods raises `TypeError` [requirement 1.3]
- [ ] *1.3 Write property-based test (Hypothesis, max_examples=20) verifying that any subclass implementing all four methods can be instantiated with a mock `DatabaseConnection` [requirement 1.3]

## Task 2: Create PhotoRepository
- [x] 2.1 Create `backend/app/db/photo_repository.py` with `PhotoRepository(BaseRepository)` implementing all photo, face_portrait, character_mapping, and style_transferred_portrait SQL methods extracted from `PhotoService` [requirement 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7]
- [x] 2.2 Write unit tests in `backend/tests/test_photo_repository.py` verifying each method delegates correct SQL and params to `DatabaseConnection` [requirement 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7]
- [ ] *2.3 Write property-based test (Hypothesis, max_examples=20) verifying round-trip: `save(photo)` then `find_by_id(photo_id)` returns equivalent data using an in-memory SQLite database [requirement 2.1, 2.3]

## Task 3: Create VoiceRecordingRepository
- [x] 3.1 Create `backend/app/db/voice_recording_repository.py` with `VoiceRecordingRepository(BaseRepository)` implementing all voice_recordings and voice_recording_events SQL methods extracted from `VoiceRecordingService` [requirement 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7]
- [x] 3.2 Write unit tests in `backend/tests/test_voice_recording_repository.py` verifying each method delegates correct SQL and params [requirement 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7]
- [ ] *3.3 Write property-based test (Hypothesis, max_examples=20) verifying filter consistency: `find_all(message_type=t)` results all have `message_type == t` [requirement 3.2]

## Task 4: Create WorldRepository
- [x] 4.1 Create `backend/app/db/world_repository.py` with `WorldRepository(BaseRepository)` implementing all location, NPC, and item SQL methods extracted from `WorldDB` [requirement 4.1, 4.2, 4.3, 4.4]
- [x] 4.2 Write unit tests in `backend/tests/test_world_repository.py` verifying each method delegates correct SQL and params [requirement 4.1, 4.2, 4.3, 4.4]
- [ ] *4.3 Write property-based test (Hypothesis, max_examples=20) verifying round-trip for locations: `save_location` then `find_all` includes the saved location [requirement 4.1]

## Task 5: Create SessionRepository
- [x] 5.1 Create `backend/app/db/session_repository.py` with `SessionRepository(BaseRepository)` implementing all session_snapshots SQL methods extracted from `SessionService` [requirement 5.1, 5.2, 5.3, 5.4]
- [x] 5.2 Write unit tests in `backend/tests/test_session_repository.py` verifying each method delegates correct SQL and params [requirement 5.1, 5.2, 5.3, 5.4]
- [ ] *5.3 Write property-based test (Hypothesis, max_examples=20) verifying delete idempotency: `delete_by_pair_id` then `delete_by_pair_id` returns `False` [requirement 5.3]

## Task 6: Refactor PhotoService to use PhotoRepository
- [x] 6.1 Update `PhotoService.__init__` to accept `PhotoRepository` parameter and replace all direct `self._db.fetch_all/fetch_one/execute` calls with `PhotoRepository` method calls [requirement 6.1, 6.5]
- [x] 6.2 Update `_get_photo_service()` factory in `main.py` to create `PhotoRepository` and pass it to `PhotoService` [requirement 7.1]
- [x] 6.3 Update existing `PhotoService` tests to pass `PhotoRepository` (or adapt fixtures) and verify all pass [requirement 8.1]

## Task 7: Refactor VoiceRecordingService to use VoiceRecordingRepository
- [x] 7.1 Update `VoiceRecordingService.__init__` to accept `VoiceRecordingRepository` parameter and replace all direct SQL calls with repository method calls [requirement 6.2, 6.5]
- [x] 7.2 Update `_get_voice_recording_service()` factory in `main.py` to create `VoiceRecordingRepository` and pass it to `VoiceRecordingService` [requirement 7.1]
- [x] 7.3 Update existing `VoiceRecordingService` tests to pass `VoiceRecordingRepository` (or adapt fixtures) and verify all pass [requirement 8.1]

## Task 8: Refactor WorldDB to use WorldRepository
- [x] 8.1 Update `WorldDB.__init__` to accept `WorldRepository` parameter and delegate all SQL methods to it [requirement 6.3, 6.5]
- [x] 8.2 Update WorldDB instantiation in `main.py` to create `WorldRepository` and pass it to `WorldDB` [requirement 7.1]
- [x] 8.3 Update existing `WorldDB` tests to pass `WorldRepository` (or adapt fixtures) and verify all pass [requirement 8.1]

## Task 9: Refactor SessionService to use SessionRepository
- [x] 9.1 Update `SessionService.__init__` to accept `SessionRepository` parameter and replace all direct SQL calls with repository method calls [requirement 6.4, 6.5]
- [x] 9.2 Update SessionService instantiation in `main.py` to create `SessionRepository` and pass it to `SessionService` [requirement 7.1]
- [x] 9.3 Update existing `SessionService` tests to pass `SessionRepository` (or adapt fixtures) and verify all pass [requirement 8.1]

## Task 10: Final Validation
- [x] 10.1 Run full test suite (`python3 -m pytest tests/ -x -q --tb=short`) and verify all 610+ tests pass [requirement 8.1]
- [x] 10.2 Verify SiblingDB source file is unchanged [requirement 6.6]
- [x] 10.3 Verify no new external dependencies were added [requirement 8.2]
