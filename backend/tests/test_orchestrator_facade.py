"""Facade delegation tests for the decomposed AgentOrchestrator.

Verifies that property accessors on the facade resolve to the correct
coordinator attributes, ensuring backward compatibility.
"""

from unittest.mock import MagicMock
from app.agents.orchestrator import AgentOrchestrator


class TestPropertyAccessors:
    """Property accessors delegate to the correct coordinator."""

    def setup_method(self):
        self.orch = AgentOrchestrator()

    def test_session_time_enforcer_getter(self):
        enforcer = MagicMock()
        self.orch.session.session_time_enforcer = enforcer
        assert self.orch.session_time_enforcer is enforcer

    def test_session_time_enforcer_setter(self):
        enforcer = MagicMock()
        self.orch.session_time_enforcer = enforcer
        assert self.orch.session.session_time_enforcer is enforcer

    def test_ws_manager_getter(self):
        ws = MagicMock()
        self.orch.session.ws_manager = ws
        assert self.orch.ws_manager is ws

    def test_ws_manager_setter(self):
        ws = MagicMock()
        self.orch.ws_manager = ws
        assert self.orch.session.ws_manager is ws

    def test_session_tasks_getter(self):
        assert self.orch._session_tasks is self.orch.session._session_tasks

    def test_world_db_getter(self):
        assert self.orch._world_db is self.orch.world.world_db

    def test_world_db_setter(self):
        new_db = MagicMock()
        self.orch._world_db = new_db
        assert self.orch.world._world_db is new_db

    def test_content_filter_getter(self):
        assert self.orch.content_filter is self.orch.story.content_filter

    def test_content_filter_setter(self):
        new_cf = MagicMock()
        self.orch.content_filter = new_cf
        assert self.orch.story.content_filter is new_cf

    def test_playback_integrator_getter(self):
        assert self.orch._playback_integrator is self.orch.story.playback_integrator

    def test_playback_integrator_setter(self):
        pi = MagicMock()
        self.orch._playback_integrator = pi
        assert self.orch.story.playback_integrator is pi

    def test_storyteller_getter(self):
        assert self.orch.storyteller is self.orch.story.storyteller

    def test_storyteller_setter(self):
        new_st = MagicMock()
        self.orch.storyteller = new_st
        assert self.orch.story.storyteller is new_st

    def test_visual_getter(self):
        assert self.orch.visual is self.orch.media.visual

    def test_visual_setter(self):
        new_vis = MagicMock()
        self.orch.visual = new_vis
        assert self.orch.media.visual is new_vis

    def test_voice_getter(self):
        assert self.orch.voice is self.orch.story.voice

    def test_voice_setter(self):
        new_voice = MagicMock()
        self.orch.voice = new_voice
        assert self.orch.story.voice is new_voice

    def test_memory_getter(self):
        assert self.orch.memory is self.orch.story.memory

    def test_memory_setter(self):
        new_mem = MagicMock()
        self.orch.memory = new_mem
        assert self.orch.story.memory is new_mem

    def test_world_state_cache_getter(self):
        assert self.orch._world_state_cache is self.orch.world._world_state_cache

    def test_world_state_cache_setter(self):
        self.orch._world_state_cache = {"pair1": {}}
        assert self.orch.world._world_state_cache == {"pair1": {}}

    def test_world_extractor_getter(self):
        assert self.orch._world_extractor is self.orch.world._world_extractor

    def test_world_extractor_setter(self):
        new_ext = MagicMock()
        self.orch._world_extractor = new_ext
        assert self.orch.world._world_extractor is new_ext


class TestCoordinatorInitialization:
    """Coordinators are properly initialized in __init__."""

    def test_has_session_coordinator(self):
        orch = AgentOrchestrator()
        from app.agents.coordinators import SessionCoordinator
        assert isinstance(orch.session, SessionCoordinator)

    def test_has_story_coordinator(self):
        orch = AgentOrchestrator()
        from app.agents.coordinators import StoryCoordinator
        assert isinstance(orch.story, StoryCoordinator)

    def test_has_world_coordinator(self):
        orch = AgentOrchestrator()
        from app.agents.coordinators import WorldCoordinator
        assert isinstance(orch.world, WorldCoordinator)

    def test_has_media_coordinator(self):
        orch = AgentOrchestrator()
        from app.agents.coordinators import MediaCoordinator
        assert isinstance(orch.media, MediaCoordinator)

    def test_singleton_preserved(self):
        from app.agents.orchestrator import orchestrator
        assert isinstance(orchestrator, AgentOrchestrator)
